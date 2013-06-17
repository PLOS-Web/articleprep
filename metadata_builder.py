#!/usr/bin/env python
# usage: metadata_builder.py metadata.xml before.xml after.xml

import sys
import re
import time
import copy
import mimetypes
import lxml.etree as etree

constructors = []

def remove_possible_node(parent, child):
    for node in parent.xpath(child):
        parent.remove(node)

def get_journal(m):
    return m.xpath("//journal-id[@journal-id-type='publisher']")[0].text

def get_issn(m):
    return m.xpath("//issn[@pub-type='ppub']")[0].text

def add_journal_meta(root, journal, issn):
    j = {'pbiology':['PLoS Biol','plosbiol'], 'pmedicine':['PLoS Med','plosmed'], 
         'pcompbiol':['PLoS Comput Biol','ploscomp'], 'pgenetics':['PLoS Genet','plosgen'], 
         'ppathogens':['PLoS Pathog','plospath'], 'pone':['PLoS ONE','plosone'], 'pntd':['PLoS Negl Trop Dis','plosntds']}
    front = root.xpath("//front")[0]
    remove_possible_node(front, "journal-meta")
    front.insert(0, etree.fromstring("""<journal-meta>
    <journal-id journal-id-type="nlm-ta">%s</journal-id>
    <journal-id journal-id-type="publisher-id">plos</journal-id>
    <journal-id journal-id-type="pmc">%s</journal-id>
    <journal-title-group><journal-title>%s</journal-title></journal-title-group>
    <issn pub-type="epub">%s</issn>
    <publisher><publisher-name>Public Library of Science</publisher-name>
    <publisher-loc>San Francisco, USA</publisher-loc></publisher>
    </journal-meta>""" % (j[journal][0], j[journal][1], j[journal][0], issn)))
    return root
constructors.append([add_journal_meta, [get_journal, get_issn]])

def get_ms_number(m):
    return m.xpath("//article-id[@pub-id-type='manuscript']")[0].text

def add_ms_number(root, ms):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "article-id[@pub-id-type='publisher-id']")
    article_meta.insert(0, etree.fromstring("""<article-id pub-id-type='publisher-id'>%s</article-id>""" % ms))
    return root
constructors.append([add_ms_number, [get_ms_number]])

def get_article_doi(m):
    return m.xpath("//article-id[@pub-id-type='doi']")[0].text

def add_article_doi(root, doi):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "article-id[@pub-id-type='doi']")
    article_meta.insert(1, etree.fromstring("""<article-id pub-id-type="doi">%s</article-id>""" % doi))
    return root
constructors.append([add_article_doi, [get_article_doi]])

def get_article_type(m):
    return m.xpath("//article-categories//subj-group[@subj-group-type='Article Type']/subject")[0].text

def add_article_type(root, article_type):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "article-categories")
    article_meta.insert(2, etree.fromstring("""<article-categories><subj-group subj-group-type="heading">
    <subject>%s</subject></subj-group></article-categories>""" % article_type))
    return root
constructors.append([add_article_type, [get_article_type]])

def get_alt_title(m):
    return m.xpath("//alt-title[@alt-title-type='running-head']")[0]

def add_alt_title(root, alt_title):
    title_group = root.xpath("//title-group")[0]
    remove_possible_node(title_group, "alt-title[@alt-title-type='running-head']")
    title_group.insert(1, alt_title)
    return root
constructors.append([add_alt_title, [get_alt_title]])    

def get_editors(m):
    return m.xpath("//contrib[@contrib-type='editor']")

def get_affs(m):
    affs = {}
    for aff in m.xpath("//aff"):
        affs[aff.attrib['id']] = aff
    return affs

