import re
from lxml import etree, html

MONTHS = [ 'tammi', 'helmi', 'maalis', 'huhti', 'touko', u'kes\u00e4',
        u'hein\u00e4', 'elo', 'syys', 'loka', 'marras', 'joulu' ]

NAME_TRANSFORMS = {
        'Timo Korhonen': 'Timo V. Korhonen',
        'Pirkko 6-Lerner': 'Pirkko Ruohonen-Lerner',
        'Tanja Saarela': 'Tanja Karpela',
        u'Tapani T\u00f6ll i': u'Tapani T\u00f6lli',
        'Tommy Taberman': 'Tommy Tabermann',
        u'Eero Akaan -Penttil\u00e4': u'Eero Akaan-Penttil\u00e4',
        u'Eero Akaan- Penttil\u00e4': u'Eero Akaan-Penttil\u00e4',
        'Miapetra Kumpula': 'Miapetra Kumpula-Natri',
        'Riikka Moilanen -Savolainen': 'Riikka Moilanen-Savolainen',
        'Martin Saarikanga s': 'Martin Saarikangas',
        'Sirpa Asko -Seljavaara': 'Sirpa Asko-Seljavaara',
        'Sirpa Asko- Seljavaara': 'Sirpa Asko-Seljavaara',
        u'Jaana Yl\u00e4 -Mononen': u'Jaana Yl\u00e4-Mononen',
        'Merikukka Forsius-Harkimo': 'Merikukka Forsius',
}

def parse_minutes(html_str, url):
        minutes = {}
        cnv_links = []
        html_doc = html.fromstring(html_str)
        #doc = etree.tostring(html, pretty_print=True, method="html")
        html_doc.make_links_absolute(url)
        content = html_doc.xpath(".//div[@class='doclist-items']")[0]
        links = html_doc.xpath(".//a[@href]")
        for child in links:
                if not 'href' in child.attrib:
                        continue
                href = child.attrib['href']
                if 'akxtmp/skt_' in href or child.text == 'Keskustelu':
                        if 'target' in child.attrib:
                                del child.attrib['target']
                        cnv_links.append(href)
                elif child.text and "Rakenteinen asiakirja" in child.text:
                        minutes['sgml_url'] = href
        minutes['cnv_links'] = cnv_links
        hdr = html_doc.xpath(".//h1")
        grp = re.match("T.ysistunnon p.yt.kirja PTK (\w+)/(\d{4})", hdr[0].text).groups()
        if len(grp) != 2:
                raise Exception("Invalid 'h1' tag: " + hdr[0].text)
        minutes['id'] = '/'.join(grp)
        hdr = html_doc.xpath(".//h2")
        text = hdr[0].text.lower()
        if "jumalanpalvelus" in text or "avajaiset" in text or "vaalikauden" in text:
                return None
        print text
        text = text.replace(u'p\u00e4iv\u00e4n\u00e4', '')
        grps = re.search(r'(?u)\d+\s*\. .+na\s+(\d{1,2})[. ]{1,3}(\w+)kuuta\s+(\d{4})', text)
        if not grps:
                raise Exception("Invalid date: " + text)
        (d, m, y) = grps.groups()
        if not m in MONTHS:
                raise Exception("Invalid date: " + text)
        m = MONTHS.index(m) + 1
        minutes['date'] = '-'.join([y, str(m), d])
        minutes['html'] = etree.tostring(content, pretty_print=True, method="html")
        return minutes

REPLACE_CHARS = [
        (u'\u009a', u'\u0161'),
        (u'\u008a', u'\u0160'),
        (u'\u2002', u'\u0020'),
        (u'\u2003', u'\u0020'),
        (u'\u2009', u'\u0020'),
        (u'\u00a0', u'\u0020')
]

def process_line(line):
        for t in REPLACE_CHARS:
                line = line.replace(t[0], t[1])
        line = re.sub("\s+", " ", line.strip())
#        print "\t'" + line + "'"
        return line

OK_TAGS = [ 'p', 'strong', 'sub', 'sup', 'div', 'i', 'blockquote' ]

def parse_block(block, lines):
        for c in block.getchildren():
                if c.tag == 'center' or c.tag == 'br':
                        continue
                if c.tag not in OK_TAGS:
                        raise Exception("Not valid statement tag: " + c.tag)
                if c.getchildren():
                        parse_block(c, lines)
                if c.tail and len(c.tail) > 4:
                        lines.append(process_line(c.tail))
                if not c.text or len(c.text) < 2:
                        continue
                lines.append(process_line(c.text))

def parse_discussion(html_str, url):
        html_doc = html.fromstring(html_str)
        content = html_doc.xpath(".//div[@class='doclist-items']")[0]
        content.make_links_absolute(url)

        speakers = content.xpath(".//a[@name]")
        disc = []
        for s in speakers:
                s = s.getnext().getchildren()[0]
                # <strong><strong>Markus&nbsp;Mustaj&auml;rvi</strong>&nbsp;/vas:&nbsp;</strong>
                ch = s.getchildren()
                # <strong><strong><strong>Puolustusministeri&nbsp;</strong>Jyri&nbsp;H&auml;k&auml;mies</strong></strong>
                if ch:
                        name = ch[0].tail
                else:
                        name = s.text
                name = process_line(name)
                if name in NAME_TRANSFORMS:
                        name = NAME_TRANSFORMS[name]
#                print '\n' + name + '\n'
#                print name
                spkr = { 'name': name }
                block = s.getparent().getparent()
                links = block.xpath(".//a")
                for e in links:
                        block.remove(e)

                if block.tag != 'div':
                        raise Exception("No 'div' tag: " + block.tag)
                text = ""
                for ch in block.getchildren():
                        text += process_line(etree.tostring(ch, pretty_print=True, method="html"))

                ch = block.getchildren();
                if ch[0].tag != 'strong':
                        raise Exception("Not 'strong' tag: " + ch[0].tag)
                lines = []
                if ch[0].tail and len(ch[0].tail) > 4:
                        lines.append(process_line(ch[0].tail))
                block.remove(ch[0])
                parse_block(block, lines)

                spkr['statement'] = lines
#                print '\t' + str(spkr['statement'])

                spkr['html'] = text
#                print spkr['html']

                disc.append(spkr)

        return disc
