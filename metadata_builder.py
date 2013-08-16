#!/usr/bin/env python
# usage: metadata_builder.py metadata.xml before.xml after.xml

import sys
import re
import time
import copy
import mimetypes
import lxml.etree as etree
import lxml.html as html
import traceback

adders = []  # functions that add metadata to article xml
getters = []  # functions that retrieve fields from metadata xml

def remove_possible_node(parent, child):
    for node in parent.xpath(child):
        parent.remove(node)

def strip_zeros(date):
    for field in ['month','day']:
        date.xpath(field)[0].text = str(int(date.xpath(field)[0].text))
    return date

def activate_links(text):
    return re.sub(r'\b((https?|www)[^ ),]*\w)', r'<ext-link ext-link-type="uri" xlink:href="\1">\1</ext-link>', text)

def get_journal(m):
    return m.xpath("//journal-id[@journal-id-type='publisher']")[0].text
getters.append([get_journal])

def get_issn(m):
    return m.xpath("//issn[@pub-type='ppub']")[0].text
getters.append([get_issn])

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
adders.append([add_journal_meta, ['journal', 'issn']])

def get_ms_number(m):
    return m.xpath("//article-id[@pub-id-type='manuscript']")[0].text
getters.append([get_ms_number])

def add_ms_number(root, ms):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "article-id[@pub-id-type='publisher-id']")
    article_meta.insert(0, etree.fromstring("""<article-id pub-id-type='publisher-id'>%s</article-id>""" % ms))
    return root
adders.append([add_ms_number, ['ms_number']])

def get_article_doi(m):
    return m.xpath("//article-id[@pub-id-type='doi']")[0].text
getters.append([get_article_doi])

def add_article_doi(root, doi):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "article-id[@pub-id-type='doi']")
    article_meta.insert(1, etree.fromstring("""<article-id pub-id-type="doi">%s</article-id>""" % doi))
    return root
adders.append([add_article_doi, ['article_doi']])

def get_article_type(m):
    return m.xpath("//article-categories//subj-group[@subj-group-type='Article Type']/subject")[0].text
getters.append([get_article_type])

def add_article_type(root, article_type):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "article-categories")
    article_meta.insert(2, etree.fromstring("""<article-categories><subj-group subj-group-type="heading">
    <subject>%s</subject></subj-group></article-categories>""" % article_type))
    return root
adders.append([add_article_type, ['article_type']])

def get_alt_title(m):
    return m.xpath("//alt-title[@alt-title-type='running-head']")[0]
getters.append([get_alt_title])

def add_alt_title(root, alt_title):
    title_group = root.xpath("//title-group")[0]
    remove_possible_node(title_group, "alt-title[@alt-title-type='running-head']")
    title_group.insert(1, alt_title)
    return root
adders.append([add_alt_title, ['alt_title']])    

def get_editors(m):
    return m.xpath("//contrib[@contrib-type='editor']")
getters.append([get_editors])

def get_affs(m):
    affs = {}
    for aff in m.xpath("//aff"):
        affs[aff.attrib['id']] = aff
    return affs
getters.append([get_affs])

def add_editors(root, editors, affs):
    article_meta = root.xpath("//article-meta")[0]
    for editor in article_meta.xpath("contrib-group/contrib[@contrib-type='editor']"):
        article_meta.remove(editor.getparent())
    for aff in article_meta.xpath("aff[contains(@id,'edit')]"):
        article_meta.remove(aff)
    previous = article_meta.index(article_meta.xpath("aff")[-1])
    contrib_group = etree.Element('contrib-group')
    i = 1
    for editor in editors:
        contrib_group.append(editor)
        editor.xpath("role")[0].text = 'Editor'
        for email in editor.xpath("email"):
            editor.remove(email)
        for degree in editor.xpath("degrees"):
            editor.remove(degree)
        rid = editor.xpath("xref[@ref-type='aff']")[0].attrib['rid']
        institution = affs[rid].xpath("institution")[0].text.strip()
        country = affs[rid].xpath("country")[0].text.title().replace('United States', 'United States of America')
        aff = html.fromstring("<aff id='edit"+str(i)+"'><addr-line>"+institution+', '+country+"</addr-line></aff>")
        article_meta.insert(previous + i, aff)
        editor.xpath("xref[@ref-type='aff']")[0].attrib['rid'] = "edit"+str(i)
        i += 1
    article_meta.insert(previous + 1, contrib_group)
    return root
adders.append([add_editors, ['editors', 'affs']])

def get_author_notes_index(root):
    am = root.xpath("//article-meta")[0]
    author_notes = am.xpath("author-notes")[0]
    return am.index(author_notes)
getters.append([get_author_notes_index, 'error: no author-notes - could not add conflict, contrib, collection, pubdate, volume, issue, elocation, history, copyright'])

def get_conflict(m):
    return m.xpath("//meta-name[contains(text(),'Competing Interest')]")[0].getnext().text
getters.append([get_conflict])

