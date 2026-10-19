"""Diagnostic comparison, never an automatic design-acceptance gate."""
import io
import math
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MAX_PIXELS = 24_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def read_image(data):
    try:
        im = Image.open(io.BytesIO(data))
        if im.format not in ('PNG', 'JPEG') or im.width * im.height > MAX_PIXELS:
            raise ValueError('请使用不超过 2400 万像素的 PNG 或 JPEG。')
        im.load()
        return im.convert('RGB')
    except (OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('无法读取图片，请使用原始 PNG 或 JPEG 截图。')


def png_bytes(im):
    output = io.BytesIO()
    im.save(output, format='PNG')
    return output.getvalue()


def finite_number(value, minimum, maximum, name):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(name + '必须为数字')
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(name + '超出允许范围')
    return number


def validate_calibration(calibration):
    return {'scale_percent': finite_number(calibration.get('scale_percent', 100), 20, 500, '缩放'),
            'offset_x': finite_number(calibration.get('offset_x', 0), -4000, 4000, '水平偏移'),
            'offset_y': finite_number(calibration.get('offset_y', 0), -4000, 4000, '垂直偏移'),
            'confirmed': calibration.get('confirmed') is True}


def normalize(candidate, reference_size, canvas, calibration):
    rw, rh = reference_size
    cw, ch = canvas['width'], canvas['height']
    sx, sy = rw / cw, rh / ch
    if abs(sx / sy - 1) > .002:
        raise ValueError('参考图与设计画布比例不一致，请提供完整且未拉伸的原稿。')
    cal = validate_calibration(calibration)
    scale = cw / candidate.width * cal['scale_percent'] / 100
    inverse = (1 / (sx * scale), 0, -cal['offset_x'] / scale,
               0, 1 / (sy * scale), -cal['offset_y'] / scale)
    normalized = candidate.transform((rw, rh), Image.Transform.AFFINE, inverse,
                                     resample=Image.Resampling.BILINEAR, fillcolor=(242, 244, 247))
    coverage = Image.new('L', candidate.size, 255).transform(
        (rw, rh), Image.Transform.AFFINE, inverse, resample=Image.Resampling.NEAREST, fillcolor=0)
    return normalized, np.asarray(coverage) > 0


def validate_rect(rect, canvas):
    x = finite_number(rect.get('x'), 0, canvas['width'], '区域 X')
    y = finite_number(rect.get('y'), 0, canvas['height'], '区域 Y')
    w = finite_number(rect.get('width'), .1, canvas['width'], '区域宽度')
    h = finite_number(rect.get('height'), .1, canvas['height'], '区域高度')
    if x + w > canvas['width'] + .1 or y + h > canvas['height'] + .1:
        raise ValueError('标注区域超出设计画布')
    return {'x': x, 'y': y, 'width': min(w, canvas['width']-x), 'height': min(h, canvas['height']-y)}


def node_matches(rect, nodes):
    matches = []
    for node in nodes:
        b = node.get('bounds') or {}
        if not all(k in b for k in ('x', 'y', 'width', 'height')) or not b['width'] or not b['height']:
            continue
        if node.get('effective_source_visible') is False or node.get('node_type') == 'artboard-group':
            continue
        area = max(0, min(rect['x']+rect['width'], b['x']+b['width']) - max(rect['x'], b['x'])) * max(
            0, min(rect['y']+rect['height'], b['y']+b['height']) - max(rect['y'], b['y']))
        if area > 0:
            score = area / max(rect['width']*rect['height'], b['width']*b['height'])
            matches.append((score, {'id': node['node_id'], 'label': str(node.get('text') or node.get('name') or node['node_id'])[:80], 'bounds': b}))
    return [n for _, n in sorted(matches, key=lambda v: v[0], reverse=True)[:4]]


def compare(reference, candidate, canvas, calibration, threshold=28, exclusions=None, nodes=None):
    threshold = finite_number(threshold, 1, 255, '差异阈值')
    normalized, coverage = normalize(candidate, reference.size, canvas, calibration)
    sx, sy = reference.width / canvas['width'], reference.height / canvas['height']
    excluded = np.zeros_like(coverage)
    for item in exclusions or []:
        if not str(item.get('reason', '')).strip():
            raise ValueError('每个排除区域都必须填写原因')
        r = validate_rect(item['rect'], canvas)
        excluded[int(r['y']*sy):math.ceil((r['y']+r['height'])*sy), int(r['x']*sx):math.ceil((r['x']+r['width'])*sx)] = True
    eligible = coverage & ~excluded
    if eligible.sum() == 0:
        raise ValueError('当前对齐或排除设置没有留下可比较区域')
    delta = np.max(np.abs(np.asarray(reference, dtype=np.int16) - np.asarray(normalized, dtype=np.int16)), axis=2)
    changed = (delta > threshold) & eligible
    # Coarse tiles group diagnostic candidates; a bounding box is not a measured widget boundary.
    tile = max(4, round(sx * 8))
    gh, gw = math.ceil(reference.height/tile), math.ceil(reference.width/tile)
    active = np.zeros((gh, gw), dtype=bool)
    for y in range(gh):
        for x in range(gw):
            part = changed[y*tile:(y+1)*tile, x*tile:(x+1)*tile]
            active[y, x] = part.sum() >= max(2, part.size * .07)
    active = np.asarray(Image.fromarray(active.astype('uint8')*255).filter(ImageFilter.MaxFilter(3))) > 0
    seen = set()
    regions = []
    for y, x in zip(*np.where(active)):
        if (y, x) in seen:
            continue
        queue, cells = deque([(y, x)]), []
        seen.add((y, x))
        while queue:
            cy, cx = queue.popleft(); cells.append((cy, cx))
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = cy+dy, cx+dx
                if 0 <= ny < gh and 0 <= nx < gw and active[ny,nx] and (ny,nx) not in seen:
                    seen.add((ny,nx)); queue.append((ny,nx))
        ys, xs = zip(*cells)
        x0, y0 = min(xs)*tile, min(ys)*tile
        x1, y1 = min((max(xs)+1)*tile, reference.width), min((max(ys)+1)*tile, reference.height)
        pixels = int(changed[y0:y1,x0:x1].sum())
        if pixels < max(8, sx*sy*3):
            continue
        rect = {'x': round(x0/sx,2), 'y': round(y0/sy,2), 'width': round((x1-x0)/sx,2), 'height': round((y1-y0)/sy,2)}
        regions.append({'rect': rect, 'changed_pixels': pixels, 'nodes': node_matches(rect, nodes or [])})
    regions.sort(key=lambda r: r['changed_pixels'], reverse=True)
    for index, region in enumerate(regions[:40]):
        region['id'] = 'suggestion-' + str(index+1)
        region['title'] = '检查「' + region['nodes'][0]['label'] + '」附近差异' if region['nodes'] else '检查局部视觉差异'
    heat = np.asarray(normalized).astype(float)*.36 + 255*.64
    heat[changed] = np.array([241, 88, 65])
    heat[~eligible] = np.array([200, 206, 214])
    stats = {'status': 'DIAGNOSTIC_ONLY', 'threshold': threshold, 'region_count': len(regions),
             'returned_regions': min(40,len(regions)), 'changed_pixels': int(changed.sum()),
             'compared_pixels': int(eligible.sum()), 'coverage_fraction': float(coverage.mean()),
             'excluded_fraction': float(excluded.mean()), 'suggestions': regions[:40]}
    return normalized, Image.fromarray(heat.astype('uint8')), stats


def numbered_comparison(reference, normalized, issues, canvas):
    scale = min(1, 1100/reference.width)
    w, h = round(reference.width*scale), round(reference.height*scale)
    image = Image.new('RGB', (w*2+24,h+42), '#f1f3f5')
    image.paste(reference.resize((w,h)), (0,42)); image.paste(normalized.resize((w,h)), (w+24,42))
    draw = ImageDraw.Draw(image)
    draw.text((12,14),'DESIGN',fill='#42546a'); draw.text((w+36,14),'CAPTURE / ALIGNED',fill='#42546a')
    for i, issue in enumerate(issues,1):
        r=issue['rect']
        for offset in (0,w+24):
            x=offset+r['x']/canvas['width']*w; y=42+r['y']/canvas['height']*h
            right=x+r['width']/canvas['width']*w; bottom=y+r['height']/canvas['height']*h
            draw.rectangle((x,y,right,bottom),outline='#e74d3d',width=3)
            draw.rectangle((x,max(42,y-20),x+27,max(42,y-20)+20),fill='#e74d3d')
            draw.text((x+6,max(42,y-20)+3),str(i),fill='white')
    return image


def numbered_capture(reference, candidate, issues, canvas, calibration):
    """Export the full capture, including image-coordinate pins below the design edge."""
    w = min(1100, reference.width)
    rh = round(reference.height*w/reference.width)
    ch = round(candidate.height*w/candidate.width)
    image = Image.new('RGB', (w*2+24, max(rh,ch)+42), '#f1f3f5')
    image.paste(reference.resize((w,rh)), (0,42))
    image.paste(candidate.resize((w,ch)), (w+24,42))
    draw = ImageDraw.Draw(image)
    draw.text((12,14),'DESIGN',fill='#42546a')
    draw.text((w+36,14),'CAPTURE / ORIGINAL',fill='#42546a')
    scale = canvas['width']*calibration.get('scale_percent',100)/100/candidate.width
    for index,issue in enumerate(issues,1):
        r=issue['rect']
        if issue.get('coordinate_space')=='image':
            x,y=r['x'],r['y']; width,height=r['width'],r['height']
        else:
            x=(r['x']-calibration.get('offset_x',0))/scale
            y=(r['y']-calibration.get('offset_y',0))/scale
            width,height=r['width']/scale,r['height']/scale
        x=w+24+x*w/candidate.width; y=42+y*w/candidate.width
        if issue.get('annotation_type')=='point':
            draw.ellipse((x-13,y-13,x+13,y+13),fill='#e74d3d',outline='white',width=2)
            draw.text((x-3*len(str(index)),y-6),str(index),fill='white')
        else:
            draw.rectangle((x,y,x+width*w/candidate.width,y+height*w/candidate.width),outline='#e74d3d',width=3)
            draw.rectangle((x,max(42,y-20),x+27,max(42,y-20)+20),fill='#e74d3d')
            draw.text((x+6,max(42,y-20)+3),str(index),fill='white')
    return image
