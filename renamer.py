#!/usr/bin/env python
# usage: renamer.py doi metadata.xml article.xml destination si.zip doi.zip

import sys
import subprocess as sp
import lxml.etree as etree
import string
import re

doi, meta, article, destination, si_zip, doi_zip = sys.argv[1:]
parser = etree.XMLParser(recover = True)
meta = etree.parse(meta, parser)
article = etree.parse(article, parser)

def normalize(s):
    return s.strip().replace(' ','').lower().translate(None, string.punctuation)

def prints(s):
    print >>sys.stderr, s
    print s

def call(command):
    call = sp.Popen(command, stdout = sp.PIPE, stderr = sp.PIPE, shell = False)
    output = call.communicate()
    if call.wait() != 0:
        print >>sys.stderr, output[0] or output[1]
    return output[0]

article_links = {}
for si in article.xpath("//supplementary-material"):
    label = normalize(si.xpath("label")[0].text)
    article_links[label] = si.attrib['{http://www.w3.org/1999/xlink}href']

meta_links = {}
strk_img = {}
for si in meta.xpath("//supplementary-material"):
    label = normalize(si.xpath("label")[0].text)
    link = si.attrib['{http://www.w3.org/1999/xlink}href']
    if "Striking Image" in label:
         strk_img[label] = link
    elif label in meta_links:
        prints("error: label '"+label+"' is duplicated in the metadata")
        file_list = call(["unzip", "-l", doi_zip, link])
        print >>sys.stderr, "Quote list:", file_list
        print >>sys.stderr, "Quote link:", link
        if link in file_list:
            prints("ariesPull cannot rename associated file '"+link+"'")
        else:
            prints("associated file '"+link+"' is not included in package")
    else:
        meta_links[label] = link

export = call(["unzip", "-l", si_zip])
for fig in meta.xpath("//fig"):
    for graphic in fig.xpath("graphic"):
        fig_file = graphic.attrib['{http://www.w3.org/1999/xlink}href']
    if fig_file in export:
        label = fig.xpath("label")[0].text
        print >>sys.stderr, "FIG_LABEL: " + label
        print >>sys.stderr, "FIG_FILE: " + fig_file
        if re.search(r'igure \d+', label):
            num = re.sub(r'\D*(\d+)\D*', r'\1', label)
            new_name = doi + ".g" + str(num).zfill(3) + ".tif"
            print >>sys.stderr, "NEW_NAME: " + new_name
            print >>sys.stderr, "UNZIP: ", call(["unzip", "-o", si_zip, fig_file, "-d", destination])
            if fig_file != fig_file.lower():
                call(["mv", destination+'/'+fig_file, destination+'/'+fig_file.lower()])
            #prints(call(["/var/local/scripts/production/articleprep/articleprep/image_processor.py", destination+'/'+fig_file.lower()]))
            call(["mv", destination+'/'+fig_file.lower().replace('.eps','.tif'), destination+'/'+new_name])
            call(["zip", "-mj", destination+'/'+doi_zip, destination+'/'+new_name])

for label in strk_img:
    unzip = call(["unzip", "-o", si_zip, strk_img[label], "-d", destination])
    print >>sys.stderr, "UNZIP SI:", unzip
    if "inflating" in unzip or "extracting" in unzip:
        if '.tif' in strk_img[label]:
            print >>sys.stderr, "MOVE:", call(["mv", destination+'/'+strk_img[label], destination+'/'+doi+'.strk.tif'])
            call(["zip", "-j", destination+'/'+doi_zip, destination+'/'+doi+'.strk.tif'])
        else:
            prints("striking image is not tif")
    else:
        prints("error: SI file '"+strk_img[label]+"' with label '"+label+"' is cited in metadata, but not included in package")

for label in set(article_links).intersection(set(meta_links)):
    print >>sys.stderr, "Aries name:", meta_links[label]
    unzip = call(["unzip", "-o", si_zip, meta_links[label], "-d", destination])
    print >>sys.stderr, "UNZIP SI:", unzip
    if "inflating" in unzip or "extracting" in unzip:
        if re.search(r'\.s\d{3}$', article_links[label]):
            si_ext = meta_links[label].split('.')[-1]
            article_links[label] += '.' + si_ext.lower()
        else:
            call(["mv", destination+'/'+meta_links[label], destination+'/'+article_links[label]])
            call(["zip", "-mj", destination+'/'+doi_zip, destination+'/'+article_links[label]])
    else:
        prints("error: SI file '"+meta_links[label]+"' with label '"+label+"' is cited in article XML, but not included in package")

for label in set(article_links)-set(meta_links):
    prints("error: article XML cites '"+label+"', metadata does not; should be '"+article_links[label]+"'")

for label in set(meta_links)-set(article_links):
    prints("warning: metadata cites '"+label+"', article XML does not; ariesPull could not rename file '"+meta_links[label]+"'")

call(["rm", "-f", destination+'/'+si_zip])
