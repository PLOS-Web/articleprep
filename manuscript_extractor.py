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

def manuscript(guidzip):
    parser = etree.XMLParser(recover = True)
    go = etree.parse(guidzip.replace('zip', 'go.xml'), parser).getroot()
    meta_xml = z.ZipFile(guidzip).extract(metadata(go))
    meta = etree.parse(meta_xml, parser).getroot()
    print list(set(go_files(go)) - set(metadata_files(meta)))    

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1][-4:] != '.zip':
        sys.exit('usage: manuscript_extractor.py guid.zip')
    manuscript(sys.argv[1])
