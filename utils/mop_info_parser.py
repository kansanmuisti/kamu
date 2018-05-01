import re
from sgmllib import SGMLParser
import html.entities

class Parser(SGMLParser):
        def __clear_state(self):
                self.next_is_photo = False
                self.in_name = False
                self.in_header = False
                self.doclist_parse = False

        def reset(self, is_lame_frame = False):
                self.desc = {}
                self.text = None
                self.__clear_state()
                self.is_lame_frame = is_lame_frame
                SGMLParser.reset(self)
                self.entitydefs = html.entities.entitydefs
                self.entitydefs['nbsp'] = '\u0020'

        def start_frame(self, attrs):
                if not self.is_lame_frame:
                        return
                right_frame = False
                link = None
                for name, value in attrs:
                        if name == 'name':
                                if value == 'oikea2':
                                        right_frame = True
                                        continue
                                else:
                                        break
                        if name == 'src':
                                link = value
                if not right_frame:
                        return
                m = re.search(r"/ed(\d+)k-su.htm", link)
                if not m:
                        raise Exception("unable to parse vasen2 link")
                self.desc['hnro'] = m.group(1)

        def start_div(self, attrs):
                for name, value in attrs:
                        if name != 'class':
                                continue
                        elif value == 'subhead':
                                self.next_is_photo = True
                                self.in_name = True
                                self.text = ""
                                break
                        elif value == 'header':
                                self.in_header = True
                                self.text = ""
                                break
                        elif value == 'doclist-items':
                                self.doclist_parse = 1
                                break
                        elif value == 'page-navi':
                                self.__clear_state()
                                break

        def end_div(self):
                if not self.in_name and not self.in_header:
                        return
                if self.in_name:
                        self.in_name = False
                        self.text = self.text.strip()
                        names = self.text.split(' ')
                        (fn, sn) = (' '.join(names[0:len(names)-1]), names[-1])
                        self.desc['name'] = sn + ' ' + fn
                if self.in_header:
                        self.in_header = False
                        (name, party) = self.text.split('/')
                        party = party.strip()
                        if party:
                                self.desc['party'] = party

        def start_img(self, attrs):
                if not self.next_is_photo:
                        return
                self.next_is_photo = False
                for name, value in attrs:
                        if name == 'src':
                                self.desc['photo'] = value
                                break

        def start_a(self, attrs):
                link = None
                is_ht = False
                for name, value in attrs:
                        if name == "id" and value == "LYHHT":
                                is_ht = True
                                continue
                        if name == "href":
                                link = value
                                if (link.startswith('/triphome/bin/hx5000.sh?') and
                                    not 'info_link' in self.desc):
                                        is_ht = True
                                continue
                if is_ht:
                        if not link:
                                raise Exception("person information link not found")
                        self.desc['info_link'] = link
        def end_a(self):
                return

        def start_tr(self, attrs):
                return

        def handle_data(self, text):
                if self.in_name or self.in_header:
                        self.text += text.decode("iso8859-1")
                elif self.doclist_parse == 1:
                        text = text.decode("iso8859-1")
                        if re.match("Eduskuntaryhm.t:", text):
                                self.doclist_parse = 'assoc'
                                self.desc['assoc'] = []
                        elif re.match("Syntym.aika ja -paikka", text):
                                self.doclist_parse = 'birth'
                        elif re.match("Puhelin:", text):
                                self.doclist_parse = 'phone'
                        elif re.match("S.hk.posti:", text):
                                self.doclist_parse = 'email'
                        elif re.match("Vaalipiiri:", text):
                                self.doclist_parse = 'district'
                                self.desc['district'] = []
                        if self.doclist_parse != 1:
                                self.text =""
                elif self.doclist_parse:
                        self.text += text.decode("iso8859-1")
                return
        def end_li(self):
                if self.doclist_parse == 'assoc':
                        table_name = 'assoc'
                elif self.doclist_parse == 'district':
                        table_name = 'district'
                else:
                        return
                DATE_MATCH = r'(\d{1,2})\.(\d{1,2}).(\d{4})'
                DATE_GROUP = r'(\d{1,2}\.\d{1,2}.\d{4})'
                text = self.text.strip()
                # Strip text within parentheses
                if text.find('(') != -1 and text.rfind(')') != -1:
                        start = text.find('(')
                        end = text.rfind(')')
                        text = text[0:start] + text[end+1:len(text)]
                m = re.split(DATE_GROUP, text)
                if len(m) < 2:
                        raise Exception("invalid district/party association")
                name = m.pop(0).strip()
                while (len(m) >= 3):
                        start = re.match(DATE_MATCH, m[0]).groups()
                        if m[1] != ' - ':
                                raise Exception("invalid district/party association")
                        end = re.match(DATE_MATCH, m[2]).groups()
                        del m[0:3]
                        if m[0] == ',  ':
                                del m[0]
                        start = '-'.join(reversed(start))
                        end = '-'.join(reversed(end))
                        self.desc[table_name].append({'name': name, 'start': start, 'end': end})
                if len(m) == 2:
                        start = re.match(DATE_MATCH, m[0]).groups()
                        if m[1] != ' -':
                                raise Exception("invalid district/party association begin")
                        start = '-'.join(reversed(start))
                        self.desc[table_name].append({'name': name, 'start': start})
                elif len(m) != 1 or (m[0] and m[0] != ','):
                        print(m)
                        raise Exception("empty district/party association")
                self.text = ""
        def end_tr(self):
                DATE_MATCH = r'(\d{1,2})\.(\d{1,2}).(\d{4})'
                if not self.doclist_parse:
                        return
                if self.doclist_parse == 'birth':
                        text = self.text.strip()
                        m = re.match(DATE_MATCH, text)
                        if not m:
                                raise Exception("invalid birth date")
                        self.desc['birthdate'] = "%s-%s-%s" % (m.group(3), m.group(2), m.group(1))
                elif self.doclist_parse == 'phone':
                        self.desc['phone'] = self.text.strip()
                elif self.doclist_parse == 'email':
                        text = self.text.strip()
                        EMAIL_MATCH = r'\b([A-Za-z0-9._%+-]+)\[at\]([A-Za-z0-9._%+-]+)'
                        if not re.match(EMAIL_MATCH, text):
                                raise Exception("invalid email")
                        l = re.split(EMAIL_MATCH, text)
                        self.desc['email'] = l[1] + '@' + l[2]
                self.doclist_parse = 1
        def unknown_endtag(self, tag):
                 if tag == 'ul':
                        self.end_li()

        '''
        def handle_starttag(self, tag, attrs):
                if tag == 'frame':
                        self.start_frame(attrs)
                elif tag == 'div':
                        self.start_div(attrs)
                elif tag == 'img':
                        self.start_img(attrs)
                elif tag == 'a':
                        self.start_a(attrs)
                elif tag == 'tr':
                        self.start_tr(attrs)
        def handle_endtag(self, tag):
                if tag == 'div':
                        self.end_div()
                elif tag == 'a':
                        self.end_a()
                elif tag == 'li':
                        self.end_li()
                elif tag == 'tr':
                        self.end_tr()
        '''
        def error(self, msg):
                print("error: " + msg)
                print(self.getpos())
                return

        def get_desc(self):
                return self.desc
