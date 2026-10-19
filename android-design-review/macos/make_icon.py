"""Create the local app icon using the workbench's existing visual language."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw


target = Path(sys.argv[1])
size = 1024
image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((64, 64, 960, 960), radius=220, fill='#194f43')
draw.rounded_rectangle((240, 176, 784, 848), radius=94, fill='#f7f4eb')
draw.rounded_rectangle((316, 254, 708, 770), radius=44, fill='#194f43')
draw.rounded_rectangle((366, 306, 658, 718), radius=28, fill='#f7f4eb')
draw.ellipse((676, 672, 852, 848), fill='#e66449')
draw.ellipse((728, 724, 800, 796), fill='#ffffff')
image.save(target)
