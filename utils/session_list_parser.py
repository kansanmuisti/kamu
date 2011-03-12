from sgmllib import SGMLParser

class Parser(SGMLParser):
        def __clear_state(self):
                self.last_link = None

        def reset(self, is_minutes=False):
                self.links = []
                self.is_in_item = 0
                self.forward_link = None
                self.is_in_luettelo = False
                self.is_minutes = is_minutes
                self.__clear_state()
                SGMLParser.reset(self)

        # Look for '<div class="list-items">' first.
        def start_div(self, attrs):
                if self.is_in_item:
                        self.is_in_item += 1
                        return
                for name, value in attrs:
                        if name != 'class':
                                break
                        if value != 'list-items':
                                break
                        self.is_in_item = 1
                        break
        def end_div(self):
                if not self.is_in_item:
                        return
                self.is_in_item -= 1
                if self.is_in_item == 0:
                        self.__clear_state()

        def start_a(self, attrs):
                if not self.is_in_item:
                        return
                for name, value in attrs:
                        if name == "href":
                                self.last_link = value
                                break

        def handle_data(self, text):
                if not self.is_in_item:
                        return
                text = text.decode('iso8859-1')
                text = text.strip()
                if ((self.is_minutes and text != 'HTML') or
                   (not self.is_minutes and text != 'Tulos')):
                        return
                if not self.last_link:
                        raise SGMLParseError('last link not defined')
                self.links.append(self.last_link);
                self.last_link = None
                return

        def start_form(self, attrs):
                for name, value in attrs:
                        if name == "name" and value == "luettelo3":
                                self.is_in_luettelo = True
                                break
        def end_form(self):
                self.is_in_luettelo = False

        def start_input(self, attrs):
                if not self.is_in_luettelo:
                        return
                match = False
                for name, value in attrs:
                        if name == 'name' and value == 'forward':
                                match = True
                                break
                if not match:
                        return
                for name, value in attrs:
                        if name == 'value':
                                self.forward_link = value
                                break

        def get_links(self):
                return self.links
        def get_forward_link(self):
                return self.forward_link
