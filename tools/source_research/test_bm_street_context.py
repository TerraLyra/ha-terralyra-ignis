"""Street-name ambiguity from RSS 92282; never discard candidate evidence."""
import unittest
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import Settlement, review_locations


class StreetContextTests(unittest.TestCase):
    def test_real_report_separates_town_street_and_responders(self):
        title = 'Két autó ütközött Nyírpazonyban'
        description = 'Két személygépkocsi Nyírpazonyban, a Szabolcs utcában. A nyíregyházi hivatásos tűzoltók áramtalanították a járműveket.'
        result = review_locations(title, description, '', load_review_places())
        town = [m for m in result.mentions if m.settlement_name == 'Nyírpazony']
        self.assertEqual(len(town), 2)
        self.assertTrue(all(not m.context_hints for m in town))
        street, = [m for m in result.mentions if m.settlement_name == 'Szabolcs']
        self.assertEqual(street.context_hints[0].kind, 'street_name_reference')
        responder, = [m for m in result.mentions if m.settlement_name == 'Nyíregyháza']
        self.assertEqual(responder.context_hints[0].kind, 'responder_reference')
        for mention in result.mentions:
            text = {'title': title, 'description': description}[mention.field]
            self.assertEqual(text[mention.start:mention.end], mention.evidence)
            for hint in mention.context_hints:
                self.assertEqual(text[hint.start:hint.end], hint.evidence)
        self.assertFalse(result.incident_location_verified)

    def test_explicit_street_suffixes(self):
        for suffix in ('utcában', 'úton', 'téren', 'közben'):
            text = f'A Szabolcs {suffix} történt.'
            result = review_locations('', text, '', (Settlement('s','Szabolcs'),))
            self.assertEqual(result.mentions[0].context_hints[0].evidence, 'Szabolcs '+suffix)

    def test_no_cross_sentence_line_or_partial_word_match(self):
        for text in ('Szabolcs. Utcában történt.', 'Szabolcs\nutcában',
                     'Szabolcs utcanév', 'Szabolcs közelében', 'Szabolcs útmutató'):
            result = review_locations('', text, '', (Settlement('s','Szabolcs'),))
            self.assertEqual(result.mentions[0].context_hints, ())

    def test_standalone_mention_not_globally_excluded(self):
        result = review_locations('Szabolcs közelében, a Szabolcs utcában.', '', '', (Settlement('s','Szabolcs'),))
        self.assertEqual(len(result.mentions), 2)
        self.assertEqual(result.mentions[0].context_hints, ())
        self.assertEqual(result.mentions[1].context_hints[0].kind, 'street_name_reference')
