"""Screen test presets and source-backed hardware references.
Physical resolution is never treated as evidence of OEM Android logical density.
"""
import copy

WIDTH_GROUPS = [
    {'id':'small','name':'小屏','range':'320–360 dp','hint':'检查窄屏换行、按钮挤压','widths':[320,360]},
    {'id':'medium','name':'中屏','range':'375–393 dp','hint':'检查日常手机布局与字号','widths':[375,384,393]},
    {'id':'large','name':'大屏','range':'400–432 dp','hint':'检查留白、列表密度与长文本','widths':[400,411,432]},
    {'id':'wide','name':'超宽手机','range':'480 dp','hint':'检查更宽显示设置下的布局','widths':[480]},
    {'id':'fold','name':'折叠内屏','range':'600–720 dp','hint':'检查展开后的宽布局；不模拟折叠动作','widths':[600,720]},
    {'id':'tablet','name':'平板','range':'800–960 dp','hint':'检查大屏拉伸与分栏','widths':[800,840,960]},
]
PHONE_WIDTHS = [320,360,375,384,393,400,411,432,480]
MODEL_GROUPS = [
    {'id':'all','name':'全部'}, {'id':'small','name':'小屏手机 · <6.5″'},
    {'id':'medium','name':'中屏手机 · 6.5–6.7″'}, {'id':'large','name':'大屏手机 · >6.7″'},
    {'id':'fold','name':'折叠屏'}, {'id':'tablet','name':'平板'},
]

def hardware(key, name, brand, width, height, inches, source, form='phone'):
    group=form if form!='phone' else ('small' if inches<6.5 else 'medium' if inches<=6.7 else 'large')
    return dict(id=key,name=name,brand=brand,width=width,height=height,inches=inches,source=source,
                group=group,form=form,verified_at='2026-10-15',density_status='unknown',
                test_widths=PHONE_WIDTHS if form=='phone' else [600,720,800,840,960],
                default_test_width=393 if form=='phone' else 720 if form=='fold' else 840)

MODELS = [
    hardware('xiaomi-17','小米 17','小米 / REDMI',1220,2656,6.3,'https://www.mi.com/global/product/xiaomi-17/specs/'),
    hardware('xiaomi-15','小米 15','小米 / REDMI',1200,2670,6.36,'https://www.mi.com/tw/product/xiaomi-15/specs/'),
    hardware('xiaomi-15-ultra','小米 15 Ultra','小米 / REDMI',1440,3200,6.73,'https://www.mi.com/ae-en/product/xiaomi-15-ultra/specs/'),
    hardware('redmi-note-14-pro','REDMI Note 14 Pro 5G','小米 / REDMI',1220,2712,6.67,'https://www.mi.co.id/id/product/redmi-note-14-pro-5g/specs/'),
    hardware('vivo-x300','vivo X300','vivo',1216,2640,6.31,'https://m.vivo.com.cn/vivo/param/x300'),
    hardware('vivo-x200','vivo X200','vivo',1260,2800,6.67,'https://m.vivo.com.cn/vivo/param/x200'),
    hardware('oppo-find-x9','OPPO Find X9','OPPO / 一加',1256,2760,6.59,'https://www.oppo.com/cn/smartphones/series-find-x/find-x9/specs/'),
    hardware('oppo-find-x8','OPPO Find X8','OPPO / 一加',1256,2760,6.59,'https://www.oppo.com/cn/smartphones/series-find-x/find-x8/specs/'),
    hardware('oneplus-13','一加 13','OPPO / 一加',1440,3168,6.82,'https://www.oneplus.com/cn/13/specs'),
    hardware('honor-magic7-pro','荣耀 Magic7 Pro','荣耀',1280,2800,6.8,'https://www.honor.com/sa-en/phones/honor-magic7-pro/spec/'),
    hardware('galaxy-s25','Samsung Galaxy S25','三星',1080,2340,6.2,'https://www.samsung.com/uk/smartphones/galaxy-s/galaxy-s25-navy-128gb-certified-re-newed-sm5s931bdbdeub/'),
    hardware('galaxy-s25-ultra','Samsung Galaxy S25 Ultra','三星',1440,3120,6.9,'https://www.samsung.com.cn/business/smartphones/galaxy-s/galaxy-s25-ultra-sm-s9380zsgchc/'),
    hardware('galaxy-a56','Samsung Galaxy A56 5G','三星',1080,2340,6.7,'https://www.samsung.com/uk/smartphones/galaxy-a/galaxy-a56-5g-awesome-olive-256gb-sm-a566bzgceub/'),
    hardware('oppo-find-n5-inner','OPPO Find N5 · 内屏','OPPO / 一加',2248,2480,8.12,'https://www.oppo.com/cn/smartphones/series-find-n/find-n5/specs/','fold'),
    hardware('galaxy-fold6-inner','Samsung Z Fold6 · 内屏','三星',1856,2160,7.6,'https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2025_Half_Interim_Report.pdf','fold'),
    hardware('xiaomi-pad7','小米 Pad 7','小米 / REDMI',2136,3200,11.2,'https://www.mi.com/ae-en/product/xiaomi-pad-7/specs/','tablet'),
]

def width_presets():
    profiles=[]
    for group in WIDTH_GROUPS:
        for width in group['widths']:
            # Exact dp at 2x, preserving representative phone / unfolded / tablet proportions.
            height=round(width*(20/9 if width<600 else 1.12 if group['id']=='fold' else 1.5))
            profiles.append(dict(id=f'width-{width}',name=group['name'],width=width*2,height=height*2,
                                 density=320,models=[],group=group['id'],verification='适配测试档位',
                                 condition=group['hint'],width_dp=width))
    return profiles

def model_profile(model_id, target_width):
    model=next((m for m in MODELS if m['id']==model_id),None)
    if not model: raise ValueError('未收录此机型，请重新选择。')
    if isinstance(target_width,bool) or target_width not in model['test_widths']:
        raise ValueError('请选择有效的测试宽度。')
    density=round(model['width']*160/target_width)
    return dict(id=f"model-{model_id}-{int(target_width)}",name=model['name'],models=[model['name']],
                width=model['width'],height=model['height'],density=density,
                width_dp=round(model['width']*160/density,2),requested_width_dp=target_width,
                model_id=model_id,source=model['source'],hardware_reference=copy.deepcopy(model),
                verification='官方屏幕参数 · 测试密度',density_status='test_override',
                condition='测试宽度由你选择，不代表该机型出厂 dp；厂商系统、挖孔和折叠动作不在模拟范围内。')