def add_conflict(root, conflict, author_notes_index):
    author_notes = root.xpath("//author-notes")[0]
    remove_possible_node(author_notes, "fn[@fn-type='conflict']")
    author_notes.insert(1, html.fromstring("""<fn fn-type="conflict"><p>%s</p></fn>""" % conflict))
    return root
adders.append([add_conflict, ['conflict', 'author_notes_index']])

def get_contrib(m):
    result = ''
    for au in m.xpath("//meta-name[contains(text(),'Author Contributions')]"):
        result += re.sub(r'.*Author Contributions: ([^<]*).*', r'\1', au.text.replace('\n','')).capitalize() + ': ' + au.getnext().text.strip() + '. '
    return result.replace('Other: ', '')
getters.append([get_contrib])

def add_contrib(root, contrib, author_notes_index):
    author_notes = root.xpath("//author-notes")[0]
    remove_possible_node(author_notes, "fn[@fn-type='con']")
    author_notes.insert(2, etree.fromstring("""<fn fn-type="con"><p>%s</p></fn>""" % contrib))
    return root
adders.append([add_contrib, ['contrib', 'author_notes_index']])

def add_collection(root, pubdate, author_notes_index):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "pub-date[@pub-type='collection']")
    year = pubdate.xpath("year")[0].text
    article_meta.insert(get_author_notes_index(root) + 1, etree.fromstring("<pub-date pub-type='collection'><year>%s</year></pub-date>" % year))
    return root
adders.append([add_collection, ['pubdate', 'author_notes_index']])

def get_pubdate(m):
    return strip_zeros(copy.deepcopy(m.xpath("//pub-date[@pub-type='epub']")[0]))
getters.append([get_pubdate, 'error: missing/incomplete pubdate - could not add pubdate, volume, issue, collection, copyright'])

def add_pubdate(root, date, author_notes_index):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "pub-date[@pub-type='epub']")
    article_meta.insert(get_author_notes_index(root) + 2, date)
    return root
adders.append([add_pubdate, ['pubdate', 'author_notes_index']])

def add_volume(root, pubdate, author_notes_index):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "volume")
    volumes = {'pbiology':2002, 'pmedicine':2003, 'pcompbiol':2004, 'pgenetics':2004, 'ppathogens':2004, 'pone':2005, 'pntd':2006}
    year = pubdate.xpath("year")[0].text
    volume = str(int(year) - volumes[get_journal(m)])
    article_meta.insert(get_author_notes_index(root) + 3, etree.fromstring("""<volume>%s</volume>""" % volume))
    return root
adders.append([add_volume, ['pubdate', 'author_notes_index']])

def add_issue(root, pubdate, author_notes_index):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "issue")
    month = pubdate.xpath("month")[0].text
    article_meta.insert(get_author_notes_index(root) + 4, etree.fromstring("""<issue>%s</issue>""" % month))
    return root
adders.append([add_issue, ['pubdate', 'author_notes_index']])

def add_elocation(root, doi, author_notes_index):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "elocation-id")
    article_meta.insert(get_author_notes_index(root) + 5, etree.fromstring("""<elocation-id>e%s</elocation-id>""" % doi[-5:]))
    return root
adders.append([add_elocation, ['article_doi', 'author_notes_index']])

def get_received_date(m):
    return strip_zeros(m.xpath("//date[@date-type='received']")[0])
getters.append([get_received_date])

def get_accepted_date(m):
    return strip_zeros(m.xpath("//date[@date-type='accepted']")[0])
getters.append([get_accepted_date])

def add_history(root, received, accepted, author_notes_index):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "history")
    history = etree.Element('history')
    history.append(received)
    history.append(accepted)
    article_meta.insert(get_author_notes_index(root) + 6, history)
    return root
adders.append([add_history, ['received_date', 'accepted_date', 'author_notes_index']])

def get_copyright_holder(m):
    s = m.xpath("//meta-name[contains(text(),'Government Employee')]")[0].getnext().text
    if s.startswith('No'):
        return '<copyright-holder>'+m.xpath("//contrib[@contrib-type='author']/role[@content-type='1']")[0].getnext().xpath('surname')[0].text+' et al</copyright-holder>'
    else:
        return ''
getters.append([get_copyright_holder])

def get_copyright_statement(m):
    s = m.xpath("//meta-name[contains(text(),'Government Employee')]")[0].getnext().text
    if s.startswith('No'):
        return 'This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.'
    if s.startswith('Yes'):
        return 'This is an open-access article, free of all copyright, and may be freely reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any lawful purpose. The work is made available under the Creative Commons CC0 public domain dedication.'
getters.append([get_copyright_statement])

def add_permissions(root, pubdate, holder, statement, author_notes_index):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "permissions")
    year = pubdate.xpath("year")[0].text
    article_meta.insert(get_author_notes_index(root) + 7, etree.fromstring("""<permissions xmlns:xlink="http://www.w3.org/1999/xlink">
    <copyright-year>%s</copyright-year>%s<license xlink:type="simple"><license-p>%s</license-p></license>
    </permissions>""" % (year, holder, statement)))
    return root
