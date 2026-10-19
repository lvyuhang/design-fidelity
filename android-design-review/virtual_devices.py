"""Managed Android preview sessions. Mutating ADB calls are restricted to our AVDs."""
import copy
import hashlib
import ipaddress
import json
import math
import os
import platform
import re
import shlex
import socket
import subprocess
import threading
import time
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlsplit, urlencode
from urllib.request import urlopen, Request, build_opener, HTTPRedirectHandler

import capture
import sdk_runtime
from device_catalog import WIDTH_GROUPS, MODEL_GROUPS, MODELS, width_presets, model_profile

CATALOG_SOURCE = 'https://android.googlesource.com/platform/tools/adt/idea/+/036498171bd3e52e4c959164aebafe93393d4c59/designer/testSrc/com/android/tools/idea/actions/DeviceMenuActionTest.kt'
PROFILES = width_presets() + [
    {'id':'pixel-5','name':'Pixel 5 / 4a','width':1080,'height':2340,'density':440,'models':['Google Pixel 5','Google Pixel 4a'],'source':CATALOG_SOURCE,'verification':'Android Studio 配置'},
    {'id':'pixel-8','name':'Pixel 8 / 7 / 6','width':1080,'height':2400,'density':420,'models':['Google Pixel 8','Google Pixel 8a','Google Pixel 7','Google Pixel 7a','Google Pixel 6','Google Pixel 6a'],'source':CATALOG_SOURCE,'verification':'Android Studio 配置'},
    {'id':'pixel-3a-xl','name':'Pixel 3a XL','width':1080,'height':2160,'density':400,'models':['Google Pixel 3a XL'],'source':CATALOG_SOURCE,'verification':'Android Studio 配置'},
]
MAX_APK = 1024**3


def display_geometry(output):
    # scrcpy may create secondary displays; only the physical Android display counts.
    blocks=re.split(r'(?=Display: mDisplayId=)',output)
    block=next((b for b in blocks if re.match(r'Display: mDisplayId=0\b',b)),None)
    if not block:return None
    m=re.search(r'ROTATION_0=\{[^\n]*?configFrame=\[(\d+),(\d+)\]\[(\d+),(\d+)\]',block)
    if not m:return None
    l,t,r,b=map(int,m.groups())
    return {'system_content_frame_px':[l,t,r,b],'width_px':max(0,r-l),'height_px':max(0,b-t),
            'source':'ADB dumpsys window displays / display 0 / portrait configFrame',
            'note':'系统参考内容区域；应用边到边绘制与键盘会影响实际内容区域'}

def validate_download_url(url):
    parts=urlsplit(url)
    if parts.scheme!='https' or not parts.hostname or parts.username or parts.password or parts.port not in (None,443):
        raise ValueError('请使用公网 HTTPS 下载链接。')
    addresses=socket.getaddrinfo(parts.hostname,443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('下载地址不能指向本机或内网。')
    return url

class PublicRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_download_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def open_download(url):
    validate_download_url(url)
    return build_opener(PublicRedirect()).open(Request(url,headers={'User-Agent':'DesignReview/1.0'}),timeout=30)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))
    temp.replace(path)


def parse_badging(output):
    if re.search(r"package:.*\bsplit='", output): raise ValueError('请选择完整 APK，暂不支持拆分 APK。')
    package = re.search(r"package: name='([^']+)' versionCode='([^']*)' versionName='([^']*)'", output)
    if not package or not re.fullmatch(r'[A-Za-z0-9_.]+', package[1]):
        raise ValueError('无法识别 APK 包名，支持完整 APK，不支持拆分安装包。')
    minimum = re.search(r"(?:minSdkVersion|sdkVersion):'(\d+)'", output)
    activity = re.search(r"launchable-activity: name='([^']+)'", output)
    label = re.search(r"application-label(?:-zh-CN)?:'([^']*)'", output)
    return {'package':package[1], 'version_code':package[2], 'version_name':package[3],
            'min_sdk':int(minimum[1]) if minimum else 1,
            'activity':activity[1] if activity else None, 'label':label[1] if label else package[1]}


