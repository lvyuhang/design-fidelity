import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from virtual_devices import VirtualDevices, parse_badging, MAX_APK

class VirtualTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.manager=VirtualDevices(self.temp.name)
    def apk(self,abi='arm64-v8a'):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('AndroidManifest.xml',b'test manifest')
            if abi:z.writestr('lib/'+abi+'/sample.so',b'test')
        return out.getvalue()
    def test_reject_truncated_wrong_arch_and_non_apk(self):
        with self.assertRaises(ValueError):self.manager.import_apk(io.BytesIO(b'zip'),3,'bad.apk')
        data=self.apk('x86_64')
        with self.assertRaisesRegex(ValueError,'arm64'):self.manager.import_apk(io.BytesIO(data),len(data),'x86.apk')
        data=self.apk()
        with self.assertRaisesRegex(ValueError,'未完成'):self.manager.import_apk(io.BytesIO(data),len(data)+1,'cut.apk')
        with self.assertRaises(ValueError):self.manager.import_apk(io.BytesIO(),MAX_APK+1,'big.apk')
        self.assertFalse(list((self.manager.root/'packages').glob('*.part')))
    def test_upload_deduplicates_and_preserves_hash(self):
        data=self.apk()
        with patch('sdk_runtime.ready',return_value=False):
            a=self.manager.import_apk(io.BytesIO(data),len(data),'a.apk')
            b=self.manager.import_apk(io.BytesIO(data),len(data),'b.apk')
        self.assertEqual(a['id'],b['id']);self.assertEqual(len(self.manager.status()['packages']),1)
        self.assertEqual((self.manager.root/'packages'/(a['id']+'.apk')).read_bytes(),data)
    def test_mutations_cannot_target_usb_or_foreign_avd(self):
        with self.assertRaises(ValueError):self.manager.control({'action':'key','key':'home','serial':'usb'})
        self.manager.active={'serial':'emulator-5580','avd':'review_test'}
        with patch('capture.command',return_value='someone_else\nOK') as adb:
            with self.assertRaisesRegex(ValueError,'操作已拒绝'):self.manager.control({'serial':'emulator-5580','action':'key','key':'home'})
            self.assertEqual(adb.call_count,1)
    def test_no_unbounded_or_nonfinite_touch_input(self):
        self.manager.active={'serial':'emulator-5580','avd':'review_test','profile':{'width':1080,'height':2400}}
        with patch('capture.command',return_value='review_test\nOK') as adb:
            for value in [float('nan'),float('inf'),-1,1.1]:
                with self.assertRaises(ValueError):self.manager.control({'serial':'emulator-5580','action':'tap','x':value,'y':.5})
            self.assertEqual(adb.call_count,4)
    def test_profile_precision_and_snapshot_immutable(self):
        p=next(p for p in self.manager.profiles() if p['id']=='pixel-5')
        self.assertEqual(p['width_dp'],392.73)
        self.manager.active={'serial':'emulator-5580','profile':p}
        evidence=self.manager.evidence('emulator-5580');self.manager.active['profile']['density']=999
        self.assertEqual(evidence['runtime']['profile']['density'],440)
        self.assertIsNone(self.manager.evidence('usb'))
    def test_sdk_license_and_single_job(self):
        with self.assertRaises(ValueError):self.manager.submit('setup',{})
        self.manager.job={'status':'running'}
        with self.assertRaises(ValueError):self.manager.submit('start',{})
    def test_invalid_calibration_does_not_touch_running_device(self):
        with patch('sdk_runtime.ready',return_value=True),patch('platform.machine',return_value='arm64'),patch.object(self.manager,'stop') as stop:
            for value in [True,0,99,1001,497.5,float('inf'),float('nan'),'480']:
                with self.assertRaisesRegex(ValueError,'逻辑密度'):
                    self.manager.start({'profile_id':'pixel-5','density_override':value})
            for field,value in [('navigation','invalid'),('cutout','invalid')]:
                with self.assertRaisesRegex(ValueError,'系统栏'):
                    self.manager.start({'profile_id':'pixel-5',field:value})
            stop.assert_not_called()
    def test_geometry_ignores_secondary_mirror_display(self):
        from virtual_devices import display_geometry
        text='Display: mDisplayId=2\nROTATION_0={configFrame=[0,0][1106,2412]}\nDisplay: mDisplayId=0\nROTATION_0={configFrame=[0,136][1220,2581]}'
        self.assertEqual(display_geometry(text)['height_px'],2445)
        self.assertIsNone(display_geometry('Display: mDisplayId=2\nROTATION_0={configFrame=[0,0][1106,2412]}'))
        self.assertIsNone(display_geometry('unsupported vendor output'))
    def test_device_settings_isolated_and_persistent(self):
        a={'model_id':'xiaomi-17','test_width_dp':393,'density_override':480,'font_scale':1.3,'navigation':'gestural','cutout':'hole'}
        b={'model_id':'vivo-x300','test_width_dp':411,'font_scale':1,'navigation':'threebutton','cutout':'none'}
        self.manager.save_device_settings(a);self.manager.save_device_settings(b)
        fresh=VirtualDevices(self.temp.name).status()['device_settings']
        self.assertEqual(fresh['model:xiaomi-17']['density_override'],480)
        self.assertEqual(fresh['model:vivo-x300']['font_scale'],1)
        self.assertEqual(fresh['model:xiaomi-17']['source'],'user_test_settings')
        before=fresh.copy()
        with self.assertRaises(ValueError):self.manager.save_device_settings({**a,'density_override':float('nan')})
        with self.assertRaises(ValueError):self.manager.save_device_settings({**a,'profile_id':'pixel-5'})
        self.assertEqual(self.manager.status()['device_settings'],before)
    def test_launch_uses_only_active_package_and_surfaces_failure(self):
        self.manager.active={'serial':'emulator-5580','avd':'review_test','profile':{},'package':{'package':'com.example.app','activity':'com.example.Main'}}
        with patch('capture.command',side_effect=['review_test\nOK','Status: ok']) as adb:
            result=self.manager.control({'serial':'emulator-5580','action':'launch_app','package':'other.app'})
            self.assertEqual(result['package'],'com.example.app')
            self.assertEqual(adb.call_args.args[0][-1],'com.example.app/com.example.Main')
        with patch('capture.command',side_effect=['review_test\nOK','Error: Activity class does not exist']):
            with self.assertRaisesRegex(ValueError,'无法打开'):
                self.manager.control({'serial':'emulator-5580','action':'launch_app'})
    def test_parse_package_metadata(self):
        m=parse_badging("package: name='com.example.app' versionCode='12' versionName='2.0'\nminSdkVersion:'23'\nlaunchable-activity: name='com.example.Main'\napplication-label:'Test'")
        self.assertEqual(m['min_sdk'],23);self.assertEqual(m['package'],'com.example.app')
        with self.assertRaises(ValueError):parse_badging('bad input')

    def test_hot_configuration_keeps_emulator_and_updates_evidence(self):
        profile=self.manager.profile('pixel-5')
        self.manager.active={'serial':'emulator-5580','avd':'review_original','profile':profile,
                             'package':{'id':'same'},'density':440,'font_scale':1,'display_scale':1,
                             'navigation':'gestural','cutout':'none'}
        before=self.manager.active.copy()
        target={**profile,'width':720,'height':1600,'density':320}
        def shell(args,**kwargs):
            if args[-3:]==['emu','avd','name']:return 'review_original\nOK'
            if args[-2:]==['wm','size']:return 'Physical size: 1080x2340\nOverride size: 720x1600'
            if args[-2:]==['wm','density']:return 'Physical density: 440\nOverride density: 320'
            return ''
        with patch('capture.command',side_effect=shell) as adb,patch.object(self.manager,'save_device_settings'),patch('subprocess.Popen') as launch:
            self.manager.reconfigure({},target,1.3,1,'gestural','none',None)
            launch.assert_not_called()
            self.assertFalse(any('kill' in call.args[0] for call in adb.call_args_list))
        self.assertEqual(self.manager.active['avd'],before['avd'])
        self.assertEqual(self.manager.active['serial'],before['serial'])
        self.assertEqual(self.manager.evidence(before['serial'])['runtime']['width_dp'],360)
        self.assertEqual(self.manager.active['font_scale'],1.3)

    def test_hot_configuration_failure_restores_previous_configuration(self):
        previous={'serial':'emulator-5580','avd':'review_original','profile':self.manager.profile('pixel-5'),
                  'density':440,'font_scale':1,'navigation':'gestural','cutout':'none'}
        self.manager.active=previous.copy()
        with patch.object(self.manager,'owned_serial',return_value='emulator-5580'),patch.object(self.manager,'apply_display') as apply,patch('capture.command',return_value='invalid'):
            with self.assertRaisesRegex(ValueError,'未生效'):
                self.manager.reconfigure({},previous['profile'],1.3,1,'gestural','none',None)
            self.assertEqual(apply.call_count,2)
        self.assertEqual(self.manager.active,previous)


