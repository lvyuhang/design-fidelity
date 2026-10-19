"""Read-only ADB adapter. No shell interpolation or device settings changes."""
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def find_adb():
    roots = [os.environ.get('ANDROID_HOME'), os.environ.get('ANDROID_SDK_ROOT')]
    candidates = [os.environ.get('REVIEW_ADB'), shutil.which('adb')]
    candidates += [str(Path(r) / 'platform-tools/adb') for r in roots if r]
    candidates += [str(Path.home() / 'Library/Android/sdk/platform-tools/adb'),
                   str(Path(__file__).resolve().parents[1] / '.tools/platform-tools/adb')]
    return next((p for p in candidates if p and Path(p).is_file() and os.access(p, os.X_OK)), None)


def command(args, timeout=15, binary=False):
    adb = find_adb()
    if not adb:
        raise ValueError('未找到 ADB。请安装 Android Platform-Tools，或设置 REVIEW_ADB。')
    try:
        result = subprocess.run([adb] + args, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ValueError('设备响应超时。请检查数据线、设备解锁状态，然后刷新设备。')
    if result.returncode:
        raise ValueError(result.stderr.decode('utf-8', 'replace').strip()[:600] or 'ADB 执行失败')
    return result.stdout if binary else result.stdout.decode('utf-8', 'replace').strip()


def parse_devices(output):
    result = []
    for line in output.splitlines():
        if not line.strip() or line.startswith(('List of devices', '*')):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[:2]
        properties = dict(p.split(':', 1) for p in parts[2:] if ':' in p)
        result.append({'id': serial, 'state': state,
                       'name': properties.get('model', serial).replace('_', ' '),
                       'kind': 'emulator' if serial.startswith('emulator-') else
                               ('usb' if 'usb' in properties else 'device')})
    return result


def devices():
    path = find_adb()
    if not path:
        return {'available': False, 'devices': [], 'message': 'ADB 尚未安装'}
    return {'available': True, 'devices': parse_devices(command(['devices', '-l'])), 'message': ''}


def ensure_screen_awake(serial, power=None):
    if power is None:
        try:
            power = command(['-s', serial, 'shell', 'dumpsys', 'power'], timeout=5)
        except ValueError:
            return  # Some Android variants do not expose power diagnostics.
    if re.search(r'mWakefulness=(?:Asleep|Dozing)\b', power or ''):
        raise ValueError('手机已息屏，请在手机上亮屏并解锁，再点击「重新连接」。')


def preview_frame(serial, package=''):
    """Fast capture for a previously validated preview session."""
    def foreground():
        window = command(['-s', serial, 'shell', 'dumpsys', 'window'])
        found = re.search(r'mCurrentFocus=.*?\s([\w.]+)/[\w.$]+', window)
        return found.group(1) if found else None
    # Device-screen mode deliberately avoids foreground-app queries. This keeps
    # preview flowing across app/home/system UI transitions and lowers latency.
    if not package:
        png = command(['-s', serial, 'exec-out', 'screencap', '-p'], timeout=15, binary=True)
        if not png.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('设备没有返回有效 PNG，请解锁手机并确认当前页面允许系统截图。')
        return png, None
    before = foreground()
    if not before or before != package:
        raise ValueError('请在手机上打开目标应用并解锁屏幕，再重新开启预览。')
    png = command(['-s', serial, 'exec-out', 'screencap', '-p'], timeout=15, binary=True)
    if not png.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('设备没有返回有效 PNG，请检查该页面是否允许系统截图。')
    after = foreground()
    if before != after:
        raise ValueError('前台应用已切换，请停留在目标应用后重新开启预览。')
    return png, before


def capture(serial, package=''):
    device = next((d for d in devices()['devices'] if d['id'] == serial), None)
    if not device or device['state'] != 'device':
        raise ValueError('设备未就绪。请刷新列表，并在手机上允许 USB 调试。')
    if package and not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+', package):
        raise ValueError('应用包名格式不正确，例如 com.example.app。')
    queries = {
        'android_version': ['getprop', 'ro.build.version.release'],
        'api_level': ['getprop', 'ro.build.version.sdk'],
        'display_size': ['wm', 'size'], 'display_density': ['wm', 'density'],
        'font_scale': ['settings', 'get', 'system', 'font_scale'],
        'window': ['dumpsys', 'window'],
        'power': ['dumpsys', 'power'],
    }
    warnings = []
    def read(item):
        key, args = item
        try:
            return key, command(['-s', serial, 'shell'] + args)
        except ValueError as error:
            warnings.append(key + ': ' + str(error))
            return key, None
    with ThreadPoolExecutor(max_workers=4) as pool:
        metadata = dict(pool.map(read, queries.items()))
    ensure_screen_awake(serial, metadata.pop('power') or '')
    window = metadata.pop('window') or ''
    match = re.search(r'mCurrentFocus=.*?\s([\w.]+)/[\w.$]+', window)
    foreground = match.group(1) if match else None
    if package and foreground and foreground != package:
        raise ValueError('当前前台应用是 ' + foreground + '，请先打开 ' + package + ' 再截图。')
    requested_package=package
    metadata.update({'device': device, 'package': requested_package or None, 'warnings': warnings,
                     'method': 'adb exec-out screencap -p', 'foreground_package': foreground})
    if requested_package:
        package_dump = read(('package_info', ['dumpsys', 'package', requested_package]))[1] or ''
        for key in ('versionName', 'versionCode'):
            found = re.search(r'\b' + key + r'=([^\s]+)', package_dump)
            metadata[key] = found.group(1) if found else None
    png = command(['-s', serial, 'exec-out', 'screencap', '-p'], timeout=30, binary=True)
    if not png.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('设备没有返回有效 PNG；请确认该页面允许系统截图。')
    # Confirm the package did not change during capture. This does not freeze animations.
    if requested_package and foreground:
        after_window = read(('after_window', ['dumpsys', 'window']))[1] or ''
        after = re.search(r'mCurrentFocus=.*?\s([\w.]+)/[\w.$]+', after_window)
        if after and after.group(1) != foreground:
            raise ValueError('截图期间前台应用发生变化，请停留在目标页面后重试。')
    return png, metadata
