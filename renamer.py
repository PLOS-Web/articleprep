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

article_links = {}
for si in article.xpath("//supplementary-material"):
    label = normalize(si.xpath("label")[0].text)
    article_links[label] = si.attrib['{http://www.w3.org/1999/xlink}href']

meta_links = {}
for si in meta.xpath("//supplementary-material"):
    label = normalize(si.xpath("label")[0].text)
    meta_href = si.attrib['{http://www.w3.org/1999/xlink}href']
    if label in meta_links:
        print "error: label '"+label+"' is duplicated in the metadata"
        file_list = call(["unzip", "-l", doi_zip, meta_href])
        print >>sys.stderr, "Quote list:", file_list
        print >>sys.stderr, "Quote meta_href:", meta_href
        if meta_href in file_list:
            print "ariesPull cannot rename associated file '"+meta_href+"'"
        else:
            print "associated file '"+meta_href+"' is not included in package"
    else:
        meta_links[label] = meta_href

def call(command):
    call = sp.Popen(command, stdout = sp.PIPE, stderr = sp.PIPE, shell = False)
    output = call.communicate()
    if call.wait() != 0:
        print >>sys.stderr, output[0] or output[1]
    return output[0]

si_files = call(["unzip", "-l", si_zip])
for fig in meta.xpath("//fig"):
    for graphic in fig.xpath("graphic"):
        fig_file = graphic.attrib['{http://www.w3.org/1999/xlink}href']
    if fig_file in si_files:
        label = fig.xpath("label")[0].text
        print >>sys.stderr, "FIG_LABEL: " + label
        print >>sys.stderr, "FIG_FILE: " + fig_file
        if re.search(r'igure \d+', label):
            num = re.sub(r'\D*(\d+)\D*', r'\1', label)
            print >>sys.stderr, "FIG_NUM: " + num
            new_name = doi + ".g" + str(num).zfill(3) + ".tif"
            print >>sys.stderr, "NEW_NAME: " + new_name
            unzip = ["unzip", "-o", si_zip, fig_file, "-d", destination]
            print >>sys.stderr, "UNZIP: " + ' '.join(unzip) + "\n"
            call(unzip)
            if fig_file != fig_file.lower():
                call(["mv", destination+'/'+fig_file, destination+'/'+fig_file.lower()])
            #print >>sys.stderr, call(["/var/local/scripts/production/articleprep/articleprep/image_processor.py", destination+'/'+fig_file.lower()])
            call(["mv", destination+'/'+fig_file.lower().replace('.eps','.tif'), destination+'/'+new_name])
            call(["zip", "-mj", destination+'/'+doi_zip, destination+'/'+new_name])

for key in meta_links:
    print >>sys.stderr, "Aries name:", meta_links[key]
    unzip_name = meta_links[key]  # TODO: lines 749-750 of ariesPullMerops
    print >>sys.stderr, "UNZIP NAME:", meta_links[key]
    if key in article_links or "Striking Image" in key:
        unzip = call(["unzip", "-o", si_zip, unzip_name, "-d", destination])
        print >>sys.stderr, "UNZIP SI:", unzip
        if "inflating" in unzip or "extracting" in unzip:
            if re.search(r'\.s\d{3}$', article_links[key]):
                si_ext = meta_links[key].split('.')[-1]
                article_links[key] += '.' + si_ext.lower()
            if "Striking Image" in key:
                if '.tif' in meta_links[key]:
                    print >>sys.stderr, "MOVE:", call(["mv", destination+'/'+meta_links[key], destination+'/'+doi+'.strk.tif'])
                    call(["zip", "-j", destination+'/'+doi_zip, destination+'/'+doi+'.strk.tif'])
                else:
                    print >>sys.stderr, "striking image is not tif"
                continue
            else:
                call(["mv", destination+'/'+meta_links[key], destination+'/'+article_links[key]])
                call(["zip", "-mj", destination+'/'+doi_zip, destination+'/'+article_links[key]])
        else:
            print >>sys.stderr, "error: SI file '"+meta_links[key]+"' with label '"+key+"' is cited in metadata, but not included in package"
    else:
        print >>sys.stderr, "error: no match for label '"+key+"' in article XML; ariesPull could not rename file '"+meta_links[key]+"'"
        unzip = call(["unzip", "-o", si_zip, meta_links[key], "-d", destination])
        if meta_links[key] in unzip:
            print >>sys.stderr, "error: SI file '"+meta_links[key]+"' with label '"+key+"' is cited in metadata, but not included in package"
        else:
            call(["zip", "-mj", destination+'/'+doi_zip, destination+'/'+meta_links[key]])

call(["rm", "-f", destination+'/'+si_zip])