def run(args, timeout=30):
    try:
        result = subprocess.run([str(a) for a in args], capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ValueError('操作超时，请重试。')
    if result.returncode:
        raise ValueError((result.stderr or result.stdout).decode('utf-8','replace')[-1200:] or '执行失败')
    return result.stdout.decode('utf-8','replace').strip()


class VirtualDevices:
    def __init__(self, data):
        self.root = Path(data) / 'virtual'
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.control_lock = threading.Lock()
        self.job = None
        self.cancel_event = threading.Event()
        self.process = None
        self.last_probe = 0
        self.active = self.read('active.json', None)

    def read(self, name, default):
        try: return json.loads((self.root / name).read_text())
        except (OSError, ValueError): return default

    def profiles(self):
        measured=self.read('profiles.json', [])
        items = [p for p in copy.deepcopy(PROFILES) if p['models'] or not any((m['width'],m['height'],m['density'])==(p['width'],p['height'],p['density']) for m in measured)] + measured
        for item in items:
            item['width_dp'] = round(item['width'] * 160 / item['density'], 2)
        return sorted(items, key=lambda p:(p['width_dp'],p['name']))

    def save_device_settings(self, body):
        model_id=body.get('model_id');profile_id=body.get('profile_id')
        if bool(model_id)==bool(profile_id):raise ValueError('请选择一个设备模板。')
        if model_id:
            model_profile(model_id,body.get('test_width_dp'))
            key='model:'+model_id
        else:
            self.profile(profile_id);key='profile:'+profile_id
        density=body.get('density_override')
        if density is not None and (isinstance(density,bool) or not isinstance(density,(int,float)) or not math.isfinite(density) or int(density)!=density or not 100<=density<=1000):
            raise ValueError('逻辑密度需为 100–1000 的整数。')
        font=body.get('font_scale',1);display=body.get('display_scale',1)
        if isinstance(font,bool) or not isinstance(font,(int,float)) or not math.isfinite(font) or not .5<=font<=2 or isinstance(display,bool) or display not in (.85,1,1.15):raise ValueError('缩放配置无效。')
        navigation=body.get('navigation','threebutton');cutout=body.get('cutout','none')
        if navigation not in ('gestural','threebutton') or cutout not in ('none','hole','tall'):raise ValueError('系统栏配置无效。')
        item={'density_override':density,'font_scale':font,'display_scale':display,'navigation':navigation,'cutout':cutout,
              'test_width_dp':body.get('test_width_dp') if model_id else None,
              'source':'user_test_settings','saved_at':time.time()}
        with self.lock:
            saved=self.read('device-settings.json',{});saved[key]=item;write_json(self.root/'device-settings.json',saved)
        return {'key':key,'settings':item}

    def status(self):
        with self.lock:
            running = self.job and self.job['status']=='running'
            if not running and self.active and time.monotonic()-self.last_probe>5:
                self.last_probe=time.monotonic()
                try:
                    serial=self.active['serial']
                    device=next((d for d in capture.devices()['devices'] if d['id']==serial),None)
                    missing=not device or device['state']!='device'
                    if not missing:
                        name=capture.command(['-s',serial,'emu','avd','name'],timeout=3).splitlines()[0]
                        missing=name!=self.active['avd']
                    if missing:
                        self.active=None
                        write_json(self.root/'active.json',None)
                except (ValueError,IndexError):
                    pass  # A transient ADB outage must not erase a recoverable session.
            if self.active and not running and 'screen_geometry' not in self.active:
                try:self.active['screen_geometry']=display_geometry(capture.command(['-s',self.active['serial'],'shell','dumpsys','window','displays'],timeout=5))
                except ValueError:self.active['screen_geometry']=None
                write_json(self.root/'active.json',self.active)
            if self.process and self.process.poll() is not None and not running:
                self.active = None
                write_json(self.root / 'active.json', None)
                self.process = None
            return {'runtime_ready':sdk_runtime.ready(), 'supported':platform.system()=='Darwin' and platform.machine()=='arm64',
                    'api_level':34,'profiles':self.profiles(),'width_groups':copy.deepcopy(WIDTH_GROUPS),
                    'model_groups':copy.deepcopy(MODEL_GROUPS),'models':copy.deepcopy(MODELS),'device_settings':self.read('device-settings.json',{}),'packages':self.read('packages.json', []),
                    'active':copy.deepcopy(self.active),'job':copy.deepcopy(self.job)}

    def import_apk(self, stream, length, name):
        if not 0 < length <= MAX_APK:
            raise ValueError('请选择不超过 1 GB 的 APK。')
        key = uuid.uuid4().hex
        folder = self.root / 'packages'
        folder.mkdir(exist_ok=True)
        temp = folder / (key + '.part')
        digest = hashlib.sha256()
        try:
            with temp.open('wb') as target:
                remaining = length
                while remaining:
                    data = stream.read(min(1024*1024, remaining))
                    if not data: raise ValueError('上传未完成，请重新选择 APK。')
                    target.write(data); digest.update(data); remaining -= len(data)
            with zipfile.ZipFile(temp) as apk:
                names = apk.namelist()
                if 'AndroidManifest.xml' not in names: raise ValueError('文件不是完整 APK。')
                abis = sorted({p.split('/')[1] for p in names if p.startswith('lib/') and p.endswith('.so')})
                if abis and 'arm64-v8a' not in abis:
                    raise ValueError('此 APK 不含 arm64-v8a，无法在当前 Apple Silicon 模拟器运行。')
            checksum = digest.hexdigest()
            metadata = {'id':checksum,'sha256':checksum,'name':Path(name).name[:180],'size':length,'abis':abis,'imported_at':time.time()}
            if sdk_runtime.ready(): metadata.update(self.inspect(temp))
            destination = folder / (checksum + '.apk')
            temp.replace(destination)
            with self.lock:
                packages = [p for p in self.read('packages.json', []) if p['id'] != checksum]
                write_json(self.root / 'packages.json', [metadata] + packages)
            return metadata
        except zipfile.BadZipFile:
            raise ValueError('无法打开 APK，请检查文件是否完整。')
        finally:
            temp.unlink(missing_ok=True)

    def inspect(self, path):
        metadata = parse_badging(run([sdk_runtime.SDK / 'build-tools/35.0.0/aapt2','dump','badging',path]))
        if metadata['min_sdk'] > 34: raise ValueError('该包要求 Android API ' + str(metadata['min_sdk']) + '，当前镜像为 API 34。')
        if not metadata['activity']: raise ValueError('APK 没有可启动的页面。')
        return metadata

    def update(self, phase, progress=None):
        with self.lock:
            if self.job: self.job.update(phase=phase, progress=progress)

    def submit(self, operation, body):
        with self.lock:
            if self.job and self.job['status']=='running': raise ValueError('已有任务正在执行，请等待或取消。')
            if operation not in ('setup','start','download','stop'): raise ValueError('未知操作')
            if operation == 'setup' and body.get('accept_license') is not True:
                raise ValueError('请先阅读并同意 Android SDK 许可协议。')
            self.cancel_event = threading.Event()
            self.job = {'id':uuid.uuid4().hex,'operation':operation,'status':'running','phase':'准备中','progress':None}
            if operation == 'setup': write_json(self.root/'license-consent.json',{'accepted_at':time.time(),'url':'https://developer.android.com/studio/terms'})
            def work():
                try:
                    if operation=='setup': sdk_runtime.install(self.update, self.cancel_event.is_set)
                    elif operation=='start': self.start(body)
                    elif operation=='download': self.download(body.get('url',''))
                    elif operation=='stop': self.stop()
                    else: raise ValueError('未知操作')
                    with self.lock: self.job['status']='cancelled' if self.cancel_event.is_set() else 'done'
                except Exception as error:
                    with self.lock: self.job.update(status='cancelled' if self.cancel_event.is_set() else 'error',error=str(error))
            threading.Thread(target=work, daemon=True, name='virtual-'+operation).start()
            return copy.deepcopy(self.job)

    def cancel(self):
        self.cancel_event.set()
        return {'cancelled':True}

    def check_cancel(self):
        if self.cancel_event.is_set(): raise ValueError('已取消。')

    def download(self, url):
        parts = urlsplit(url)
        if parts.scheme!='https' or not parts.hostname or parts.username:
            raise ValueError('请输入 HTTPS APK 下载链接。')
        # Direct APK URLs only. Distribution pages remain explicit and never scrape credentials.
        self.update('获取开发包链接')
        if parts.hostname == 'fir.xcxwo.com':
            url = self.fir_url(parts.path.strip('/'))
        with open_download(url) as response:
            content_type = response.headers.get('Content-Type','')
            if 'text/' in content_type or 'json' in content_type:
                raise ValueError('此链接返回了网页。请从分发页下载 APK 后上传，或使用 APK 直链。')
            path = self.root / ('download-' + uuid.uuid4().hex + '.apk')
            total = int(response.headers.get('Content-Length') or 0)
            if total > MAX_APK: raise ValueError('APK 超过 1 GB。')
            size = 0
            try:
                with path.open('wb') as target:
                    while True:
                        self.check_cancel()
                        chunk = response.read(1024*1024)
                        if not chunk: break
                        size += len(chunk)
                        if size > MAX_APK: raise ValueError('APK 超过 1 GB。')
                        target.write(chunk)
                        self.update(f'下载 APK · {size//1048576} MB', round(size/total*100) if total else None)
                with path.open('rb') as stream: imported=self.import_apk(stream,size,Path(parts.path).name if parts.path.endswith('.apk') else '链接导入.apk')
                self.update('已导入 '+imported.get('label',imported['name']),100)
            finally: path.unlink(missing_ok=True)

    def fir_url(self, short):
        if not re.fullmatch(r'[A-Za-z0-9]{2,32}', short): raise ValueError('分发链接格式无效。')
        endpoint = 'https://download.appmeta.cn/' + short + '?referer=fir.xcxwo.com&visit_https=true'
        with open_download(endpoint) as response: data=json.load(response)
        app=data.get('app') or {}
        if data.get('auth') is not True or app.get('has_passwd') or not app.get('token') or app.get('type')!='android':
            raise ValueError('此 FIR 页面需要验证或没有 Android 包。请打开原链接下载 APK 后上传。')
        app_id=app.get('id','')
        if not re.fullmatch(r'[a-zA-Z0-9]+',app_id): raise ValueError('无法识别 FIR 应用。')
        release=(app.get('releases') or {}).get('master') or {}
        query={'short':short,'download_token':app['token']}
        if release.get('id'):query['release_id']=release['id']
        self.update('已识别 '+str(app.get('name','应用'))+' · '+str(release.get('version','')))
        return 'https://download.appmeta.cn/apps/'+app_id+'/install?'+urlencode(query)

    def profile(self, key):
        value = next((p for p in self.profiles() if p['id']==key), None)
        if not value: raise ValueError('设备配置不存在。')
        return value

    def owned_serial(self):
        if not self.active: raise ValueError('模拟器尚未启动。')
        serial = self.active['serial']
        name = capture.command(['-s',serial,'emu','avd','name'], timeout=5).splitlines()[0]
        if name != self.active['avd'] or not name.startswith('review_'):
            raise ValueError('设备不是工作台管理的模拟器，操作已拒绝。')
        return serial

    def stop(self):
        if self.active:
            serial = self.active['serial']
            if not any(d['id']==serial for d in capture.devices()['devices']):
                self.active=None;self.process=None;write_json(self.root/'active.json',None)
                return
            serial = self.owned_serial()
            capture.command(['-s',serial,'emu','kill'], timeout=10)
            if self.process:
                try: self.process.wait(timeout=20)
                except subprocess.TimeoutExpired: self.process.terminate(); self.process.wait(timeout=10)
            else:
                deadline=time.monotonic()+20
                while time.monotonic()<deadline:
                    if not any(d['id']==serial for d in capture.devices()['devices']): break
                    time.sleep(.5)
            self.active = None
            self.process = None
            write_json(self.root/'active.json',None)
        self.update('模拟器已停止')

    def start(self, body):
        if not sdk_runtime.ready(): raise ValueError('请先安装 Android 环境。')
        if platform.machine()!='arm64': raise ValueError('当前运行时仅支持 Apple Silicon Mac。')
        p = model_profile(body['model_id'],body.get('test_width_dp')) if body.get('model_id') else self.profile(body.get('profile_id'))
        override=body.get('density_override')
        if override is not None:
            if isinstance(override,bool) or not isinstance(override,(int,float)) or not math.isfinite(override) or int(override)!=override or not 100<=override<=1000:
                raise ValueError('逻辑密度需为 100–1000 的整数。')
            p=copy.deepcopy(p);p['density']=int(override);p['width_dp']=round(p['width']*160/override,2)
            p['density_status']='manual_calibration'
        navigation=body.get('navigation','threebutton');cutout=body.get('cutout','none')
        if navigation not in ('gestural','threebutton') or cutout not in ('none','hole','tall'):raise ValueError('系统栏配置无效。')
        package = next((a for a in self.read('packages.json',[]) if a['id']==body.get('package_id')),None)
        if not package: raise ValueError('请先上传 APK。')
        font = float(body.get('font_scale',1))
        display = float(body.get('display_scale',1))
        if not math.isfinite(font) or not .5<=font<=2 or display not in (.85,1,1.15): raise ValueError('缩放配置无效。')
        if self.active and self.active.get('state')=='ready' and self.active.get('package',{}).get('id')==package['id']:
            self.reconfigure(body,p,font,display,navigation,cutout,override)
            return
        apk = self.root / 'packages' / (package['id']+'.apk')
        package.update(self.inspect(apk))
        with self.lock:
            write_json(self.root/'packages.json',[package if a['id']==package['id'] else a for a in self.read('packages.json',[])])
        self.check_cancel()
        self.update('准备虚拟设备')
        if self.active: self.stop()
        self.check_cancel()
        avd_name = 'review_' + p['id'].replace('-','_')
        avd_home = self.root/'avd'; avd_dir = avd_home/(avd_name+'.avd')
        avd_dir.mkdir(parents=True,exist_ok=True)
        settings = {'AvdId':avd_name,'avd.ini.displayname':'设计验收 '+str(round(p['width_dp']))+' dp','avd.ini.encoding':'UTF-8',
                    'abi.type':'arm64-v8a','hw.cpu.arch':'arm64','hw.cpu.ncore':'4','hw.ramSize':'2048',
                    'hw.lcd.width':p['width'],'hw.lcd.height':p['height'],'hw.lcd.density':p['density'],
                    'hw.gpu.enabled':'yes','hw.gpu.mode':'host','hw.keyboard':'yes','hw.mainKeys':'no',
                    'hw.audioInput':'no','hw.audioOutput':'no','hw.camera.back':'none','hw.camera.front':'none',
                    'disk.dataPartition.size':'4G','image.sysdir.1':str(sdk_runtime.SDK/sdk_runtime.IMAGE)+'/',
                    'tag.id':'default','tag.display':'Default','PlayStore.enabled':'false',
                    'showDeviceFrame':'no','fastboot.forceColdBoot':'yes','fastboot.forceFastBoot':'no'}
        (avd_dir/'config.ini').write_text(''.join(f'{k}={v}\n' for k,v in settings.items()))
        (avd_home/(avd_name+'.ini')).write_text(f'avd.ini.encoding=UTF-8\npath={avd_dir}\ntarget=android-34\n')
        used={d['id'] for d in capture.devices()['devices']}
        port=None
        for candidate in range(5580,5680,2):
            if 'emulator-'+str(candidate) in used: continue
            try:
                with socket.socket() as s, socket.socket() as t:
                    s.bind(('127.0.0.1',candidate));t.bind(('127.0.0.1',candidate+1))
                port=candidate;break
            except OSError: continue
        if port is None: raise ValueError('没有空闲的模拟器端口。')
        env={**os.environ,'ANDROID_AVD_HOME':str(avd_home),'ANDROID_SDK_ROOT':str(sdk_runtime.SDK),'ANDROID_HOME':str(sdk_runtime.SDK)}
        with (self.root/'emulator.log').open('w') as log:
            self.process=subprocess.Popen([str(sdk_runtime.SDK/'emulator/emulator'),'-avd',avd_name,'-port',str(port),
                '-no-window','-no-audio','-no-boot-anim','-no-snapshot','-gpu','host'],env=env,stdout=log,stderr=log,start_new_session=True)
        serial='emulator-'+str(port)
        try:
            deadline=time.monotonic()+180
            self.update('启动 Android，首次启动约 1–3 分钟')
            while time.monotonic()<deadline:
                self.check_cancel()
                if self.process.poll() is not None: raise ValueError('模拟器启动失败，请查看 virtual/emulator.log。')
                try:
                    if capture.command(['-s',serial,'shell','getprop','sys.boot_completed'],timeout=5)=='1': break
                except ValueError: pass
                time.sleep(1)
            else: raise ValueError('Android 启动超时，请重试。')
            self.active={'serial':serial,'avd':avd_name,'profile':p,'package':package,'font_scale':font,'display_scale':display,
                         'density':round(p['density']*display),'width_dp':round(p['width']*160/round(p['density']*display),2),
                         'api_level':34,'density_override':override,'navigation':navigation,'cutout':cutout,'started_at':time.time(),'state':'starting'}
            write_json(self.root/'active.json',self.active)
            for args in [['wm','size',f"{p['width']}x{p['height']}"],['wm','density',str(self.active['density'])],['settings','put','system','font_scale',str(font)],
                         ['settings','put','system','screen_off_timeout','2147483647'],['input','keyevent','82']]:
                self.check_cancel();capture.command(['-s',serial,'shell']+args)
            capture.command(['-s',serial,'shell','cmd','overlay','enable-exclusive','--category','com.android.internal.systemui.navbar.'+navigation])
            for shape in ('hole','tall'):
                capture.command(['-s',serial,'shell','cmd','overlay','disable','com.android.internal.display.cutout.emulation.'+shape])
            if cutout!='none':capture.command(['-s',serial,'shell','cmd','overlay','enable-exclusive','--category','com.android.internal.display.cutout.emulation.'+cutout])
            self.update('安装 '+package.get('label',package['name']))
            result=capture.command(['-s',serial,'install','-r',str(apk)],timeout=120)
            if 'Success' not in result: raise ValueError(result or 'APK 安装失败。')
            self.check_cancel()
            self.update('打开应用')
            component=package['package']+'/'+package['activity']
            if not re.fullmatch(r'[A-Za-z0-9_.$/]+',component): raise ValueError('启动页面格式无效。')
            result=capture.command(['-s',serial,'shell','am','start','-W','-n',component],timeout=30)
            if 'Error:' in result: raise ValueError(result)
            self.active['state']='ready'
            try:self.active['screen_geometry']=display_geometry(capture.command(['-s',serial,'shell','dumpsys','window','displays'],timeout=5))
            except ValueError:self.active['screen_geometry']=None
            write_json(self.root/'active.json',self.active)
            self.save_device_settings(body)
            self.update('模拟器已就绪',100)
        except Exception:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:self.process.wait(timeout=15)
                except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
            self.active=None;self.process=None;write_json(self.root/'active.json',None)
            raise

    def apply_display(self, serial, config):
        p=config['profile']
        commands=[['wm','size',f"{p['width']}x{p['height']}"],
                  ['wm','density',str(config['density'])],
                  ['settings','put','system','font_scale',str(config['font_scale'])],
                  ['cmd','overlay','enable-exclusive','--category','com.android.internal.systemui.navbar.'+config['navigation']]]
        commands += [['cmd','overlay','disable','com.android.internal.display.cutout.emulation.'+shape] for shape in ('hole','tall')]
        if config['cutout']!='none':commands.append(['cmd','overlay','enable-exclusive','--category','com.android.internal.display.cutout.emulation.'+config['cutout']])
        for args in commands:
            result=capture.command(['-s',serial,'shell']+args,timeout=10)
            if re.search(r'(?im)^(error|exception|securityexception)',result):raise ValueError(result)

    def reconfigure(self, body, profile, font, display, navigation, cutout, override):
        with self.control_lock:
            serial=self.owned_serial()
            previous=copy.deepcopy(self.active)
            density=round(profile['density']*display)
            current={**previous,'profile':profile,'font_scale':font,'display_scale':display,
                     'density':density,'width_dp':round(profile['width']*160/density,2),
                     'density_override':override,'navigation':navigation,'cutout':cutout}
            self.update('正在应用设备配置，无需重启 Android')
            try:
                self.check_cancel()
                self.apply_display(serial,current)
                self.check_cancel()
                size=capture.command(['-s',serial,'shell','wm','size'],timeout=5)
                actual=re.findall(r'(\d+)x(\d+)',size)
                measured=capture.command(['-s',serial,'shell','wm','density'],timeout=5)
                densities=re.findall(r'density:\s*(\d+)',measured)
                if not actual or tuple(map(int,actual[-1]))!=(profile['width'],profile['height']) or not densities or int(densities[-1])!=density:
                    raise ValueError('设备配置未生效，已尝试恢复之前的配置。')
                current['screen_geometry']=display_geometry(capture.command(['-s',serial,'shell','dumpsys','window','displays'],timeout=5))
                current['configured_at']=time.time()
                self.active=current
                write_json(self.root/'active.json',current)
                self.save_device_settings(body)
                self.update('设备配置已应用，正在恢复预览',100)
            except Exception as error:
                try:self.apply_display(serial,previous)
                except Exception as rollback_error:
                    self.active={**previous,'state':'configuration_error'}
                    write_json(self.root/'active.json',self.active)
                    raise ValueError('应用配置失败，恢复旧配置也失败，请重新启动模拟器。') from rollback_error
                self.active=previous
                write_json(self.root/'active.json',previous)
                raise error

    def control(self, body):
        with self.control_lock:
            if self.job and self.job['status']=='running': raise ValueError('模拟器正在准备，请稍候。')
            serial=self.owned_serial()
            if body.get('serial')!=serial: raise ValueError('预览设备已经变化，请重试。')
            action=body.get('action')
            p=self.active['profile']
            def point(key, maximum):
                value=float(body.get(key,-1))
                if not math.isfinite(value) or not 0<=value<=1: raise ValueError('触控坐标无效。')
                return str(min(maximum-1,round(value*maximum)))
            if action=='launch_app':
                package=self.active.get('package',{})
                component=package.get('package','')+'/'+package.get('activity','')
                if not re.fullmatch(r'[A-Za-z0-9_.$]+/[A-Za-z0-9_.$]+',component):raise ValueError('测试 App 启动信息缺失，请重新选择开发包。')
                result=capture.command(['-s',serial,'shell','am','start','-W','-n',component],timeout=30)
                if 'Error:' in result or 'Exception' in result:raise ValueError('无法打开测试 App：'+result[-500:])
                return {'ok':True,'package':package['package']}
            if action=='tap': args=['input','tap',point('x',p['width']),point('y',p['height'])]
            elif action=='swipe': args=['input','swipe',point('x',p['width']),point('y',p['height']),point('x2',p['width']),point('y2',p['height']),str(min(1500,max(80,int(body.get('duration',300)))))]
            elif action=='key':
                keys={'back':'4','home':'3','recent':'187','enter':'66','delete':'67','tab':'61'}
                if body.get('key') not in keys: raise ValueError('不支持的按键。')
                args=['input','keyevent',keys[body['key']]]
            elif action=='text':
                value=str(body.get('text',''))
                if not value or len(value)>500 or not value.isascii() or any(ord(c)<32 for c in value):
                    raise ValueError('当前快捷输入支持英文、数字和符号，其他文字请使用安卓输入法。')
                args=['input','text',shlex.quote(value.replace(' ','%s'))]
            else: raise ValueError('不支持的操作。')
            capture.command(['-s',serial,'shell']+args, timeout=8)
            return {'ok':True}

    def collect(self, serial):
        if not any(d['id']==serial and d['state']=='device' and d['kind']!='emulator' for d in capture.devices()['devices']):
            raise ValueError('请选择已授权的 USB 真机。')
        def shell(*args):return capture.command(['-s',serial,'shell',*args],timeout=8)
        size=shell('wm','size');density=shell('wm','density')
        dims=re.findall(r'(\d+)x(\d+)',size);dpi=re.findall(r'density:\s*(\d+)',density)
        if not dims or not dpi: raise ValueError('无法读取设备显示参数。')
        width,height=map(int,dims[-1]);d=int(dpi[-1])
        if not 160<=width<=4000 or not 160<=height<=8000 or not 100<=d<=1000: raise ValueError('显示配置超出支持范围。')
        model=shell('getprop','ro.product.model');brand=shell('getprop','ro.product.brand')
        name='OPPO Reno10 (PHW110)' if model=='PHW110' else (brand+' '+model)
        item={'id':'measured-'+hashlib.sha256(f'{model}-{width}-{height}-{d}'.encode()).hexdigest()[:12],
              'name':name,'models':[name],'width':width,'height':height,'density':d,'verification':'真机采集',
              'android_version':shell('getprop','ro.build.version.release'),'font_scale':shell('settings','get','system','font_scale'),
              'sampled_at':time.time(),'source':'ADB wm size / wm density','display_override':'Override' in size+density,
              'condition':'采集时显示设置；不保证为出厂默认'}
        try:
            mode=shell('settings','get','secure','navigation_mode');item['navigation']='gestural' if mode=='2' else 'threebutton' if mode=='0' else None
        except ValueError:item['navigation']=None
        try:item['screen_geometry']=display_geometry(shell('dumpsys','window','displays'))
        except ValueError:item['screen_geometry']=None
        with self.lock:write_json(self.root/'profiles.json',[p for p in self.read('profiles.json',[]) if p['id']!=item['id']]+[item])
        return item

    def evidence(self, serial):
        if not self.active or self.active['serial']!=serial: return None
        return {'schema_version':1,'source':'managed_emulator','runtime':copy.deepcopy(self.active),
                'ui_tree':None,'ai_comparison':None}
