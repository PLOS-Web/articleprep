#!/usr/bin/env python
# usage: metadata_builder.py metadata.xml before.xml after.xml

import sys
import re
import copy
import lxml.etree as etree

constructors = []

def get_journal(m):
	return m.xpath("//journal-id[@journal-id-type='publisher']")[0].text

def get_issn(m):
	return m.xpath("//issn[@pub-type='ppub']")[0].text

def add_journal_meta(root, journal, issn):
	j = {'plosbiol':"PLoS Biol", 'plosmed':"PLoS Med", 'ploscomp':"PLoS Comput Biol", 'plosgen':"PLoS Genet",
		 'plospath':"PLoS Pathog", 'plosone':"PLoS ONE", 'plosntds':"PLoS Negl Trop Dis"}
	front = root.xpath("//front")[0]
	for node in front.xpath("journal-meta"):
		front.remove(node)
	front.insert(0, etree.fromstring("""<journal-meta>
	<journal-id journal-id-type="nlm-ta">%s</journal-id>
	<journal-id journal-id-type="publisher-id">plos</journal-id>
	<journal-id journal-id-type="pmc">%s</journal-id>
	<journal-title-group><journal-title>%s</journal-title></journal-title-group>
	<issn pub-type="epub">%s</issn>
	<publisher><publisher-name>Public Library of Science</publisher-name>
	<publisher-loc>San Francisco, USA</publisher-loc></publisher>
	</journal-meta>""" % (j[journal], journal, j[journal], issn)))
	return root
constructors.append([add_journal_meta, [get_journal, get_issn]])

def get_ms_number(m):
	return m.xpath("//article-id[@pub-id-type='manuscript']")[0].text

def add_ms_number(root, ms):
	article_meta = root.xpath("//article-meta")[0]
	for node in article_meta.xpath("article-id[@pub-id-type='publisher-id']"):
		article_meta.remove(node)
	article_meta.insert(0, etree.fromstring("""<article-id pub-id-type='publisher-id'>%s</article-id>""" % ms))
	return root
constructors.append([add_ms_number, [get_ms_number]])

def get_article_doi(m):
	return m.xpath("//article-id[@pub-id-type='doi']")[0].text

def add_article_doi(root, doi):
	article_meta = root.xpath("//article-meta")[0]
	for node in article_meta.xpath("article-id[@pub-id-type='doi']"):
		article_meta.remove(node)
	article_meta.insert(1, etree.fromstring("""<article-id pub-id-type="doi">%s</article-id>""" % doi))
	return root
constructors.append([add_article_doi, [get_article_doi]])

def get_article_type(m):
	return m.xpath("//article-categories//subj-group[@subj-group-type='Article Type']/subject")[0].text

def add_article_type(root, article_type):
	article_meta = root.xpath("//article-meta")[0]
	for node in article_meta.xpath("article-categories"):
		article_meta.remove(node)
	article_meta.insert(2, etree.fromstring("""<article-categories><subj-group subj-group-type="heading">
	<subject>%s</subject></subj-group></article-categories>""" % article_type))
	return root
constructors.append([add_article_type, [get_article_type]])

def get_conflict(m):
	return m.xpath("//custom-meta[@id='conflict']/meta-value")[0].text

def add_conflict(root, conflict):
	author_notes = root.xpath("//author-notes")[0]
	for node in author_notes.xpath("fn[@fn-type='conflict']"):
		author_notes.remove(node)
	author_notes.insert(1, etree.fromstring("""<fn fn-type="conflict"><p>%s</p></fn>""" % conflict))
	return root
constructors.append([add_conflict, [get_conflict]])

def get_contrib(m):
	result = ''
	for au in m.xpath("//meta-name[contains(text(),'Author Contributions')]"):
		result += re.sub(r'.*Author Contributions: ([^<]*).*', r'\1', au.text.replace('\n','')).capitalize() \
			+ ': ' + au.getnext().text + '. '
	return result

