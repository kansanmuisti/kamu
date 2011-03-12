from sgmllib import SGMLParser
import htmlentitydefs

class Parser(SGMLParser):
        def __clear_state(self):
                self.in_desc = False
                self.img_cnt = 0
                return

        def reset(self):
                self.desc = {}
                self.__clear_state()
                SGMLParser.reset(self)
                self.entitydefs = htmlentitydefs.entitydefs
                self.entitydefs['nbsp'] = u'\u0020'

        def start_div(self, attrs):
                for name, value in attrs:
                        if name == 'id' and value == 'main-header':
                                self.in_desc = True
                                break

        def start_img(self, attrs):
                if not self.in_desc:
                        return
#                self.img_cnt += 1
#                if self.img_cnt != 2:
#                        return
                ref = None
                is_logo = False
                for name, value in attrs:
                        if name == 'src':
                                self.desc['logo'] = value
                                break
                self.__clear_state()

        def get_desc(self):
                return self.desc
