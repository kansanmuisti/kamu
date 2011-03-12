from sgmllib import SGMLParser
import htmlentitydefs

class Parser(SGMLParser):
        def __clear_state(self):
                self.last_link = None
                self.is_in_list = False
                self.is_in_mop = False
                self.name = None

        def reset(self):
                self.mop_list = []
                self.__clear_state()
                SGMLParser.reset(self)
                self.entitydefs = htmlentitydefs.entitydefs
                self.entitydefs['nbsp'] = u'\u0020'

        # Look for '<div class="list-items">' first.
        def start_table(self, attrs):
                if self.is_in_list:
                        raise Exception("Parse error")
                for name, value in attrs:
                        if name != 'width':
                                break
                        if value != '595':
                                break
                        self.is_in_list = True
                        break
        def end_table(self):
                if not self.is_in_list:
                        return
                self.__clear_state()

        def start_a(self, attrs):
                if not self.is_in_list:
                        return
                for name, value in attrs:
                        if name == "href":
#                                value = value.replace("hx3510", "hx5110");
#                                value = value.replace("bin/hx5000.sh", "bin/thw/trip/")
                                self.last_link = value
                                self.is_in_mop = True
                                self.name = u""
                                break
        def end_a(self):
                if not self.is_in_mop:
                        return
                self.is_in_mop = False
                names = self.name.split(',')
                surname = ','.join(names[0:len(names)-1])
                firstnames = names[-1]
                surname = surname.lstrip()
                firstnames = firstnames.strip()
                print firstnames + ':' + surname
                self.mop_list.append({'surname': surname, 'link': self.last_link,
                                'firstnames': firstnames})

        def start_tr(self, attrs):
                return

        def handle_data(self, text):
                if not self.is_in_mop:
                        return
                text = text.decode('iso8859-1')
                if not self.name:
                        text = text.lstrip()
                self.name += text
                return

        def get_mop_list(self):
                return self.mop_list
