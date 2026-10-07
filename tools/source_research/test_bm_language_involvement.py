import re
import unittest
from bm_language_involvement import review_involvement


def review(text, lemmas):
    return review_involvement(dict(text=text,tokens=[dict(text=m.group(), start=m.start(),end=m.end(),lemma=lemmas.get(m.group(),m.group()).lower()) for m in re.finditer(r'\w+',text)]))

class InvolvementTests(unittest.TestCase):
    def test_spread_and_extinguishing_preserve_multiple_categories(self):
        text='Aljnövényzetről melléképületre terjedt a tűz. A lángokat elfojtották.'
        r=review(text,{'Aljnövényzetről':'aljnövényzet','melléképületre':'melléképület','terjedt':'terjed','lángokat':'láng','elfojtották':'elfojt'})
        self.assertEqual(r['involvement'],['building','vegetation'])
        self.assertTrue(r['reported_extinguishing'])
        self.assertFalse(r['current_status_verified'])
        for e in r['evidence']:
            self.assertEqual(text[e['start']:e['end']],e['evidence'])

    def test_threat_and_negative_ignition_do_not_become_burning_building(self):
        r=review('A fű ég, egy épületet veszélyeztet, de az épület nem gyulladt ki.',{'épületet':'épület','gyulladt':'gyullad'})
        self.assertEqual(r['involvement'],['vegetation'])
        self.assertEqual(r['threatened'],['building'])

    def test_negation_and_unknown_do_not_promote(self):
        for text in ['Az épület nem ég.', 'Az épület közelében tűzoltók állnak.']:
            self.assertEqual(review(text,{})['involvement'],[])
        r=review('A lángokat nem oltották el.',{'lángokat':'láng','oltották':'elolt'})
        self.assertFalse(r['reported_extinguishing'])

    def test_nonfire_creation_and_hypothetical_do_not_promote(self):
        self.assertEqual(review('Az épületben kár keletkezett.',{'épületben':'épület','keletkezett':'keletkezik'})['involvement'],[])
        self.assertEqual(review('Az épület éghet volna.',{'éghet':'ég'})['involvement'],[])