def add_editors(root, editors, affs):
    article_meta = root.xpath("//article-meta")[0]
    previous = article_meta.index(article_meta.xpath("aff")[-1])
    contrib_group = etree.Element('contrib-group')
    i = 1
    for editor in editors:
        contrib_group.append(editor)
        editor.xpath("role")[0].text = 'Editor'
        editor.remove(editor.xpath("email")[0])
        rid = editor.xpath("xref[@ref-type='aff']")[0].attrib['rid']
        institution = affs[rid].xpath("institution")[0].text.strip()
        country = affs[rid].xpath("country")[0].text.title().replace('United States', 'United States of America')
        aff = etree.fromstring("<aff id='edit"+str(i)+"'><addr-line>"+institution+', '+country+"</addr-line></aff>")
        article_meta.insert(previous + i, aff)
        editor.xpath("xref[@ref-type='aff']")[0].attrib['rid'] = "edit"+str(i)
        i += 1
    article_meta.insert(previous + 1, contrib_group)
    return root
constructors.append([add_editors, [get_editors, get_affs]]) 

def get_conflict(m):
    return m.xpath("//meta-name[contains(text(),'Competing Interest')]")[0].getnext().text

def add_conflict(root, conflict):
    author_notes = root.xpath("//author-notes")[0]
    remove_possible_node(author_notes, "fn[@fn-type='conflict']")
    author_notes.insert(1, etree.fromstring("""<fn fn-type="conflict"><p>%s</p></fn>""" % conflict))
    return root
constructors.append([add_conflict, [get_conflict]])

def get_contrib(m):
    result = ''
    for au in m.xpath("//meta-name[contains(text(),'Author Contributions')]"):
        result += re.sub(r'.*Author Contributions: ([^<]*).*', r'\1', au.text.replace('\n','')).capitalize() + ': ' + au.getnext().text + '. '
    return result

def add_contrib(root, contrib):
    author_notes = root.xpath("//author-notes")[0]
    remove_possible_node(author_notes, "fn[@fn-type='con']")
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
    remove_possible_node(article_meta, "pub-date[@pub-type='collection']")
    article_meta.insert(get_author_notes_index(root) + 1, etree.fromstring("<pub-date pub-type='collection'><year>%s</year></pub-date>" % collection))
    return root
constructors.append([add_collection, [get_collection]])

def get_pubdate(m):
    return copy.deepcopy(m.xpath("//pub-date[@pub-type='epub']")[0])

def add_pubdate(root, date):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "pub-date[@pub-type='epub']")
    article_meta.insert(get_author_notes_index(root) + 2, date)
    return root
constructors.append([add_pubdate, [get_pubdate]])

def get_volume(m):
    volumes = {'pbiology':2002, 'pmedicine':2003, 'pcompbiol':2004, 'pgenetics':2004, 'ppathogens':2004, 'pone':2005, 'pntd':2006}
    year = m.xpath("//pub-date[@pub-type='epub']/year")[0].text
    return str(int(year) - volumes[get_journal(m)])

def add_volume(root, volume):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "volume")
    article_meta.insert(get_author_notes_index(root) + 3, etree.fromstring("""<volume>%s</volume>""" % volume))
    return root
constructors.append([add_volume, [get_volume]])

def get_issue(m):
    return str(int(m.xpath("//pub-date[@pub-type='epub']/month")[0].text))

def add_issue(root, issue):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "issue")
    article_meta.insert(get_author_notes_index(root) + 4, etree.fromstring("""<issue>%s</issue>""" % issue))
    return root
constructors.append([add_issue, [get_issue]])

def add_elocation(root, doi):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "elocation-id")
    article_meta.insert(get_author_notes_index(root) + 5, etree.fromstring("""<elocation-id>e%s</elocation-id>""" % doi[-5:]))
    return root
constructors.append([add_elocation, [get_article_doi]])

def get_received_date(m):
    return m.xpath("//date[@date-type='received']")[0]

def get_accepted_date(m):
    return m.xpath("//date[@date-type='accepted']")[0]

def add_history(root, received, accepted):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "history")
    history = etree.Element('history')
    history.append(received)
    history.append(accepted)
    article_meta.insert(get_author_notes_index(root) + 6, history)
    return root
