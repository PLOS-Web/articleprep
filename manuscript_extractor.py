#!/usr/bin/env python
# usage: manuscript_extractor.py guid.zip

import sys
import zipfile as z
import lxml.etree as etree

def go_files(root):
    return [f.attrib['name'] for f in root.xpath("//filegroup/file")]

def metadata(root):
    return root.xpath("//metadata-file")[0].attrib['name']

def metadata_files(root):
    return [f.attrib['{http://www.w3.org/1999/xlink}href'] for f in root.xpath("//fig/graphic") + root.xpath("//supplementary-material")]

def doi(guidzip):
    go = etree.parse(guidzip.replace('zip', 'go.xml')).getroot()
    print go.xpath("//parameter[@name='DOI']")[0].attrib['value']

def manuscript(guidzip):
    go = etree.parse(guidzip.replace('zip', 'go.xml')).getroot()
    meta_xml = z.ZipFile(guidzip).open(metadata(go))
    meta = etree.parse(meta_xml).getroot()
    print list(set(go_files(go)) - set(metadata_files(meta)))[0]

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1][-4:] != '.zip':
        sys.exit('usage: manuscript_extractor.py guid.zip')
    manuscript(sys.argv[1])
