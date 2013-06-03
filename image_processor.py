#!/usr/bin/env python
# usage: image_processor.py image1 image2 ...

import sys
import subprocess

def call(command):
    call = subprocess.Popen(command.split(), stdout = subprocess.PIPE, shell = False)
    return call.communicate()[0]

def convert(image, new_image, top, bottom):
    call("convert -strip -alpha off -colorspace RGB -depth 8 -trim -bordercolor white -border 1% \
        -units PixelsPerInch -density 300 -resample 300 -resize 2049x2758> -resize 980x2000< \
        +repage -compress lzw " + image + " " + new_image)
    call("convert -gravity north -crop 100%x5% " + new_image + " " + top)
    call("convert -gravity south -crop 100%x5% " + new_image + " " + bottom)

def ocr(new_image, top, bottom):
    call("tesseract " + new_image + " " + new_image)
    call("tesseract " + top + " " + top)
    call("tesseract " + bottom + " " + bottom)

def grep(new_image, top, bottom):
    labels = call("grep -iE (fig|table) " + new_image + ".txt " + top + ".txt " + bottom + ".txt")
    for label in labels.split()[:1]:
        print "warning: " + label[:label.index(':')] + " contains label: " + label[label.index(':')+1:]

def prepare(images):
    for image in images:
        new_image = image.replace('.eps', '.tif')
        top = new_image.replace('.tif', '_top.tif')
        bottom = new_image.replace('.tif', '_bottom.tif')

        convert(image, new_image, top, bottom)
        ocr(new_image, top, bottom)
        grep(new_image, top, bottom)        

if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.exit('usage: image_processor.py image1 image2 ...')
    prepare(sys.argv[1:])