def add_contrib(root, contrib):
	author_notes = root.xpath("//author-notes")[0]
	for node in author_notes.xpath("fn[@fn-type='con']"):
		author_notes.remove(node)
	author_notes.insert(2, etree.fromstring("""<fn fn-type="con"><p>%s</p></fn>""" % contrib))
	return root
constructors.append([add_contrib, [get_contrib]])

def get_author_notes_index(root):
	am = root.xpath("//article-meta")[0]
	author_notes = am.xpath("author-notes")[0]
	return am.index(author_notes)

def get_collection(m):
	return str(int(m.xpath("//pub-date[@pub-type='epub']/year")[0].text))

def add_collection(root, collection):
	article_meta = root.xpath("//article-meta")[0]
	for node in article_meta.xpath("pub-date[@pub-type='collection']"):
		article_meta.remove(node)
	article_meta.insert(get_author_notes_index(root) + 1, etree.fromstring("<pub-date pub-type='collection'><year>%s</year></pub-date>" % collection))
	return root
constructors.append([add_collection, [get_collection]])

def get_pubdate(m):
	return copy.deepcopy(m.xpath("//pub-date[@pub-type='epub']")[0])

def add_pubdate(root, date):
	article_meta = root.xpath("//article-meta")[0]
	for node in article_meta.xpath("pub-date[@pub-type='epub']"):
		article_meta.remove(node)
	article_meta.insert(get_author_notes_index(root) + 2, date)
	return root
constructors.append([add_pubdate, [get_pubdate]])

def get_volume(m):
    volumes = {'plosbiol':2002, 'plosmed':2003, 'ploscomp':2004, 'plosgen':2004, 'plospath':2004, 'plosone':2005, 'plosntds':2006}
    year = m.xpath("//pub-date[@pub-type='epub']/year")[0].text
    return str(int(year) - volumes[get_journal(m)])

def add_volume(root, volume):
	article_meta = root.xpath("//article-meta")[0]
	for node in article_meta.xpath("volume"):
		article_meta.remove(node)
	article_meta.insert(get_author_notes_index(root) + 3, etree.fromstring("""<volume>%s</volume>""" % volume))
	return root
constructors.append([add_volume, [get_volume]])

def get_issue(m):
	return str(int(m.xpath("//pub-date[@pub-type='epub']/month")[0].text))

def add_issue(root, issue):
	article_meta = root.xpath("//article-meta")[0]
	for node in article_meta.xpath("issue"):
		article_meta.remove(node)
	article_meta.insert(get_author_notes_index(root) + 4, etree.fromstring("""<issue>%s</issue>""" % issue))
	return root
constructors.append([add_issue, [get_issue]])

def add_elocation(root, doi):
	article_meta = root.xpath("//article-meta")[0]
	for node in article_meta.xpath("elocation-id"):
		article_meta.remove(node)
	article_meta.insert(get_author_notes_index(root) + 5, etree.fromstring("""<elocation-id>e%s</elocation-id>""" % doi[-5:]))
	return root
constructors.append([add_elocation, [get_article_doi]])

def get_received_date(m):
	return m.xpath("//date[@date-type='received']")[0]

def get_accepted_date(m):
	return m.xpath("//date[@date-type='accepted']")[0]

def add_history(root, received, accepted):
	article_meta = root.xpath("//article-meta")[0]
	for node in article_meta.xpath("history"):
		article_meta.remove(node)
	history = etree.Element('history')
	history.append(received)
	history.append(accepted)
	article_meta.insert(get_author_notes_index(root) + 6, history)
	return root
constructors.append([add_history, [get_received_date, get_accepted_date]])

def get_copyright_holder(m):
	return m.xpath("//contrib[@contrib-type='author']/role[@content-type='1']")[0].getnext().xpath('surname')[0].text + ' et al'

