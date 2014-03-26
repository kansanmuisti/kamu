# -*- coding: utf-8 -*-
import re
import os
import logging
from lxml import etree, html
from eduskunta.importer import Importer, ParseError
from parliament.models.party import Party, GoverningParty, Government

PG_MAP = u'''Kansallisen kokoomuksen eduskuntaryhmä /kok
    Sosialidemokraattinen eduskuntaryhmä /sd
    Perussuomalaisten eduskuntaryhmä /ps
    Keskustan eduskuntaryhmä /kesk
    Vasemmistoliiton eduskuntaryhmä /vas
    Ruotsalainen eduskuntaryhmä /r
    Vihreä eduskuntaryhmä /vihr
    Kristillisdemokraattinen eduskuntaryhmä /kd
    Muutos 2011 eduskuntaryhmä /m11'''

def pg_to_party(pg):
    lines = [l.strip().split(' /') for l in PG_MAP.split('\n')]
    for l in lines:
        if l[0] == pg:
            return l[1]
    return None

class PartyImporter(Importer):
    FILENAME = 'parties.txt'
    GOVS_FILENAME = 'governments.txt'
    GPS_FILENAME = 'governingparties.txt'

    def import_parties(self):
        path = os.path.dirname(os.path.realpath(__file__))
        f = open(os.path.join(path, self.FILENAME))
        for line in f.readlines():
            line = line.strip().decode('utf8')
            if not line or line[0] == '#':
                continue
            (abbr, long_name, logo, vis_color) = line.split('\t')
            try:
                party = Party.objects.get(abbreviation=abbr)
                if not self.replace:
                    continue
            except Party.DoesNotExist:
                party = Party(abbreviation=abbr)
            party.name = long_name
            self.logger.info(u"importing party %s/%s" % (party.name, party.abbreviation))
            party.logo = logo
            party.vis_color = vis_color
            party.save()

    def import_governments(self):
        path = os.path.dirname(os.path.realpath(__file__))
        f = open(os.path.join(path, self.GOVS_FILENAME))
        for line in f.readlines():
            line = line.strip().decode('utf8')
            if not line or line[0] == '#':
                continue
            (name, begin, end) = line.split('\t')
            try:
                gov = Government.objects.get(name=name)
                if not self.replace:
                    continue
            except Government.DoesNotExist:
                gov = Government(name=name, begin=begin)
            gov.begin = begin
            if end == "None":
                gov.end = None
            else:
                gov.end = end
            self.logger.info(u"importing government %s / %s - %s" % (gov.name, gov.begin, gov.end))
            gov.save()

    def import_governingparties(self):
        """ This requires that governments & parties have already been imported """
        path = os.path.dirname(os.path.realpath(__file__))
        f = open(os.path.join(path, self.GPS_FILENAME))
        for line in f.readlines():
            line = line.strip().decode('utf8')
            if not line or line[0] == '#':
                continue
            (party, government, begin, end) = line.split('\t')
            try:
                party = Party.objects.get(abbreviation=party)
            except Party.DoesNotExist:
                raise ParseError('Invalid party %s in initial governing party data' % party)
            try:
                government = Government.objects.get(name=government)
            except Government.DoesNotExist:
                raise ParseError('Invalid government %s in initial governing party data' % government)
            try:
                gp = GoverningParty.objects.get(party=party, government=government)
                if not self.replace:
                    continue
            except GoverningParty.DoesNotExist:
                gp = GoverningParty(party=party, government=government)
            gp.begin=begin
            if end == "None":
                gp.end = None
            else:
                gp.end = end
            self.logger.info(u"importing governing party %s / %s - %s" % (gp.party, gp.begin, gp.end))
            gp.save()
