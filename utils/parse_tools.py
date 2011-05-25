#!/usr/bin/python
# -*- coding: utf-8 -*-

MEMBER_NAME_TRANSFORMS = {
    'Korhonen Timo': 'Korhonen Timo V.',
    'Ollila Heikki': 'Ollila Heikki A.',
    'Saarela Tanja': 'Karpela Tanja',
    'Kumpula Miapetra': 'Kumpula-Natri Miapetra',
    'Forsius-Harkimo Merikukka': 'Forsius Merikukka',
    'Taberman Tommy': 'Tabermann Tommy',
    'Harkimo Leena-Kaisa': 'Harkimo Leena',
    'Packalen Tom': 'Packalén Tom',
    'Virtanen Pertti "Veltto"': 'Virtanen Pertti',
    'Elomaa Kike': 'Elomaa Ritva',
    'Maijala Eeva-Maria': 'Maijala Eeva Maria',
    'Gästgivars Lars': 'Gästgivars Lars Erik',
}

def fix_mp_name(name):
    if not isinstance(name, unicode):
	name = name.decode('utf8')
    if name.encode('utf8') in MEMBER_NAME_TRANSFORMS:
        name = MEMBER_NAME_TRANSFORMS[name.encode('utf8')].decode('utf8')
    return name

