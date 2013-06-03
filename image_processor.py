#!/usr/bin/env python
# usage: image_processor.py image1 image2 ...

import sys
import subprocess

def convert(images):
    for image in images:
        new_image = image.replace('.eps', '.tif')
        convert = "convert -strip -alpha off -colorspace RGB -depth 8 -trim -bordercolor white \
        -border 1% -units PixelsPerInch -density 300 -resample 300 -resize 2049x2758> -resize 980x2000< \
        +repage -compress lzw " + image + " " + new_image
        top = "convert -gravity north -crop 100%x5% " + new_image + " " + new_image.replace('.tif', '_top.tif')
        bottom = "convert -gravity south -crop 100%x5% " + new_image + " " + new_image.replace('.tif', '_bottom.tif')
        subprocess.call(convert.split(), shell = False)
        subprocess.call(top.split(), shell = False)
        subprocess.call(bottom.split(), shell = False)

# output string
# grep -i (fig|table)
# output += file has unwanted label

if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.exit('usage: image_processor.py image1 image2 ...')
    convert(sys.argv[1:])
