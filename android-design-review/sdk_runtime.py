"""Install a pinned, checksum-verified Android runtime without altering a user's SDK."""
import hashlib
import capture
import json
import os
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

SDK = Path(os.environ.get('REVIEW_ANDROID_SDK', Path.home() / 'Library/Application Support/设计验收/android-sdk'))
IMAGE = 'system-images/android-34/default/arm64-v8a'
# Stable packages from Google's repository2-3.xml and sys-img/android/sys-img2-3.xml.
PACKAGES = [
    ('模拟器', 'emulator-darwin_aarch64-16428233.zip', '3af4fe44ce82b3d88ae5678a53735f27ad729c15', 416112708, 'emulator', 'emulator/emulator'),
    ('Android 14 系统', 'sys-img/android/arm64-v8a-34_r04.zip', 'd9f2011131919abe952814e041f16f317242c3fa', 705115396, IMAGE, IMAGE + '/system.img'),
    ('APK 解析工具', 'build-tools_r35_macosx.zip', '93ab8ce91230e067b5add4bfa79919c52b27f072', 76857898, 'build-tools/35.0.0', 'build-tools/35.0.0/aapt2'),
]


def ready():
    return (SDK/'platform-tools/adb').is_file() and all((SDK / marker).is_file() for *_, marker in PACKAGES)


def install(update, cancelled):
    SDK.mkdir(parents=True, exist_ok=True)
    adb=capture.find_adb()
    if not (SDK/'platform-tools/adb').exists():
        if not adb: raise ValueError('请先安装 Android Platform-Tools。')
        shutil.copytree(Path(adb).parent,SDK/'platform-tools',dirs_exist_ok=True)
    if shutil.disk_usage(SDK).free < 7 * 1024**3:
        raise ValueError('首次安装需要至少 7 GB 可用空间。')
    cache = SDK / 'downloads'
    cache.mkdir(exist_ok=True)
    for name, url, checksum, size, destination, marker in PACKAGES:
        if (SDK / marker).is_file():
            continue
        archive = cache / Path(url).name
        command = ['curl', '--fail', '--location', '--retry', '3', '--connect-timeout', '20',
                   '--speed-time', '60', '--speed-limit', '1024', '--continue-at', '-',
                   '--output', str(archive), 'https://dl.google.com/android/repository/' + url]
        with (cache / 'download.log').open('a') as log:
            if not archive.exists() or archive.stat().st_size != size:
                process = subprocess.Popen(command, stdout=log, stderr=log)
                try:
                    while process.poll() is None:
                        if cancelled():
                            raise ValueError('已取消安装；下次可继续下载。')
                        done = archive.stat().st_size if archive.exists() else 0
                        update(f'下载{name} · {done // 1048576} / {size // 1048576} MB', round(min(99, done / size * 100)))
                        time.sleep(.5)
                    if process.returncode:
                        raise ValueError('下载失败，请检查网络后重试（会继续下载）。')
                finally:
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=10)
        update('校验' + name, 100)
        digest = hashlib.sha1()
        with archive.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024*1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != checksum:
            archive.unlink(missing_ok=True)
            raise ValueError('下载文件校验失败，请重试。')
        if cancelled():
            raise ValueError('已取消安装。')
        update('解压' + name, None)
        with tempfile.TemporaryDirectory(dir=SDK) as temp:
            with zipfile.ZipFile(archive) as z:
                for entry in z.infolist():
                    target = (Path(temp) / entry.filename).resolve()
                    if Path(temp) not in target.parents:
                        raise ValueError('压缩包包含无效路径')
                z.extractall(temp)
                for entry in z.infolist():
                    mode = entry.external_attr >> 16
                    if mode:
                        (Path(temp) / entry.filename).chmod(mode & 0o777)
            roots = list(Path(temp).iterdir())
            root = next(p for p in roots if p.is_dir())
            dest = SDK / destination
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(root), dest)
    (SDK / 'installation.json').write_text(json.dumps({'api_level':34,'abi':'arm64-v8a','source':'https://dl.google.com/android/repository/','installed_at':time.time()}))
    update('Android 环境已就绪', 100)


if __name__ == '__main__':
    # Run only after the user has explicitly accepted the linked SDK terms.
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--accept-sdk-license', action='store_true')
    args = p.parse_args()
    if not args.accept_sdk_license:
        p.error('请先阅读并同意 https://developer.android.com/studio/terms')
    install(lambda phase, progress: print(phase, flush=True), lambda: False)
