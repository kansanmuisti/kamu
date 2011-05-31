# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
import json

class AutocompleteTestCase(TestCase):
    def run_query(self, term, exp_res, exp_code=200, req_opts={}):
        req_pars = self.req_params.copy()
        req_pars.update(req_opts)
        req_pars[u'name'] = term

        err_msg = 'query=' + term
        err_msg += ' exp_code=' + unicode(exp_code)
        err_msg += ' exp_res=' + unicode(exp_res)
        try:
            response = self.client.get(self.req_url, req_pars)
        except:
            print err_msg
            raise           # Re-raise the exception we're handling

        err_msg_raw = u'(resp_code=' + unicode(response.status_code)
        err_msg_raw += ' resp_raw=' + response.content + u')'
        self.assertEqual(response.status_code, exp_code,
                         msg=err_msg + ' ' + err_msg_raw)

        if (exp_res is None):
            return

        decoded_res = self.decode_res(response.content)
        err_msg = err_msg + ' res=' + unicode(decoded_res) + ' ' + err_msg_raw
        self.assertEqual(decoded_res, exp_res, msg=err_msg)

class AutocompleteSearchTest(AutocompleteTestCase):
    fixtures = ['test_keyword', 'test_session', 'test_member']
    req_url = reverse('votes.views.autocomplete_search')
    req_params = {
            u'max_results'      : 6,
            u'thumbnail_width'  : 30,
            u'thumbnail_height' : 30,
    }

    def setUp(self):
        qpar_str = u'?query='

        def kw_url_res(kw):
            return reverse(u'votes.views.search_by_keyword') + u'?query=' + kw

        def mb_url_res(mb):
            return reverse(u'votes.views.show_member',
                           kwargs={'member':slugify(mb)})

        def query_res(name, exp_url):
            return {
                'name'      : name,
                'url'       : exp_url,
            }

        def kw_res(name):
            return query_res(name, kw_url_res(name))

        def mb_res(name):
            return query_res(name, mb_url_res(name))

        def kw_req(term, exp_names):
            if type(exp_names) is not list:
                exp_names = [exp_names]
            return {
                'term'    : term,
                'exp_res' : [query_res(n, kw_url_res(n)) for n in exp_names]
            }

        def mb_req(term, exp_names):
            if type(exp_names) is not list:
                exp_names = [exp_names]
            return {
                'term'    : term,
                'exp_res' : [query_res(n, mb_url_res(n)) for n in exp_names]
            }

        def mix_req(term, exp_results):
            return {
                'term'    : term,
                'exp_res' : exp_results,
            }

        self.queries = [
                # member queries returning a single result
                mb_req(u'aalto',               u'Aaltonen Markus'),
                mb_req(u'Markus ',             u'Aaltonen Markus'),
                mb_req(u' Aaltonen   Markus ', u'Aaltonen Markus'),
                mb_req(u'ala-nissilä',         [u'Ala-Nissilä Olavi']),

                # keyword queries returning a single result
                kw_req(u'aasia',               u'Aasia'),
                kw_req(u'Aasia ',              u'Aasia'),
                kw_req(u' Aasia ',             u'Aasia'),
                kw_req(u'ja rahoitus- kehittä',
                                u'Asumisen rahoitus- ja kehittämiskeskus'),

                # member queries returning multiple results
                mb_req(u'aho',                 [u'Aho Esko',
                                                  u'Aho Hannu',
                                                  u'Ahonen Esko']),

                # keyword queries returning multiple results
                kw_req('f',                    [u'Finanssivalvonta',
                                                  u'Fortum']),

                # mixed queries returning both members and keywords
                mix_req(u'aa',               [mb_res(u'Aaltonen Markus'),
                                                  kw_res(u'Aasia')]),

                # mixed queries returning all members and keywords limited
                # by max_results
                mix_req(u'',                 [mb_res(u'Aaltonen Markus'),
                                                  kw_res(u'Aasia'),
                                                  kw_res(u'Adoptio'),
                                                  kw_res(u'Afrikka'),
                                                  mb_res(u'Ahde Matti'),
                                                  mb_res(u'Aho Esko')]),

                # query returning nothing
                mb_req(u'aa ',                []),
                mb_req(u'foobar',             []),
        ]

    def decode_res(self, res):
        dr = json.loads(res)
        # TODO: validate also the thumbnail path which is dynamically generated
        return [{'name': x[0], 'url' : x[2]} for x in dr]


    def test_queries(self):
        for q in self.queries:
            self.run_query(q['term'], q['exp_res'])

        # queries resulting in an HTTP bad-request response
        self.run_query(u'1 2 3 4 5 6 7 8 9 10 11', None, exp_code=400)
        self.run_query(u'1', None, exp_code=400, req_opts={'max_results':101})
        self.run_query(u'1', None, exp_code=400,
                       req_opts={'thumbnail_width':81})

class AutocompleteCountyTest(AutocompleteTestCase):
    fixtures = ['test_county']
    req_url = reverse('votes.views.autocomplete_county')
    req_params = {
            u'max_results'      : 6,
    }

    def setUp(self):
        def c_req(term, exp_counties):
            if type(exp_counties) is not list:
                exp_counties = [exp_counties]

            return {
                'term'    : term,
                'exp_res' : [[c] for c in exp_counties]
            }

        self.queries = [
                c_req(u'Akaa',               u'Akaa'),
                c_req(u'alajärvi',           u'Alajärvi'),
                c_req(u'alajärvi  ',         u'Alajärvi'),
                c_req(u'Pedersören ',        u'Pedersören kunta'),
                c_req(u' kunt',              u'Pedersören kunta'),

                c_req(u'As',                 [u'Asikkala',
                                                u'Askola']),

                c_req(u'',                   [u'Akaa',
                                                u'Alajärvi',
                                                u'Alavieska',
                                                u'Alavus',
                                                u'Asikkala',
                                                u'Askola']),

                c_req(u'as ',                []),
                c_req(u'foobar',             []),
        ]

    def decode_res(self, res):
        return json.loads(res)

    def test_queries(self):
        for q in self.queries:
            self.run_query(q['term'], q['exp_res'])

        # queries resulting in an HTTP bad-request response
        self.run_query(u'1 2 3 4 5 6 7 8 9 10 11', None, exp_code=400)
        self.run_query(u'1', None, exp_code=400, req_opts={'max_results':501})
