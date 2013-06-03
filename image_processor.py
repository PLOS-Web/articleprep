#!/usr/bin/env python
# usage: image_processor.py image1 image2 ...

import sys
import subprocess

def call(command):
    subprocess.call(command.split(), shell = False)

def convert(image):
    new_image = image.replace('.eps', '.tif')
    call("convert -strip -alpha off -colorspace RGB -depth 8 -trim -bordercolor white -border 1% \
        -units PixelsPerInch -density 300 -resample 300 -resize 2049x2758> -resize 980x2000< \
        +repage -compress lzw " + image + " " + new_image)
    call("convert -gravity north -crop 100%x5% " + new_image + " " + new_image.replace('.tif', '_top.tif'))
    call("convert -gravity south -crop 100%x5% " + new_image + " " + new_image.replace('.tif', '_bottom.tif'))

def prepare(images):
    for image in images:
        convert(image)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.exit('usage: image_processor.py image1 image2 ...')
    prepare(sys.argv[1:])
