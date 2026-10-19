"""Low-latency video preview with lossless ADB capture for saved evidence."""
import base64
import copy
import io
import secrets
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone

from PIL import Image

import capture
from imaging import read_image
from scrcpy_stream import ScrcpyVideoStream


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class PreviewStore:
    def __init__(self, ttl=90, max_sessions=4, max_frames=180,
                 stream_factory=ScrcpyVideoStream):
        self.ttl, self.max_sessions, self.max_frames = ttl, max_sessions, max_frames
        self.stream_factory = stream_factory
        self.sessions = OrderedDict()
        self.lock = threading.RLock()

    def _prune(self):
        cutoff = time.monotonic() - self.ttl
        for key, session in list(self.sessions.items()):
            if session['touched'] < cutoff:
                del self.sessions[key]
                if session.get('stream'):
                    session['stream'].stop()

    def _get(self, key):
        self._prune()
        session = self.sessions.get(key)
        if not session:
            raise ValueError('预览已结束或过期，请重新开启实时预览。')
        session['touched'] = time.monotonic()
        return session

    def start(self, serial):
        started = utc_now()
        stream = None
        if self.stream_factory:
            try:
                stream = self.stream_factory(serial).start()
            except (OSError, ValueError):
                stream = None
        try:
            raw, metadata = capture.capture(serial)
        except Exception:
            if stream:
                stream.stop()
            raise
        metadata.update({'metadata_sampled_at': started})
        key = secrets.token_urlsafe(24)
        with self.lock:
            self._prune()
            while len(self.sessions) >= self.max_sessions:
                _, old = self.sessions.popitem(last=False)
                if old.get('stream'):
                    old['stream'].stop()
            self.sessions[key] = {'device': serial, 'metadata': metadata, 'frames': OrderedDict(),
                                  'touched': time.monotonic(), 'inflight': False,
                                  'stream': stream, 'last_sequence': 0}
        return self._remember(key, raw, metadata, started, utc_now(), transport='adb')

    def next_frame(self, key):
        with self.lock:
            session = self._get(key)
            if session['inflight']:
                raise ValueError('上一帧仍在采集中，请稍后重试。')
            session['inflight'] = True
        started = utc_now()
        try:
            stream = session.get('stream')
            if stream:
                try:
                    sequence, image = stream.get(session['last_sequence'])
                    session['last_sequence'] = sequence
                    return self._remember_image(key, image, session['metadata'], started, utc_now(), 'video')
                except ValueError:
                    stream.stop()
                    session['stream'] = None
            raw, foreground = capture.preview_frame(session['device'])
            metadata = {**session['metadata'], 'foreground_package': foreground}
            # With no target package, do not attach the old app's version to a new app.
            if foreground != metadata.get('package'):
                metadata.update({'package': foreground, 'versionName': None, 'versionCode': None})
            return self._remember(key, raw, metadata, started, utc_now(), transport='adb')
        finally:
            with self.lock:
                session['inflight'] = False

    def _remember(self, key, raw, metadata, started, finished, transport):
        return self._remember_image(key, read_image(raw), metadata, started, finished, transport)

    def _remember_image(self, key, image, metadata, started, finished, transport):
        size = list(image.size)
        # Only query power for a near-black frame; normal video has no extra
        # ADB round trip. A dark page on an awake phone is still valid.
        if image.convert('L').getextrema()[1] <= 8:
            with self.lock:
                serial = self._get(key)['device']
            capture.ensure_screen_awake(serial)
        image.thumbnail((1024, 2010), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=90, subsampling=0, optimize=False)
        frame_id = secrets.token_urlsafe(18)
        evidence = {**copy.deepcopy(metadata), 'preview_frame_id': frame_id,
                    'captured_at': started, 'capture_finished_at': finished,
                    'capture_source': 'lossless ADB PNG at screenshot action'}
        with self.lock:
            session = self._get(key)
            session['frames'][frame_id] = (evidence, time.monotonic())
            while len(session['frames']) > self.max_frames:
                session['frames'].popitem(last=False)
        return {'session_id': key, 'frame_id': frame_id, 'captured_at': started,
                'capture_finished_at': finished, 'image_size': size,
                'transport': transport,
                'preview_url': 'data:image/jpeg;base64,' + base64.b64encode(output.getvalue()).decode()}

    def freeze(self, key, frame_id, serial):
        with self.lock:
            session = self._get(key)
            if session['device'] != serial:
                raise ValueError('设备已改变，请重新开启预览后截图。')
            frame = session['frames'].get(frame_id)
            if not frame or time.monotonic() - frame[1] > self.ttl:
                raise ValueError('这帧画面已过期，请重新开启预览后截图。')
            preview_metadata = copy.deepcopy(frame[0])
        raw, metadata = capture.capture(serial)
        metadata.update({name: value for name, value in preview_metadata.items()
                         if name.startswith('preview_') or name in ('capture_source',)})
        metadata['captured_at'] = utc_now()
        metadata['capture_finished_at'] = utc_now()
        return raw, metadata

    def stop(self, key):
        with self.lock:
            session = self.sessions.pop(key, None)
        if session and session.get('stream'):
            session['stream'].stop()
