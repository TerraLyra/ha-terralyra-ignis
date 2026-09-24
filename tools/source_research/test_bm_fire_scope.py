import unittest
from bm_fire_scope import review_fire_scope


class FireScopeTests(unittest.TestCase):
    def test_vegetation_and_local_are_distinct(self):
        for text, expected in [('Ég a nádas.', 'vegetation_fire_candidate'),
                               ('Erdőtűz pusztít.', 'vegetation_fire_candidate'),
                               ('Kigyulladt egy személyautó.', 'local_asset_fire_candidate'),
                               ('Teljes terjedelmében ég egy ház.', 'local_asset_fire_candidate')]:
            result = review_fire_scope(text, '')
            self.assertEqual(result['category'], expected)
            self.assertFalse(result['automatically_excluded'])
            self.assertFalse(result['large_extent_verified'])

    def test_mixed_and_uncertain_reports_are_retained(self):
        for text, expected in [('Ég egy autó és az aljnövényzet.', 'mixed_fire_candidate'),
                               ('Nem ég az erdő.', 'unknown'),
                               ('Erdőtűz veszélye miatt figyelmeztetnek.', 'unknown'),
                               ('Baleset az erdő közelében.', 'unknown'),
                               ('Ég egy ház. A közelben nádas található.', 'local_asset_fire_candidate')]:
            self.assertEqual(review_fire_scope(text, '')['category'], expected)

    def test_area_is_evidence_not_extent_confirmation(self):
        text = '2,5 hektáron ég a tarló.'
        result = review_fire_scope('', text)
        self.assertEqual(result['category'], 'vegetation_fire_candidate')
        area = [e for e in result['evidence'] if e['kind'] == 'area']
        self.assertEqual(len(area), 1)
        self.assertEqual(area[0]['evidence'], '2,5 hektáron')
        for item in result['evidence']:
            self.assertEqual(text[item['start']:item['end']], item['evidence'])
        self.assertFalse(result['large_extent_verified'])

    def test_truncated_and_nonfire_input(self):
        result = review_fire_scope('Ég az erdő', '', input_truncated=True)
        self.assertEqual(result['category'], 'unknown')
        self.assertEqual(result['evidence'], [])
        self.assertEqual(review_fire_scope('Négyes karambol Debrecenben', '')['category'], 'unknown')


class AccidentScopeTests(unittest.TestCase):
    def test_accidents_with_body_and_responders(self):
        for title in ('Szalagkorlátnak ütközött egy kisbusz az M1-esen',
                      'Egymásnak ütközött két autó Debrecenben',
                      'Parkoló autónak ütközött egy személygépkocsi Veresegyházán'):
            result = review_fire_scope(title, 'A tűzoltók áramtalanították a járműveket.')
            self.assertEqual(result['category'], 'non_fire_report_candidate')
            self.assertFalse(result['automatically_excluded'])
            self.assertTrue(any(e['kind'] == 'accident' for e in result['evidence']))

    def test_fire_or_smoke_anywhere_vetoes_nonfire_label(self):
        for body in ('Kigyulladt egy autó.', 'Füst szállt fel.', 'Eloltották a tüzet.',
                     'Avartűz keletkezett.', 'Lángra kapott a rakomány.',
                     'Nem keletkezett tűz.', 'Oltják a lángokat.', 'Tűzoltás zajlik.'):
            self.assertNotEqual(review_fire_scope('Karambol az úton', body)['category'],
                                'non_fire_report_candidate')

    def test_incomplete_and_ambiguous_stay_unknown(self):
        self.assertEqual(review_fire_scope('Karambol az úton', '')['category'], 'unknown')
        self.assertEqual(review_fire_scope('Karambol az úton', 'Rövid hír', input_truncated=True)['category'], 'unknown')
        self.assertEqual(review_fire_scope('Baleset lehetett', 'A vizsgálat folyik.')['category'], 'unknown')
