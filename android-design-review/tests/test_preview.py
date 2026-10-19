import sys
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import capture
from imaging import png_bytes
from preview import PreviewStore


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.raw = png_bytes(Image.new('RGB', (1080, 2412), 'green'))
        self.next_raw = png_bytes(Image.new('RGB', (1080, 2412), 'red'))
        self.meta = {'package':'com.test.app', 'foreground_package':'com.test.app',
                     'versionName':'1.0', 'device':{'id':'test'}}
        self.patcher = patch.object(capture, 'capture', return_value=(self.raw, self.meta))
        self.patcher.start();self.addCleanup(self.patcher.stop)
        self.store = PreviewStore(max_frames=2, stream_factory=None)

    def test_freeze_saves_displayed_frame_not_latest_or_preview_jpeg(self):
        shown = self.store.start('test')
        with patch.object(capture,'preview_frame',return_value=(self.next_raw,'com.test.app')):
            latest = self.store.next_frame(shown['session_id'])
        raw, meta = self.store.freeze(shown['session_id'],shown['frame_id'],'test')
        self.assertEqual(raw, self.raw)
        self.assertNotEqual(raw, self.next_raw)
        self.assertEqual(meta['preview_frame_id'],shown['frame_id'])
        self.assertEqual(shown['image_size'],[1080,2412])
        self.assertTrue(shown['preview_url'].startswith('data:image/jpeg;base64,'))
        self.assertNotEqual(shown['frame_id'],latest['frame_id'])

    def test_reject_wrong_device_expired_and_stopped_session(self):
        shown = self.store.start('test')
        args = (shown['session_id'],shown['frame_id'])
        with self.assertRaises(ValueError): self.store.freeze(*args,'other')
        self.store.sessions[args[0]]['touched'] -= 100
        with self.assertRaises(ValueError):self.store.freeze(*args,'test')
        shown = self.store.start('test')
        self.store.stop(shown['session_id'])
        with self.assertRaises(ValueError):self.store.next_frame(shown['session_id'])

    def test_memory_and_frame_count_bounded(self):
        shown = self.store.start('test')
        with patch.object(capture,'preview_frame',return_value=(self.next_raw,'com.test.app')):
            self.store.next_frame(shown['session_id']);self.store.next_frame(shown['session_id'])
        with self.assertRaises(ValueError):self.store.freeze(shown['session_id'],shown['frame_id'],'test')
        self.assertEqual(len(self.store.sessions[shown['session_id']]['frames']),2)

    def test_old_frame_expires_even_while_session_active(self):
        shown = self.store.start('test')
        session = self.store.sessions[shown['session_id']]
        metadata, stamp = session['frames'][shown['frame_id']]
        session['frames'][shown['frame_id']] = metadata, stamp-100
        with self.assertRaises(ValueError):self.store.freeze(shown['session_id'],shown['frame_id'],'test')

    def test_black_frame_requires_awake_screen_but_dark_pages_remain_valid(self):
        shown = self.store.start('test')
        black = png_bytes(Image.new('RGB', (1080, 2412), 'black'))
        with patch.object(capture, 'preview_frame', return_value=(black, None)):
            with patch.object(capture, 'ensure_screen_awake', side_effect=ValueError('手机已息屏')):
                with self.assertRaisesRegex(ValueError, '手机已息屏'):
                    self.store.next_frame(shown['session_id'])
            with patch.object(capture, 'ensure_screen_awake', return_value=None):
                packet = self.store.next_frame(shown['session_id'])
                self.assertEqual(packet['image_size'], [1080, 2412])

    def test_metadata_copied_and_app_version_not_misattributed(self):
        shown = self.store.start('test')
        with patch.object(capture,'preview_frame',return_value=(self.next_raw,'com.new.app')):
            other = self.store.next_frame(shown['session_id'])
        meta = self.store.sessions[shown['session_id']]['frames'][other['frame_id']][0]
        self.assertIsNone(meta['versionName'])
        self.assertEqual(meta['package'],'com.new.app')
        original = self.store.sessions[shown['session_id']]['frames'][shown['frame_id']][0]
        self.assertEqual(original['versionName'],'1.0')

    def test_device_screen_preview_does_not_bind_foreground_app(self):
        window = lambda name:'mCurrentFocus=Window{aa u0 '+name+'/.Main}'
        with patch.object(capture,'command',return_value=self.raw) as command:
            raw, foreground=capture.preview_frame('test')
            self.assertEqual(raw,self.raw);self.assertIsNone(foreground);self.assertEqual(command.call_count,1)
        with patch.object(capture,'command',side_effect=[window('com.test.app'),self.raw,window('com.other.app')]):
            with self.assertRaises(ValueError):capture.preview_frame('test','com.test.app')
        with patch.object(capture,'command',return_value=window('com.other.app')) as command:
            with self.assertRaises(ValueError):capture.preview_frame('test','com.test.app')
            self.assertEqual(command.call_count,1)

    def test_video_stream_drives_preview_but_freeze_uses_lossless_adb_capture(self):
        class Stream:
            def __init__(self, serial): self.stopped = False
            def start(self): return self
            def get(self, after): return 7, Image.new('RGB', (858, 1920), 'blue')
            def stop(self): self.stopped = True
        store = PreviewStore(stream_factory=Stream)
        shown = store.start('test')
        packet = store.next_frame(shown['session_id'])
        self.assertEqual(packet['transport'], 'video')
        self.assertEqual(packet['image_size'], [858, 1920])
        raw, metadata = store.freeze(packet['session_id'], packet['frame_id'], 'test')
        self.assertEqual(raw, self.raw)
        self.assertEqual(metadata['capture_source'], 'lossless ADB PNG at screenshot action')
        store.stop(shown['session_id'])

    def test_video_failure_falls_back_to_adb_preview(self):
        instances = []
        class BrokenStream:
            def __init__(self, serial): self.stopped = False; instances.append(self)
            def start(self): return self
            def get(self, after): raise ValueError('encoder unavailable')
            def stop(self): self.stopped = True
        store = PreviewStore(stream_factory=BrokenStream)
        shown = store.start('test')
        with patch.object(capture, 'preview_frame', return_value=(self.next_raw, None)):
            packet = store.next_frame(shown['session_id'])
        self.assertEqual(packet['transport'], 'adb')
        self.assertTrue(instances[0].stopped)