def get_copyright_statement(m):
	s = m.xpath("//custom-meta[@id='copyright-statement']/meta-value")[0].text
	if s.startswith('No'):
		return 'This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.'
	if s.startswith('Yes'):
		return 'This is an open-access article distributed under the terms of the Creative Commons Public Domain declaration which stipulates that, once placed in the public domain, this work may be freely reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any lawful purpose.'

def add_permissions(root, pubdate, holder, statement):
	article_meta = root.xpath("//article-meta")[0]
	for node in article_meta.xpath("permissions"):
		article_meta.remove(node)
	year = pubdate.xpath("year")[0].text
	article_meta.insert(get_author_notes_index(root) + 7, etree.fromstring("""<permissions xmlns:xlink="http://www.w3.org/1999/xlink">
    <copyright-year>%s</copyright-year><copyright-holder>%s</copyright-holder>
    <license xlink:type="simple"><license-p>%s</license-p></license>
  	</permissions>""" % (year, holder, statement)))
	return root
constructors.append([add_permissions, [get_pubdate, get_copyright_holder, get_copyright_statement]])

def get_funding_statement(m):
	return m.xpath("//custom-meta[@id='financial-disclosure']/meta-value")[0].text

def add_funding(root, statement):
	article_meta = root.xpath("//article-meta")[0]
	for node in article_meta.xpath("funding-group"):
		article_meta.remove(node)
	article_meta.append(etree.fromstring("""<funding-group><funding-statement>%s</funding-statement></funding-group>""" % statement))
	return root
constructors.append([add_funding, [get_funding_statement]])

# remove SI in body if they exist
def strip_body_si(root):
	for fig in root.xpath("//fig"):
		if re.search('figS[0-9]', fig.attrib['id']):
			fig.getparent().remove(fig)
	return root
constructors.append([strip_body_si, []])

def fix_figures(root, doi):
	i = 1
	for fig in root.xpath("//fig"):
		fig_doi = doi[-12:] + ".g" + str(i).zfill(3)
		fig_id = re.sub('\.', '-', fig_doi)
		for xref in root.xpath("//xref[@ref-type='fig']"):
			if xref.attrib['rid'] == fig.attrib['id']:
				xref.attrib['rid'] = fig_id
		fig.attrib['id'] = fig_id
		fig.insert(0, etree.fromstring("""<object-id pub-id-type="doi">10.1371/journal.%s</object-id>""" % fig_doi))
		fig.xpath("graphic")[0].attrib["{http://www.w3.org/1999/xlink}href"] = fig_doi + ".tif"
		i += 1
	return root
constructors.append([fix_figures, [get_article_doi]])

def fix_si(root, doi):
	i = 1
	for si in root.xpath("//supplementary-material"):
		si_doi = doi[-12:] + ".s" +str(i).zfill(3)
		si_id = re.sub('\.', '-', si_doi)
		for xref in root.xpath("//xref[@ref-type='supplementary-material']"):
			if xref.attrib['rid'] == si.attrib['id']:
				xref.attrib['rid'] = si_doi
		si.attrib['id'] = si_doi
		# filetype unknown from merops output; default to tif
		si.attrib["{http://www.w3.org/1999/xlink}href"] = si_doi + ".tif"
		# remove graphic children if they exist
		for graphic in si.xpath("graphic"):
			si.remove(graphic)
		i += 1
	return root
constructors.append([fix_si, [get_article_doi]])

if __name__ == '__main__':
	if len(sys.argv) != 4:
		sys.exit('usage: metadata_builder.py metadata.xml before.xml after.xml')
	parser = etree.XMLParser(recover = True, remove_comments = True)
	m = etree.parse(sys.argv[1], parser).getroot()
	e = etree.parse(sys.argv[2], parser)
	root = e.getroot()
	for constructor, subfunctions in constructors:
		root = constructor(root, *map(lambda x: x(m), subfunctions))
	e.write(sys.argv[3], xml_declaration = True, encoding = 'UTF-8')
	print 'done'