adders.append([add_permissions, ['pubdate', 'copyright_holder', 'copyright_statement', 'author_notes_index']])

def get_funding_statement(m):
    return activate_links(m.xpath("//meta-name[contains(text(),'Financial Disclosure')]")[0].getnext().text)
getters.append([get_funding_statement])

def add_funding(root, statement):
    article_meta = root.xpath("//article-meta")[0]
    remove_possible_node(article_meta, "funding-group")
    article_meta.append(html.fromstring("""<funding-group"><funding-statement>%s</funding-statement></funding-group>""" % statement))
    return root
adders.append([add_funding, ['funding_statement']])

# remove SI in body if they exist
def strip_body_si(root):
    for fig in root.xpath("//fig"):
        if re.search('figS[0-9]', fig.attrib['id']):
            fig.getparent().remove(fig)
    return root
adders.append([strip_body_si, []])

def fix_figures(root, doi):
    # first fix multiple rids
    for xref in root.xpath("//xref[@ref-type='fig']"):
        rids = xref.attrib['rid'].split()
        if len(rids) > 1:
            xref_num = re.sub(r'\D*(\d+)\D*', r'\1', xref.text)
            for rid in rids:
                rid_num = re.sub(r'\D*(\d+)\D*', r'\1', rid)
                if xref_num == rid_num:
                    xref.attrib['rid'] = rid
    # main fix figures
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
adders.append([fix_figures, ['article_doi']])

def get_si_ext(m):
    exts = {}
    for si in m.xpath("//supplementary-material"):
        filename = si.attrib['{http://www.w3.org/1999/xlink}href']
        name = si.xpath("label")[0].text.strip() if si.xpath("label") else filename[:filename.index('.')]
        exts[name] = filename[filename.rfind('.'):]
    return exts
getters.append([get_si_ext])

def fix_si(root, doi, exts):
    i = 1
    for si in root.xpath("//supplementary-material"):
        si_doi = doi[-12:] + ".s" +str(i).zfill(3)
        for xref in root.xpath("//xref[@ref-type='supplementary-material']"):
            if xref.attrib['rid'] == si.attrib['id']:
                xref.attrib['rid'] = si_doi
        si.attrib['id'] = si_doi
        ext = exts.get(si.xpath("label")[0].text.strip(), '')
        si.attrib["{http://www.w3.org/1999/xlink}href"] = si_doi + ext.lower()
        try: si.attrib['mimetype'] = mimetypes.guess_type('x' + ext, False)[0]
        except Exception as ee: logger.error('error getting mimetype for ' + si_doi + ext + ': ' + str(ee))
        si.xpath("caption")[0].append(etree.fromstring('<p>('+ext.replace('.','').upper()+')</p>'))
        # remove graphic children if they exist
        for graphic in si.xpath("graphic"):
            si.remove(graphic)
        i += 1
    return root
adders.append([fix_si, ['article_doi', 'si_ext']])

if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit('usage: metadata_builder.py metadata.xml before.xml after.xml')
    print >>sys.stderr, '** metadata builder starting'
    log = open('/var/local/scripts/production/articleprep/log/metadata_builder.log', 'a')
    log.write('-'*50 + '\n'+time.strftime("%Y-%m-%d %H:%M:%S   "+sys.argv[2]+'\n'))
    try:
        parser = etree.XMLParser(recover = True, remove_comments = True)
        m = etree.parse(sys.argv[1]).getroot()
        e = etree.parse(sys.argv[2], parser)
        root = e.getroot()
    except Exception as ee:
        print 'error parsing: '+str(ee)
        log.write('** error parsing: '+str(ee)+'\n')
        log.close()
        sys.exit(1)
    meta = {}
    for args in getters:
        getter = args[0]
        error_message = args[1] if len(args)>1 else None
        try:
            tree = m if getter.__name__!='get_author_notes_index' else root
            meta[getter.__name__.replace('get_','')] = getter(tree)
        except Exception as ee:
            if error_message:
                print error_message
                log.write('** '+error_message+'\n')
            else:
                print 'error in '+getter.__name__+': '+str(ee)
                log.write('** error in '+getter.__name__+': '+str(ee)+'\n')
                traceback.print_exc()
                log.write(traceback.format_exc())
    for adder, inputs in adders:
        try:
            args = [meta[x] if x in meta else None for x in inputs]
            if not None in args:
                root = adder(root, *args)
        except Exception as ee:
            print 'error in '+adder.__name__+': '+str(ee)
            log.write('** error in '+adder.__name__+': '+str(ee)+'\n')
            traceback.print_exc()
            log.write(traceback.format_exc())
    e.write(sys.argv[3], xml_declaration = True, encoding = 'UTF-8')
    log.close()
    print >>sys.stderr, '** metadata builder exiting'