class StreamResponseTests(unittest.TestCase):
    def test_continuous_response_preserves_frame_ids_and_stops_on_disconnect(self):
        import io, json, server
        handler=server.Handler.__new__(server.Handler)
        handler.send_response=Mock();handler.send_header=Mock();handler.end_headers=Mock()
        handler.connection=Mock();handler.wfile=io.BytesIO()
        store=Mock();store.lock=__import__('threading').RLock()
        store.next_frame.side_effect=[{'frame_id':'a','image_size':[922,2010]}, {'frame_id':'b','image_size':[922,2010]}, BrokenPipeError()]
        with patch.object(server,'PREVIEW',store):handler.stream_preview('session')
        packets=[json.loads(line) for line in handler.wfile.getvalue().splitlines()]
        self.assertEqual([p['frame_id'] for p in packets],['a','b'])
        store._get.assert_called_once_with('session')
        self.assertTrue(handler.close_connection)
        handler.send_header.assert_any_call('Cache-Control','no-store')

    def test_expired_session_rejected_before_stream_headers(self):
        import server
        handler=server.Handler.__new__(server.Handler);handler.send_response=Mock()
        store=Mock();store.lock=__import__('threading').RLock();store._get.side_effect=ValueError('expired')
        with patch.object(server,'PREVIEW',store),self.assertRaises(ValueError):handler.stream_preview('expired')
        handler.send_response.assert_not_called()

if __name__=='__main__':unittest.main()