class DeviceCatalogTests(unittest.TestCase):
    def test_categories_cover_widths_without_oem_density_claims(self):
        from device_catalog import WIDTH_GROUPS, width_presets, MODELS
        profiles=width_presets()
        self.assertEqual(len(WIDTH_GROUPS),6)
        self.assertEqual(len(profiles),14)
        for p in profiles:self.assertEqual(p['width']*160/p['density'],p['width_dp'])
        self.assertEqual(len({m['id'] for m in MODELS}),len(MODELS))
        self.assertTrue(all(m['density_status']=='unknown' and m['source'].startswith('https://') for m in MODELS))
    def test_model_test_width_rounding_and_provenance(self):
        from device_catalog import model_profile
        p=model_profile('xiaomi-17',393)
        self.assertEqual((p['width'],p['height']),(1220,2656))
        self.assertLess(abs(p['width_dp']-393),.5)
        self.assertEqual(p['density_status'],'test_override')
        self.assertEqual(p['requested_width_dp'],393)
        self.assertIn('出厂',p['condition'])
        self.assertEqual(model_profile('oppo-find-n5-inner',720)['width'],2248)
        for model,width in [('bad',393),('xiaomi-17',960),('xiaomi-17',float('nan')),('xiaomi-17',True)]:
            with self.assertRaises(ValueError):model_profile(model,width)

if __name__=='__main__':unittest.main()
