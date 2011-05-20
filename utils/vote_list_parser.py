from sgmllib import SGMLParser, SGMLParseError
import htmlentitydefs
import re

MEMBER_NAME_TRANSFORMS = {
        'Korhonen Timo': 'Korhonen Timo V.',
        'Saarela Tanja': 'Karpela Tanja',
        'Taberman Tommy': 'Tabermann Tommy',
        'Kumpula Miapetra': 'Kumpula-Natri Miapetra',
        'Forsius-Harkimo Merikukka': 'Forsius Merikukka',
}

class Parser(SGMLParser):
        def __clear_state(self):
                self.td_parse_nr = 0
                self.is_in_list = False
                self.name = None
                self.info = None
                self.vote = None
                self.desc_parse_nr = 0
                self.is_in_asettelu = False
                self.in_info = False
                self.in_subject = 0
                self.in_docs = 0
                return

        def reset(self):
                self.__clear_state()
                self.vote_list = []
                self.desc = {}
                SGMLParser.reset(self)
                self.entitydefs = htmlentitydefs.entitydefs

        def start_table(self, attrs):
                if self.is_in_list:
                        raise SGMLParseError('Unexpected <table> tag')
                        return

                for name, value in attrs:
                        if name == 'class' and value == 'statistics':
                                self.is_in_list = True
                                break
                        if name == 'class' and value == 'voteResults':
                                self.desc_parse_nr = 1
                                break
        def end_table(self):
                if not self.is_in_list and not self.desc_parse_nr:
                        return
                self.__clear_state()

        def start_td(self, attrs):
                if not self.is_in_list:
                        return
                # 0 -> start
                # 1 -> name
                # 2 -> vote
                if self.td_parse_nr == 2:
                        for name, value in attrs:
                                if name == "class":
                                        self.td_parse_nr = 0
                                        return
                        self.name = ''
                        self.td_parse_nr = 1
                        return
                self.td_parse_nr += 1
                if self.td_parse_nr == 1:
                        self.name = ''
                else:
                        self.vote = ''

        def end_td(self):
                if self.in_docs:
                        self.in_docs = 0
                        return
                if self.in_info or self.in_subject:
                        self.__end_info_item()
                        return

                VOTE_CHOICES = {
                        u'Jaa': 'Y',
                        u'Ei': 'N',
                        u'Tyhj\u00e4\u00e4': 'E',
                        u'Poissa': 'A',
                        u'Puhemies': 'S'
                }
                if self.td_parse_nr != 2:
                        return
                if not self.vote:
                        return

                vote = self.vote
                (name, party) = self.name.split('/')
                name = name.rstrip()

                if (vote != 'Jaa' and vote != 'Ei' and
                    vote != u'Tyhj\u00e4\u00e4' and vote != 'Poissa' and
                    vote != 'Tyhj'):
                        print self.name
                        print vote
                        raise Exception("invalid vote value")

                s = u' puhemiehen\u00e4'
                if party.endswith(s):
                        if vote != 'Poissa':
                                raise Exception("invalid puhemies vote")
                        party = party[0:len(party) - len(s)]
                        vote = 'Puhemies'
                if name in MEMBER_NAME_TRANSFORMS:
                        name = MEMBER_NAME_TRANSFORMS[name]
                self.vote_list.append([name, party, VOTE_CHOICES[vote]])

        def __parse_vote_data(self, text):
                text = text.decode('iso8859-1')
                if not text.strip():
                        return
                if self.td_parse_nr == 1:
                        self.name += text
                        return
                if self.td_parse_nr == 2:
                        self.vote += text
                        return

        def start_a(self, attrs):
                if (not self.desc_parse_nr == 2) and (not self.in_docs):
                        return
                for name, value in attrs:
                        if name == "href":
                                link = value
                                break
                if self.desc_parse_nr == 2:
                        self.desc_parse_nr = 3
                        self.desc['session_link'] = link
                elif self.in_docs:
                        self.doc_link = link
                        self.info = ''
                        self.in_docs = 2
        def end_a(self):
                if not self.in_docs == 2:
                        return
                self.info = self.info.rstrip()
                m = re.match(r'(\w+) (\d+/\d{4})', self.info)
                if not m:
                        raise Exception("Invalid document name")
                doc = {'type': m.groups()[0], 'id': m.groups()[1]}
                doc['url'] = self.doc_link
                self.desc['docs'].append(doc)
                self.in_docs = 1

        def start_tbody(self, attrs):
                if 'info' in self.desc:
                        return
                self.in_info = True
                self.desc['info'] = []
                self.info = ""
        def __parse_info(self, text):
                text = text.decode('iso8859-1')
                text = text.replace(u'\u009a', u'\u0161')
                if not self.info:
                        text = text.lstrip()
                self.info += text
        def __end_info_item(self):
                info = self.info.rstrip()
                if self.in_subject:
                        self.in_subject += 1
                        if self.in_subject < 3:
                                self.info = ""
                                return
                        self.desc['subject'] = info
                        self.info = None
                        self.in_subject = 0
                        return

                if len(info) <= 5:
                        self.info = ""
                        return
                self.desc['info'].append(info)
                self.info = ""
        def end_tbody(self):
                self.in_info = False
        def start_th(self, attrs):
                self.in_info = False
                for name, value in attrs:
                        if name == 'scope' and value == 'row':
                                if self.in_subject or 'subject' in self.desc:
                                        return
                                self.in_subject = 1
                                self.info = ""
                                break
                        elif name == 'id' and value == 'asiakirjat':
                                self.desc['docs'] = []
                                self.in_docs = 1
                                break
        def end_th(self):
                if self.in_subject:
                        self.__end_info_item()

        def __parse_desc_data(self, text):
                text = text.decode('iso8859-1')
                if not text.strip():
                        return
                if self.desc_parse_nr == 1:
                        text = text.strip()
#                        m = re.match(r"(\w+) (\d+)\s+klo ([0-9.]{5})", text)
                        m = re.match(r"(?u)(\w+) (\d+)\s+klo ([0-9.]{5})", text)
                        if not m:
                                raise Exception("invalid vote description")
                        self.desc['nr'] = m.group(2)
                        self.desc['time'] = m.group(3).replace('.', ':')
                        self.desc_parse_nr = 2
                elif self.desc_parse_nr == 3:
                        text = text.strip()
                        (id, date) = text.split('/')
                        if not id or not date:
                                raise Exception("invalid session id")
                        (d, m, y) = date.split('.')
                        self.desc['date'] = '-'.join((y, m, d))
                        self.desc_parse_nr = 0
                return

        def handle_data(self, text):
                if self.td_parse_nr:
                        self.__parse_vote_data(text)
                elif self.is_in_asettelu:
                        self.__parse_asettelu(text)
                elif self.desc_parse_nr:
                        self.__parse_desc_data(text)
                elif self.in_info or self.in_subject:
                        self.__parse_info(text)
                elif self.in_docs == 2:
                        self.__parse_info(text)

        def get_votes(self):
                return self.vote_list
        def get_desc(self):
                return self.desc
