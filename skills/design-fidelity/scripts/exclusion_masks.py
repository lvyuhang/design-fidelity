"""Frozen source-space exclusion shapes; foreground protection always wins."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def build_keep_mask(canvas, scale, exclusions, protections=()):
    size = tuple(round(v * scale) for v in canvas)
    if scale <= 0 or min(size) <= 0:
        raise ValueError("Invalid mask canvas/scale")
    excluded = np.zeros((size[1], size[0]), dtype=bool)

    def raster(spec):
        kind = spec.get('shape', 'rect')
        im = Image.new('L', size)
        draw = ImageDraw.Draw(im)
        if kind == 'polygon':
            points = spec['points']
            if len(points) < 3 or any(len(v) != 2 for v in points):
                raise ValueError('Invalid mask polygon')
            if any(not math.isfinite(v) for pt in points for v in pt):
                raise ValueError('Nonfinite mask polygon')
            if any(not (0 <= x <= canvas[0] and 0 <= y <= canvas[1]) for x,y in points):
                raise ValueError('Mask polygon outside canvas')
            draw.polygon([(x*scale,y*scale) for x,y in points], fill=255)
        elif kind in ('rect', 'ellipse'):
            x,y,w,h = spec['rect']
            if not all(math.isfinite(v) for v in (x,y,w,h)) or x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > canvas[0] or y+h > canvas[1]:
                raise ValueError('Invalid mask bounds')
            box = (round(x*scale),round(y*scale),round((x+w)*scale)-1,round((y+h)*scale)-1)
            if kind == 'rect': draw.rectangle(box, fill=255)
            else: draw.ellipse(box, fill=255)
        else:
            raise ValueError('Unknown mask shape: ' + str(kind))
        inset = spec.get('inset', 0)
        if not math.isfinite(inset) or inset < 0:
            raise ValueError('Invalid mask inset')
        radius = round(inset*scale)
        if radius: im = im.filter(ImageFilter.MinFilter(2*radius+1))
        return np.asarray(im) > 0

    for spec in exclusions:
        if not spec.get('reason', '').strip():
            raise ValueError('Exclusion mask needs a reason')
        excluded |= raster(spec)
    # Apply after union: a second exclusion must never hide protected foreground.
    for spec in protections:
        if not spec.get('reason', '').strip():
            raise ValueError('Mask protection needs a reason')
        excluded &= ~raster(spec)
    return ~excluded
