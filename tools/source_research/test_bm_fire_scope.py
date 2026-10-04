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


class SpreadingFireTests(unittest.TestCase):
    def test_vehicle_fire_spreading_to_brush_is_mixed(self):
        title = 'Tűz volt Sámsonházán'
        text = 'Kigyulladt egy lakókocsi. A tűz a bozótosra is átterjedt.'
        result = review_fire_scope(title, text)
        self.assertEqual(result['category'], 'mixed_fire_candidate')
        self.assertFalse(result['large_extent_verified'])
        self.assertFalse(result['automatically_excluded'])
        for item in result['evidence']:
            original = title if item['field'] == 'title' else text
            self.assertEqual(original[item['start']:item['end']], item['evidence'])

    def test_negated_spread_is_not_promoted(self):
        result = review_fire_scope('', 'Kigyulladt egy lakókocsi. A tűz nem terjedt át a bozótosra.')
        self.assertEqual(result['category'], 'unknown')

    def test_unrelated_vegetation_sentence_is_not_spread(self):
        result = review_fire_scope('', 'Kigyulladt egy lakókocsi. A bozótosra rálátni.')
        self.assertEqual(result['category'], 'local_asset_fire_candidate')


class PossessiveResponderTests(unittest.TestCase):
    def test_observed_possessive_responder_is_not_fire_evidence(self):
        title = 'Villanyoszlopnak ütközött egy autó a XVIII. kerületben'
        body = 'A fővárosi hivatásos tűzoltók és a Foka ÖTE önkéntes tűzoltói érkeztek a helyszínre, áramtalanították az autót.'
        result = review_fire_scope(title, body)
        self.assertEqual(result['category'], 'non_fire_report_candidate')
        self.assertFalse(any(e['kind'] == 'possible_fire' for e in result['evidence']))
        self.assertFalse(result['automatically_excluded'])
        self.assertTrue(result['requires_review'])

    def test_responder_form_does_not_hide_real_fire_clues(self):
        for clue in ('Füst szállt fel.', 'Tűzoltás zajlik.', 'Kigyulladt egy autó.',
                     'A tűzoltóautó kigyulladt.', 'Nem keletkezett tűz.'):
            with self.subTest(clue=clue):
                body = 'Az önkéntes tűzoltói megérkeztek. ' + clue
                result = review_fire_scope('Baleset az úton', body)
                self.assertNotEqual(result['category'], 'non_fire_report_candidate')
                for evidence in result['evidence']:
                    text = body if evidence['field'] == 'description' else 'Baleset az úton'
                    self.assertEqual(text[evidence['start']:evidence['end']], evidence['evidence'])


class SeparatedIgnitionTests(unittest.TestCase):
    def test_mixed_ignition_and_negation(self):
        body = 'Egy melléképület és az aljnövényzet gyulladt ki.'
        result = review_fire_scope('Műhely ég', body)
        self.assertEqual(result['category'], 'mixed_fire_candidate')
        self.assertTrue(any(e['evidence'] == 'gyulladt ki' for e in result['evidence']))
        self.assertFalse(result['large_extent_verified'])
        self.assertEqual(review_fire_scope('', 'Az aljnövényzet nem gyulladt ki.')['category'], 'unknown')
        self.assertEqual(review_fire_scope('', 'Az aljnövényzet gyulladt. Ki érkezett?')['category'], 'unknown')
