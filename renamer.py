#!/usr/bin/env python
# --DRAFT-- usage: renamer.py doi metadata.xml destination si.zip doi.zip

import sys
import subprocess as sp
import lxml.etree as etree
import re

doi, meta, destination, si_zip, doi_zip = sys.argv[1:]
parser = etree.XMLParser(recover = True)
meta = etree.parse(meta, parser)
hrefs = {}  # TODO: parse hrefs from doi.xml

def call(command):
	print >>sys.stderr, ' '.join(command)
	call = sp.Popen(command, stdout = sp.PIPE, stderr = sp.PIPE, shell = False)
	output = call.communicate()
	if call.wait() != 0:
		print >>sys.stderr, output[0] or output[1]
	return output[0]

for fig in meta.xpath("//fig"):
	label = fig.xpath("label")[0].text
	print >>sys.stderr, "FIG_LABEL: " + label
	for graphic in fig.xpath("graphic"):
		fig_file = graphic.attrib['{http://www.w3.org/1999/xlink}href']
	print >>sys.stderr, "FIG_FILE: " + fig_file
	if re.search(r'igure \d+', label):
		num = re.sub(r'\D*(\d+)', r'\1', label)
		print >>sys.stderr, "FIG_NUM: " + num
		new_name = doi + ".g" + str(num).zfill(3)
		print >>sys.stderr, "NEW_NAME: " + new_name
		call(["unzip", "-o", si_zip, fig_file, "-d", destination])
		call(["mv", destination+'/'+fig_file, destination+'/'+fig_file.lower()])
		print >>sys.stderr, call(["/var/local/scripts/production/articleprep/articleprep/image_processor.py", destination+'/'+fig_file])
		call(["mv", destination+'/'+fig_file.replace('.eps','.tif'), destination+'/'+new_name])
		call(["zip", "-mj", destination+'/'+doi_zip, destination+'/'+new_name])
		call(["zip", "-d", destination+'/'+doi_zip, fig_file])

aries_names = {}
for supp in meta.xpath("//supplementary-material"):
	meta_href = supp.attrib['{http://www.w3.org/1999/xlink}href']
	label = supp.xpath("label")[0].text.strip()
	if label in aries_names:
		print "error: label "+label+" is duplicated in the metadata"
		file_list = call(["unzip", "-l", doi_zip, meta_href])
		print >>sys.stderr, "Quote list:", file_list
		print >>sys.stderr, "Quote meta_href:", meta_href
		if meta_href in file_list:
			print "ariesPull cannot rename associated file "+meta_href
		else:
			print "associated file "+meta_href+" is not included in package"
	else:
		aries_names[label] = meta_href

for key in aries_names:
	print >>sys.stderr, "Aries name:", aries_names[key]
	unzip_name = aries_names[key]  # TODO: lines 749-750 of ariesPullMerops
	print >>sys.stderr, "UNZIP NAME:", aries_names[key]
	if key in hrefs or "Striking Image" in key:
		unzip = call(["unzip", "-o", si_zip, unzip_name, "-d", destination])
		print >>sys.stderr, "UNZIP SI:", unzip
		if "inflating" in unzip or "extracting" in unzip:
			if re.search(r'\.s\d{3}$', hrefs[key]):
				si_ext = aries_names[key].split('.')[-1]
				hrefs[key] += '.' + si_ext.lower()
			if "Striking Image" in key:
				if '.tif' in aries_names[key]:
					print >>sys.stderr, "MOVE:", call(["mv", destination+'/'+aries_names[key], destination+'/'+doi+'.strk.tif'])
					call(["zip", "-j", destination+'/'+doi_zip, destination+'/'+doi+'.strk.tif'])
				else:
					print "striking image is not tif"
				continue
			else:
				call(["mv", destination+'/'+aries_names[key], destination+'/'+hrefs[key]])
				call(["zip", "-mj", destination+'/'+doi_zip, destination+'/'+hrefs[key]])
		else:
			print "error: SI file", aries_names[key], "with label", key, "is cited in metadata, but not included in package"
	else:
		print "error: no match for label", key, "in article XML; ariesPull could not rename file", aries_names[key]
		unzip = call(["unzip", "-o", si_zip, aries_names[key], "-d", destination])
		if aries_names[key] in unzip:
			print "error: SI file", aries_names[key], "with label", key, "is cited in metadata, but not included in package"
		else:
			call(["zip", "-mj", destination+'/'+doi_zip, destination+'/'+aries_names[key]])

call(["rm", "-f", destination+'/'+si_zip])
