"""Export licensed system fonts locally; no historical screenshots required."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from fontTools import subset
from fontTools.ttLib import TTFont, TTCollection

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ('PingFangSC-Regular.otf', 'PingFangSC-Medium.otf',
            'PingFangSC-Semibold.otf', 'PingFangSC-Full-Regular.ttf',
            'PingFangSC-Full-Medium.ttf', 'ArialUnicode-Gift.ttf')


def discover_pingfang(explicit=None):
    if explicit:
        return Path(explicit).expanduser()
    candidates = [Path('/System/Library/Fonts/PingFang.ttc')]
    for base in (Path('/System/Library/AssetsV2'), Path('/System/Library/Assets')):
        if base.exists():
            candidates.extend(sorted(base.glob('com_apple_MobileAsset_Font*/*/AssetData/PingFang.ttc')))
    return next((p for p in candidates if p.is_file()), None)


def prepare(output, font_dir=None, pingfang=None, arial=None, force=False):
    output = Path(output).resolve(); output.mkdir(parents=True, exist_ok=True)
    source_label = 'existing-local-files'
    if font_dir:
        source = Path(font_dir).expanduser().resolve()
        missing = [n for n in EXPECTED if not (source/n).is_file()]
        if missing: raise ValueError('字体目录缺少：' + ', '.join(missing))
        for name in EXPECTED:
            if (force or not (output/name).exists()) and source != output:
                shutil.copyfile(source/name, output/name)
        source_label = 'user-supplied-font-directory'
    elif force or any(not (output/n).is_file() for n in EXPECTED):
        source = discover_pingfang(pingfang)
        if source is None or not source.is_file():
            raise ValueError('未找到本机 PingFang.ttc。请在 macOS 字体册下载苹方，或用 --font-dir 提供有权使用的完整字体目录；不会静默替换字体。')
        gift = Path(arial).expanduser() if arial else next((p for p in (
            Path('/Library/Fonts/Arial Unicode.ttf'),
            Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')) if p.is_file()), None)
        if (force or not (output/'ArialUnicode-Gift.ttf').exists()) and (gift is None or not gift.is_file()):
            raise ValueError('历史礼物文案需要 Arial Unicode 字体，请用 --arial-unicode 指定有权使用的字体。')
        collection = TTCollection(source, lazy=True)
        faces = {f['name'].getDebugName(6): i for i, f in enumerate(collection.fonts)}
        collection.close()
        for face in ('Regular','Medium','Semibold'):
            name = 'PingFangSC-'+face
            if name not in faces: raise ValueError('字体集合缺少 '+name)
            for target in [output/(name+'.otf')] + ([output/('PingFangSC-Full-'+face+'.ttf')] if face != 'Semibold' else []):
                if force or not target.exists():
                    with TTFont(source,fontNumber=faces[name],recalcTimestamp=False) as f: f.save(target)
        target = output/'ArialUnicode-Gift.ttf'
        if force or not target.exists():
            with TTFont(gift,recalcTimestamp=False) as f:
                sub = subset.Subsetter();sub.populate(text='礼物名称');sub.subset(f);f.save(target)
        source_label = 'local-system-fonts'
    receipt = {'redistribution':False,'source':source_label,'fonts':[]}
    for name in EXPECTED:
        path = output/name
        with TTFont(path) as f:
            cmap = f.getBestCmap() or {}
            required = '礼物名称' if name == 'ArialUnicode-Gift.ttf' else '设置提现支付宝≈¥发现消息关系任务我的'
            missing = ''.join(ch for ch in required if ord(ch) not in cmap)
            if missing: raise ValueError(name+' 缺字 '+missing+'；请用 --force 从完整字体重新生成。')
        receipt['fonts'].append({'file':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
    (output/'font-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'flutter_ui_components/assets/fonts')
    p.add_argument('--font-dir');p.add_argument('--pingfang',default=os.environ.get('DESIGN_FIDELITY_PINGFANG', os.environ.get('JUXINGGE_PINGFANG')))
    p.add_argument('--arial-unicode',default=os.environ.get('DESIGN_FIDELITY_ARIAL_UNICODE', os.environ.get('JUXINGGE_ARIAL_UNICODE')))
    p.add_argument('--force',action='store_true');a=p.parse_args()
    try:r=prepare(a.output,a.font_dir,a.pingfang,a.arial_unicode,a.force)
    except (ValueError,OSError) as e:p.exit(2,str(e)+'\n')
    print('字体准备完成：%s 个文件，字符覆盖已检查，字体不入库。' % len(r['fonts']))


if __name__=='__main__':main()
