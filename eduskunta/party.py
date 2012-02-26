# -*- coding: utf-8 -*-
import re
import os
import logging
from lxml import etree, html
from eduskunta.importer import Importer
from parliament.models.party import Party

PG_MAP = u'''Kansallisen kokoomuksen eduskuntaryhmä /kok
    Sosialidemokraattinen eduskuntaryhmä /sd
    Perussuomalaisten eduskuntaryhmä /ps
    Keskustan eduskuntaryhmä /kesk
    Vasemmistoliiton eduskuntaryhmä /vas
    Ruotsalainen eduskuntaryhmä /r
    Vihreä eduskuntaryhmä /vihr
    Kristillisdemokraattinen eduskuntaryhmä /kd'''
#    Vasenryhmän eduskuntaryhmä /vr'''

def pg_to_party(pg):
    lines = [l.strip().split(' /') for l in PG_MAP.split('\n')]
    for l in lines:
        if l[0] == pg:
            return l[1]
    return None

class PartyImporter(Importer):
    FILENAME = 'parties.txt'

    def import_parties(self):
        path = os.path.dirname(os.path.realpath(__file__))
        f = open(os.path.join(path, self.FILENAME))
        for line in f.readlines():
            line = line.strip().decode('utf8')
            if not line or line[0] == '#':
                continue
            (name, long_name, logo, vis_color) = line.split('\t')
            try:
                party = Party.objects.get(name=name)
                if not self.replace:
                    continue
            except Party.DoesNotExist:
                party = Party(name=name)
            party.full_name = long_name
            self.logger.info(u"importing party %s/%s" % (party.full_name, party.name))
            party.logo = logo
            party.vis_color = vis_color
            party.save()