constructors.append([add_history, [get_received_date, get_accepted_date]])

def get_copyright_holder(m):
    min_role = min([role.attrib['content-type'] for role in m.xpath("//contrib[@contrib-type='author']/role")])
    return m.xpath("//contrib[@contrib-type='author']/role[@content-type="+min_role+"]")[0].getnext().xpath('surname')[0].text + ' et al'

def get_copyright_statement(m):
    s = m.xpath("//meta-name[contains(text(),'Government Employee')]")[0].getnext().text
    if s.startswith('No'):
        return 'This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.'
    if s.startswith('Yes'):
        return 'This is an open-access article distributed under the terms of the Creative Commons Public Domain declaration which stipulates that, once placed in the public domain, this work may be freely reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any lawful purpose.'

def add_permissions(root, pubdate, holder, statement):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "permissions")
    year = pubdate.xpath("year")[0].text
    article_meta.insert(get_author_notes_index(root) + 7, etree.fromstring("""<permissions xmlns:xlink="http://www.w3.org/1999/xlink">
    <copyright-year>%s</copyright-year><copyright-holder>%s</copyright-holder><license xlink:type="simple"><license-p>%s</license-p></license>
    </permissions>""" % (year, holder, statement)))
    return root
constructors.append([add_permissions, [get_pubdate, get_copyright_holder, get_copyright_statement]])

def get_funding_statement(m):
    return m.xpath("//meta-name[contains(text(),'Financial Disclosure')]")[0].getnext().text

def add_funding(root, statement):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "funding-group")
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

def get_si_ext(m):
    exts = {}
    for si in m.xpath("//supplementary-material"):
        filename = si.attrib['{http://www.w3.org/1999/xlink}href']
        exts[si.xpath("label")[0].text] = filename[filename.rfind('.'):]
    return exts

def fix_si(root, doi, exts):
    i = 1
    for si in root.xpath("//supplementary-material"):
        si_doi = doi[-12:] + ".s" +str(i).zfill(3)
        si_id = re.sub('\.', '-', si_doi)
        for xref in root.xpath("//xref[@ref-type='supplementary-material']"):
            if xref.attrib['rid'] == si.attrib['id']:
                xref.attrib['rid'] = si_doi
        si.attrib['id'] = si_doi
        ext = exts.get(si.xpath("label")[0].text, '')
        si.attrib["{http://www.w3.org/1999/xlink}href"] = si_doi + ext
        try: si.attrib['mimetype'] = mimetypes.guess_type('x' + ext, False)[0]
        except Exception as ee: log.write('** error getting mimetype for ' + si_doi + ext + ': ' + str(ee) + '\n')
        # remove graphic children if they exist
        for graphic in si.xpath("graphic"):
            si.remove(graphic)
        i += 1
    return root
constructors.append([fix_si, [get_article_doi, get_si_ext]])

if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit('usage: metadata_builder.py metadata.xml before.xml after.xml')
    log = open('/var/local/scripts/production/articleprep/log/metadata_log', 'a')
    log.write('-' * 80 + '\n' + time.strftime("%Y-%m-%d %H:%M:%S") + '  ' + ' '.join(sys.argv[1:]) + '\n')
    try:
        parser = etree.XMLParser(recover = True, remove_comments = True)
        m = etree.parse(sys.argv[1], parser).getroot()
        e = etree.parse(sys.argv[2], parser)
        root = e.getroot()
    except Exception as ee:
        log.write('** error parsing: ' + str(ee) + '\n')
        log.close()
        raise
    for constructor, subfunctions in constructors:
        try: root = constructor(root, *map(lambda x: x(m), subfunctions))
        except Exception as ee: log.write('** error in ' + constructor.__name__ + ': ' + str(ee) + '\n')
    e.write(sys.argv[3], xml_declaration = True, encoding = 'UTF-8')
    log.close()
    print 'done'
