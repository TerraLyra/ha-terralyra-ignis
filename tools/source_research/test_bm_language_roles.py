import re
import unittest
from bm_language_roles import annotate_roles
from bm_location_candidates import Settlement

PLACES = tuple(Settlement(n,n) for n in ('Gyöngyös','Hatvan','Dabas','Ócsa'))

def review(text, lemmas=None):
    lemmas = lemmas or {}
    analysis = dict(text=text, entities=[], tokens=[dict(text=m.group(),start=m.start(),end=m.end(),lemma=lemmas.get(m.group(),m.group())) for m in re.finditer(r'\w+|[^\w\s]',text)])
    return annotate_roles(analysis, PLACES)

class RolesTests(unittest.TestCase):
    def test_same_place_has_separate_event_unknown_and_responder_mentions(self):
        r=review('Gyöngyösön ég. A gyöngyösi és hatvani tűzoltók dolgoznak.', {'Gyöngyösön':'Gyöngyös'})
        self.assertEqual([m['roles'][0]['role'] for m in r['mentions']], ['unknown','responder','responder'])
        self.assertIsNone(r['event_location'])
        self.assertFalse(r['incident_location_verified'])

    def test_plain_name_organization_and_negation(self):
        text='Dabas Tűzoltóság érkezett. Nem Dabason, hanem Ócsán ég.'
        r=review(text, {'Dabason':'Dabas','Ócsán':'Ócsa'})
        self.assertEqual([m['roles'][0]['role'] for m in r['mentions']], ['responder','negated','unknown'])
        for m in r['mentions']:
            for role in m['roles']:
                self.assertEqual(text[role['start']:role['end']],role['evidence'])

    def test_no_cross_sentence_or_global_place_exclusion(self):
        r=review('Gyöngyös ég. Hatvan tűzoltósága érkezett.')
        self.assertEqual(r['mentions'][0]['roles'][0]['role'],'unknown')
        self.assertEqual(r['mentions'][1]['roles'][0]['role'],'responder')

    def test_direction_street_and_bad_spans(self):
        r=review('Dabas felé. Hatvan utca.')
        self.assertEqual([m['roles'][0]['role'] for m in r['mentions']],['direction','street'])
        with self.assertRaises(ValueError):
            annotate_roles(dict(text='Dabas',entities=[],tokens=[dict(text='Other',start=0,end=5,lemma='Dabas')]),PLACES)

    def test_fire_engine_is_not_a_firefighter_organization(self):
        r=review('Dabas tűzoltóautója ég.')
        self.assertEqual(r['mentions'][0]['roles'][0]['role'],'unknown')
