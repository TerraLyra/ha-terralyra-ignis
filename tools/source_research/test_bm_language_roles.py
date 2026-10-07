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

    def test_unknown_member_does_not_break_qualified_list(self):
        text='A gyöngyösi, az ismeretlenfalvi létesítményi és a hatvani önkéntes tűzoltók dolgoznak.'
        r=review(text)
        self.assertEqual([m['evidence'] for m in r['mentions']],['gyöngyösi','ismeretlenfalvi','hatvani'])
        self.assertTrue(all(any(h['role']=='responder' for h in m['roles']) for m in r['mentions']))
        self.assertEqual(r['mentions'][1]['settlements'],[])
        self.assertIsNone(r['event_location'])
        for m in r['mentions']:
            for h in m['roles']:
                self.assertEqual(text[h['start']:h['end']],h['evidence'])

    def test_shared_list_cannot_cross_sentence_or_nonresponder_noun(self):
        for text in ['A gyöngyösi és hatvani házak égnek.',
                     'A gyöngyösi házak égnek. A hatvani tűzoltók érkeztek.',
                     'A gyöngyösi, a hatvani épület mellett tűzoltók állnak.']:
            r=review(text)
            self.assertEqual(r['mentions'][0]['roles'][0]['role'],'unknown')

    def test_between_places_preserves_corridor_without_coordinates(self):
        text='Gyöngyös és Hatvan között ég a fű.'
        r=review(text)
        self.assertEqual(len(r['corridors']),1)
        self.assertEqual(r['corridors'][0]['endpoints'],[['Gyöngyös'],['Hatvan']])
        self.assertFalse(r['corridors'][0]['incident_geometry_verified'])
        self.assertIsNone(r['event_location'])
        self.assertTrue(all(m['roles'][0]['role']=='between_places' for m in r['mentions']))
        c=r['corridors'][0]
        self.assertEqual(text[c['start']:c['end']],c['evidence'])

    def test_corridor_does_not_override_other_context_or_cross_unknown_text(self):
        for text in ['Nem Gyöngyös és Hatvan között ég.',
                     'Gyöngyös és Hatvan utca között.',
                     'Gyöngyös ég. És Hatvan között.',
                     'Gyöngyös és Ismeretlenfalva között.',
                     'Gyöngyös és Hatvan tűzoltósága között egyeztetnek.']:
            self.assertEqual(review(text)['corridors'],[],text)
