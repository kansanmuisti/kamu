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
    # funding 2011
    'Modig Anna': 'Modig Silvia',
    'Wallinheimo Mika': 'Wallinheimo Sinuhe',
    'Huovinen Krista': 'Huovinen Susanna',
    'Stubb Cai-Göran': 'Stubb Alexander',
    'Anttila Sirkka': 'Anttila Sirkka-Liisa',
    'Viitanen Pia-Liisa': 'Viitanen Pia',
    'Vikman Maria': 'Vikman Sofia',
    'Väätäinen Toivo': 'Väätäinen Juha',
    'Pekkarinen Reijo': 'Pekkarinen Mauri',
    'Koskinen Hannu': 'Koskinen Johannes',
    'Jungner Juhani': 'Jungner Mikael',
    'Wideroos Cecilia': 'Wideroos Ulla-Maj',
    'Maijala Eeva': 'Maijala Eeva Maria',
    'Nauclér Charlotte': 'Nauclér Elisabeth',
    'Kiljunen Leila': 'Kiljunen Anneli',
    'Joutsenlahti Juha': 'Joutsenlahti Anssi',
    'Gestrin Anna': 'Gestrin Christina',
    'Mäkinen Heikki': 'Mäkinen Tapani',
    'Jääskeläinen Osmo': 'Jääskeläinen Pietari',
    'Viitamies Johanna': 'Viitamies Pauliina',
    'Kerola Eeva': 'Kerola Inkeri',
    'Orpo Antti': 'Orpo Petteri',
    'Hiltunen Lea': 'Hiltunen Rakel',
    'Tolppanen Eeva': 'Tolppanen Maria',
}

def fix_mp_name(name):
    if not isinstance(name, str):
	name = name.decode('utf8')
    if name.encode('utf8') in MEMBER_NAME_TRANSFORMS:
        name = MEMBER_NAME_TRANSFORMS[name.encode('utf8')].decode('utf8')
    return name

