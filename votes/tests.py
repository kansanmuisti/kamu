# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core.urlresolvers import reverse
import json

class AutocompleteSearchTest(TestCase):
    fixtures = ['test_keyword', 'test_sessionkeyword', 'test_member']

    def setUp(self):
        qpar_str = u'?query='
        search_kw_url = reverse('votes.views.search_by_keyword') + qpar_str
        search_mb_url = reverse('votes.views.search') + qpar_str

        def query_res(name, exp_url):
            return {
                'name'      : name,
                'url'       : exp_url + name,
            }

        def kw_res(name):
            return query_res(name, search_kw_url)

        def mb_res(name):
            return query_res(name, search_mb_url)

        def query_req(term, exp_url, exp_names):
            if type(exp_names) is not list:
                exp_names = [exp_names]

            return {
                'term'    : term,
                'exp_res' : [query_res(n, exp_url) for n in exp_names],
            }

        def kw_req(term, exp_names):
            return query_req(term, search_kw_url, exp_names)

        def mb_req(term, exp_names):
            return query_req(term, search_mb_url, exp_names)

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
                kw_req('af',                   [u'Afganistan',
                                                  u'Afrikka']),

                # mixed queries returning both members and keywords
                mix_req(u'aa',               [mb_res(u'Aaltonen Markus'),
                                                  kw_res(u'Aasia')]),

                # mixed queries returning all members and keywords limited
                # by max_results
                mix_req(u'',                 [mb_res(u'Aaltonen Markus'),
                                                  kw_res(u'Aasia'),
                                                  kw_res(u'Adoptio'),
                                                  kw_res(u'Afganistan'),
                                                  kw_res(u'Afrikka'),
                                                  mb_res(u'Ahde Matti')]),

                # query returning nothing
                mb_req(u'foobar',             []),
        ]

    def decode_res(self, res):
        dr = json.loads(res)
        # TODO: validate also the thumbnail path which is dynamically generated
        return [{'name': x[0], 'url' : x[2]} for x in dr]

    def run_query(self, term, exp_res):
        req_params = {
                u'name'             : term,
                u'max_results'      : 6,
                u'thumbnail_width'  : 30,
                u'thumbnail_height' : 30,
        }
        autocomplete_url = reverse('votes.views.autocomplete_search')

        err_msg = 'query=' + term + ' expected=' + unicode(exp_res)
        try:
            response = self.client.get(autocomplete_url, req_params)
        except:
            print err_msg
            raise           # Re-raise the exception we're handling

        err_msg_raw = u'(resp_cont=' + response.content + u')'
        self.assertEqual(response.status_code, 200,
                         msg=err_msg + ' ' + err_msg_raw)
        decoded_res = self.decode_res(response.content)
        err_msg = err_msg + ' got=' + unicode(decoded_res) + ' ' + err_msg_raw
        self.assertEqual(decoded_res, exp_res, msg=err_msg)

    def test_queries(self):
        for q in self.queries:
            self.run_query(q['term'], q['exp_res'])


class AutocompleteCountyTest(TestCase):
    fixtures = ['test_county']

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

                c_req(u'As',                 [u'Asikkala',
                                                u'Askola']),

                c_req(u'',                   [u'Akaa',
                                                u'Alajärvi',
                                                u'Alavieska',
                                                u'Alavus',
                                                u'Asikkala',
                                                u'Askola']),
        ]

    def decode_res(self, res):
        return json.loads(res)

    def run_query(self, term, exp_res):
        req_params = {
                u'name'             : term,
                u'max_results'      : 6,
                u'thumbnail_width'  : 30,
                u'thumbnail_height' : 30,
        }
        autocomplete_url = reverse('votes.views.autocomplete_county')

        err_msg = 'query="' + term + '" expected="' + unicode(exp_res) + '"'
        try:
            response = self.client.get(autocomplete_url, req_params)
        except:
            print err_msg
            raise           # Re-raise the exception we're handling

        err_msg_raw = u'(resp_cont="' + response.content + u'")'
        self.assertEqual(response.status_code, 200,
                         msg=err_msg + ' ' + err_msg_raw)
        decoded_res = self.decode_res(response.content)
        err_msg = err_msg + ' got=' + unicode(decoded_res) + ' ' + err_msg_raw
        self.assertEqual(decoded_res, exp_res, msg=err_msg)

    def test_queries(self):
        for q in self.queries:
            self.run_query(q['term'], q['exp_res'])
