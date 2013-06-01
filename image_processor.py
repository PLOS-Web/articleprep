#!/usr/bin/env python
# usage: image_processor.py image1 image2 ...

import sys
import subprocess

def convert(images):
    for image in images:
        command = "convert -strip -alpha off -colorspace RGB -depth 8 -trim -bordercolor white -border 1% -units \
        PixelsPerInch -density 300 -resample 300 -resize 2049x2758> -resize 980x2000< +repage -compress lzw "+image+" "+image
        subprocess.call(command.split(), shell = False)
        print command.split()

# ocr step
# convert -gravity north -crop 100%x5% i.tif i_top.tif
# convert -gravity south -crop 100%x5% i.tif i_bottom.tif
# tesseract

# output string
# grep -i (fig|table)
# output += file has unwanted label

if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.exit('usage: image_processor.py image1 image2 ...')
    convert(sys.argv[1:])
