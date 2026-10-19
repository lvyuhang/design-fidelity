"""Low-latency, read-only Android screen stream backed by scrcpy-server."""
from __future__ import annotations

import hashlib
import os
import secrets
import socket
import subprocess
import threading
import time
from pathlib import Path

import av

import capture


SERVER_VERSION = '4.1'
SERVER_NAME = 'scrcpy-server-v4.1'
SERVER_SHA256 = 'deacb991ed2509715160ffdc7907e47b4160eb30d1566217e9047fd5b8850cae'
REMOTE_SERVER = '/data/local/tmp/scrcpy-server-design-review.jar'


def server_path():
    configured = os.environ.get('REVIEW_SCRCPY_SERVER')
    return Path(configured) if configured else Path(__file__).resolve().parent / '.tools' / SERVER_NAME


class ScrcpyVideoStream:
    """Keep only the newest decoded frame so slow consumers never add latency."""

    def __init__(self, serial, max_size=2010, max_fps=60, bit_rate=20_000_000):
        self.serial = serial
        self.max_size = max_size
        self.max_fps = max_fps
        self.bit_rate = bit_rate
        self.condition = threading.Condition()
        self.latest_frame = None
        self.sequence = 0
        self.error = None
        self.stopped = False
        self.listener = None
        self.socket = None
        self.process = None
        self.thread = None
        self.reverse_name = None

    def start(self):
        path = server_path()
        if not path.is_file():
            raise ValueError('缺少高清视频组件，请重新启动工作台或检查 .tools/scrcpy-server-v4.1。')
        if hashlib.sha256(path.read_bytes()).hexdigest() != SERVER_SHA256:
            raise ValueError('高清视频组件校验失败，请重新下载官方 scrcpy-server v4.1。')
        if not capture.find_adb():
            raise ValueError('未找到 ADB，无法启动高清视频预览。')
        self.thread = threading.Thread(target=self._run, name='android-video-' + self.serial, daemon=True)
        self.thread.start()
        return self

    def _adb(self, *args, timeout=15):
        command = [capture.find_adb(), '-s', self.serial, *args]
        try:
            result = subprocess.run(command, capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError('ADB 视频通道响应超时') from error
        if result.returncode:
            detail = result.stderr.decode('utf-8', 'replace').strip()
            raise RuntimeError(detail[:500] or 'ADB 视频通道启动失败')
        return result.stdout

    def _run(self):
        try:
            self._adb('push', str(server_path()), REMOTE_SERVER, timeout=30)
            scid = secrets.randbelow(0x7fffffff)
            self.reverse_name = 'localabstract:scrcpy_' + format(scid, '08x')
            self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener.bind(('127.0.0.1', 0))
            self.listener.listen(1)
            self.listener.settimeout(8)
            port = self.listener.getsockname()[1]
            self._adb('reverse', self.reverse_name, 'tcp:' + str(port))
            args = [capture.find_adb(), '-s', self.serial, 'shell',
                    'CLASSPATH=' + REMOTE_SERVER, 'app_process', '/',
                    'com.genymobile.scrcpy.Server', SERVER_VERSION,
                    'scid=' + format(scid, '08x'), 'audio=false', 'control=false',
                    'cleanup=false', 'raw_stream=true', 'max_size=' + str(self.max_size),
                    'max_fps=' + str(self.max_fps), 'video_bit_rate=' + str(self.bit_rate)]
            self.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.socket, _ = self.listener.accept()
            self.socket.settimeout(1)
            codec = av.CodecContext.create('h264', 'r')
            while not self.stopped:
                try:
                    data = self.socket.recv(262_144)
                except socket.timeout:
                    continue
                if not data:
                    raise RuntimeError('手机视频流已断开')
                for packet in codec.parse(data):
                    for frame in codec.decode(packet):
                        with self.condition:
                            self.latest_frame = frame
                            self.sequence += 1
                            self.condition.notify_all()
        except Exception as error:
            if not self.stopped:
                with self.condition:
                    self.error = str(error) or type(error).__name__
                    self.condition.notify_all()
        finally:
            self._cleanup()

    def get(self, after=0, timeout=2):
        deadline = time.monotonic() + timeout
        with self.condition:
            while not self.stopped and not self.error and (self.latest_frame is None or self.sequence <= after):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self.condition.wait(remaining)
            if self.error:
                raise ValueError('高清视频预览失败：' + self.error)
            if self.latest_frame is None:
                raise ValueError('等待手机画面超时，请保持屏幕亮起后重试。')
            frame, sequence = self.latest_frame, self.sequence
        return sequence, frame.to_image().convert('RGB')

    def stop(self):
        with self.condition:
            self.stopped = True
            self.condition.notify_all()
        for resource in (self.socket, self.listener):
            if resource:
                try:
                    resource.close()
                except OSError:
                    pass
        if self.process and self.process.poll() is None:
            self.process.terminate()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=2)
        self._remove_reverse()

    def _remove_reverse(self):
        name, self.reverse_name = self.reverse_name, None
        if name and capture.find_adb():
            subprocess.run([capture.find_adb(), '-s', self.serial, 'reverse', '--remove', name],
                           capture_output=True, timeout=5)

    def _cleanup(self):
        for resource in (self.socket, self.listener):
            if resource:
                try:
                    resource.close()
                except OSError:
                    pass
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self._remove_reverse()
