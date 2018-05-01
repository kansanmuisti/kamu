from sgmllib import SGMLParser
import html.entities

class Parser(SGMLParser):
        def __clear_state(self):
                self.last_link = None
                self.is_in_list = False
                self.name = None

        def reset(self):
                self.party_list = []
                self.__clear_state()
                SGMLParser.reset(self)
                self.entitydefs = html.entities.entitydefs
                self.entitydefs['nbsp'] = '\u0020'

        # Look for '<div class="list-items">' first.
        def start_div(self, attrs):
                if self.is_in_list:
                        raise Exception("Parse error")
                for name, value in attrs:
                        if name == 'class' and value == 'c-list':
                                self.is_in_list = True
                                self.name = ''
                                break
        def end_div(self):
                if not self.is_in_list:
                        return
                self.__clear_state()

        def start_a(self, attrs):
                if not self.is_in_list:
                        return
                for name, value in attrs:
                        if name == "href":
                                self.last_link = value
                                self.name = ''
                                break
        def end_a(self):
                if not self.is_in_list:
                        return
                (fullname, name) = self.name.split('/')
                fullname = fullname.rstrip()
                info_link = self.last_link.split('?')[0]
                info_link = info_link.replace('index.htx', 'esittely.htx')
                self.party_list.append({'fullname': fullname, 'name': name,
                                        'info_link': info_link})

        def start_tr(self, attrs):
                return

        def handle_data(self, text):
                if not self.is_in_list:
                        return
                text = text.decode('utf-8')
                if not self.name:
                        text = text.lstrip()
                self.name += text
                return

        def get_list(self):
                return self.party_list
