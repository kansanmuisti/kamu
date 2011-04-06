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
            return { 'name' : name, 'url' : exp_url + name }

        def kw_res(name):
            return query_res(name, search_kw_url)

        def mb_res(name):
            return query_res(name, search_mb_url)

        def query_item(term, exp_url, exp_names):
            if type(exp_names) is not list:
                exp_names = [exp_names]

            return {
                'term'    : term,
                'exp_res' : [query_res(n, exp_url) for n in exp_names]
            }

        def kw_query(term, exp_names):
            return query_item(term, search_kw_url, exp_names)

        def mb_query(term, exp_names):
            return query_item(term, search_mb_url, exp_names)

        def mixed_query(term, exp_results):
            return {
                'term'    : term,
                'exp_res' : exp_results
            }

        self.queries = [
                # member queries returning a single result
                mb_query(u'aalto',               u'Aaltonen Markus'),
                mb_query(u'Markus ',             u'Aaltonen Markus'),
                mb_query(u' Aaltonen   Markus ', u'Aaltonen Markus'),
                mb_query(u'ala-nissilä',         [u'Ala-Nissilä Olavi']),

                # keyword queries returning a single result
                kw_query(u'aasia',               u'Aasia'),
                kw_query(u'Aasia ',              u'Aasia'),
                kw_query(u' Aasia ',             u'Aasia'),
                kw_query(u'ja rahoitus- kehittä',
                                u'Asumisen rahoitus- ja kehittämiskeskus'),

                # member queries returning multiple results
                mb_query(u'aho',                 [u'Aho Esko',
                                                  u'Aho Hannu',
                                                  u'Ahonen Esko']),

                # keyword queries returning multiple results
                kw_query('af',                   [u'Afganistan',
                                                  u'Afrikka']),

                # mixed queries returning both members and keywords
                mixed_query(u'aa',               [mb_res(u'Aaltonen Markus'),
                                                  kw_res(u'Aasia')]),

                # mixed queries returning all members and keywords limited
                # by max_results
                mixed_query(u'',                 [mb_res(u'Aaltonen Markus'),
                                                  kw_res(u'Aasia'),
                                                  kw_res(u'Adoptio'),
                                                  kw_res(u'Afganistan'),
                                                  kw_res(u'Afrikka'),
                                                  mb_res(u'Ahde Matti')]),
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

