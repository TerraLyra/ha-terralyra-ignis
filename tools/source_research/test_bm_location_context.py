"""Synthetic context clues; all candidate evidence remains review-only."""
import unittest
from bm_location_candidates import Settlement, review_locations

PLACES = (Settlement('k','Komárom'),Settlement('e','Esztergom'),
          Settlement('t','Tatabánya',('tatabányai',)),
          Settlement('v','Vértesszőlős',('vértesszőlősi',)))

class ContextTests(unittest.TestCase):
    def result(self, text):
        return review_locations('', text, '', PLACES)

    def test_compound_county_keeps_both_mentions_with_exact_context(self):
        for dash in ('-', '–'):
            text = f'A Komárom{dash}Esztergom vármegyei szolgálat.'
            result = self.result(text)
            self.assertEqual(len(result.mentions), 2)
            for mention in result.mentions:
                hint, = mention.context_hints
                self.assertEqual(hint.kind, 'county_name')
                self.assertEqual(text[hint.start:hint.end], hint.evidence)
            self.assertFalse(result.incident_location_verified)

    def test_direct_responder_reference(self):
        result = self.result('A tatabányai hivatásos tűzoltók megérkeztek.')
        hint, = result.mentions[0].context_hints
        self.assertEqual(hint.kind, 'responder_reference')
        self.assertEqual(hint.evidence, 'tatabányai hivatásos tűzoltók')

    def test_event_adjective_does_not_become_responder(self):
        result = self.result('Egy vértesszőlősi házban tűz keletkezett.')
        self.assertEqual(result.mentions[0].context_hints, ())
        self.assertFalse(result.incident_location_verified)

    def test_separate_city_and_county_mentions(self):
        result = self.result('Komárom közelében, Komárom-Esztergom vármegyében.')
        self.assertEqual(result.mentions[0].context_hints, ())
        self.assertEqual(result.mentions[1].context_hints[0].kind, 'county_name')

    def test_no_cross_sentence_responder_hint(self):
        self.assertEqual(self.result('Tatabányai. Tűzoltók érkeztek.').mentions[0].context_hints, ())

    def test_unknown_context_stays_unknown(self):
        result = self.result('Nem Esztergom a helyszín.')
        self.assertEqual(result.mentions[0].context_hints, ())
        self.assertEqual(result.status, 'requires_review')

class ResponderListTests(unittest.TestCase):
    places = (Settlement('n','Nyíradony',('nyíradonyi',)),
              Settlement('b','Nyírbátor',('nyírbátori',)),
              Settlement('d','Debrecen',('debreceni',)))

    def review(self, value):
        return review_locations('', value, '', self.places)

    def test_all_members_keep_shared_evidence(self):
        text = 'Nyíradonyi, nyírbátori és debreceni hivatásos egységeket riasztottak.'
        result = self.review(text)
        self.assertEqual(len(result.mentions), 3)
        for mention in result.mentions:
            hints = [h for h in mention.context_hints if h.kind == 'responder_list_reference']
            self.assertEqual(len(hints), 1)
            self.assertEqual(text[hints[0].start:hints[0].end], hints[0].evidence)
        self.assertFalse(result.incident_location_verified)

    def test_conjunction_variants(self):
        for join in (', ', ' és ', ', illetve ', ' illetve '):
            result = self.review('Nyíradonyi' + join + 'debreceni tűzoltók érkeztek.')
            self.assertTrue(all(any(h.kind == 'responder_list_reference' for h in m.context_hints) for m in result.mentions))

    def test_unknown_member_blocks_propagation(self):
        result = self.review('Nyíradonyi, ismeretleni és debreceni tűzoltók érkeztek.')
        self.assertEqual(result.mentions[0].context_hints, ())

    def test_sentence_boundary_and_other_noun_block_propagation(self):
        for text in ('Nyíradonyi. Debreceni tűzoltók érkeztek.',
                     'Nyíradonyi és debreceni házak égtek.'):
            self.assertFalse(any(h.kind == 'responder_list_reference' for m in self.review(text).mentions for h in m.context_hints))

    def test_standalone_event_mention_is_preserved(self):
        result = self.review('Nyíradony határában ég. Nyíradonyi és debreceni tűzoltók érkeztek.')
        self.assertEqual(result.mentions[0].evidence, 'Nyíradony')
        self.assertEqual(result.mentions[0].context_hints, ())


class CommonWordTests(unittest.TestCase):
    places = (Settlement('n', 'Négyes', ('Négyesen', 'négyesi')),
              Settlement('d', 'Debrecen', ('Debrecenben',)))

    def test_collision_count_is_flagged_without_deleting_evidence(self):
        for text in ('Négyes karambol Debrecenben', 'NÉGYES KARAMBOL Debrecenben'):
            result = review_locations(text, '', '', self.places)
            mention = next(m for m in result.mentions if m.settlement_id == 'n')
            hint, = mention.context_hints
            self.assertEqual(hint.kind, 'possible_vehicle_count')
            self.assertEqual(text[hint.start:hint.end], hint.evidence)
            self.assertEqual(text[mention.start:mention.end], mention.evidence)
            self.assertTrue(result.multiple_candidates)
            self.assertFalse(result.incident_location_verified)

    def test_real_settlement_occurrences_remain_candidates(self):
        for text in ('Négyes közelében karambol történt.', 'Négyesen történt baleset.',
                     'A négyesi úton történt karambol.', 'Négyes. Karambol Debrecenben.',
                     'Négyes\nkarambol', 'Négyes karambolos'):
            result = review_locations(text, '', '', self.places)
            mention = next(m for m in result.mentions if m.settlement_id == 'n')
            if text == 'A négyesi úton történt karambol.':
                self.assertEqual(mention.context_hints[0].kind, 'street_name_reference')
            else:
                self.assertEqual(mention.context_hints, ())
            self.assertFalse(result.incident_location_verified)

    def test_count_and_town_in_one_report_keep_separate_context(self):
        result = review_locations('Négyes karambol Négyesen', '', '', self.places)
        self.assertEqual(len(result.mentions), 2)
        self.assertEqual(result.mentions[0].context_hints[0].kind, 'possible_vehicle_count')
        self.assertEqual(result.mentions[1].context_hints, ())


class MixedResponderListTests(unittest.TestCase):
    places = (Settlement('a', 'Ajka', ('ajkai',)),
              Settlement('s', 'Somlóvásárhely', ('somlóvásárhelyi',)))

    def review(self, text):
        return review_locations('', text, '', self.places)

    def test_shared_noun_with_individual_qualifiers(self):
        for text in ('Az ajkai hivatásos és a somlóvásárhelyi önkéntes tűzoltókat riasztották.',
                     'Ajkai önkormányzati, illetve somlóvásárhelyi önkéntes egységek érkeztek.'):
            result = self.review(text)
            self.assertEqual(len(result.mentions), 2)
            for mention in result.mentions:
                hints = [h for h in mention.context_hints if h.kind == 'responder_list_reference']
                self.assertEqual(len(hints), 1)
                self.assertEqual(text[hints[0].start:hints[0].end], hints[0].evidence)
            self.assertFalse(result.incident_location_verified)

    def test_boundaries_unknown_members_and_other_nouns(self):
        for text in ('Ajkai hivatásos. Somlóvásárhelyi önkéntes tűzoltók.',
                     'Ajkai hivatásos és\na somlóvásárhelyi önkéntes tűzoltók.',
                     'Ajkai hivatásos és ismeretleni önkéntes tűzoltók.',
                     'Ajkai hivatásos és somlóvásárhelyi önkéntes sportolók.',
                     'Ajkai házak és somlóvásárhelyi önkéntes tűzoltók.'):
            self.assertFalse(any(h.kind == 'responder_list_reference'
                                 for m in self.review(text).mentions for h in m.context_hints))

    def test_event_mention_outside_list_stays_unmarked(self):
        result = self.review('Somlóvásárhely közelében dolgoznak az ajkai hivatásos és a somlóvásárhelyi önkéntes tűzoltók.')
        self.assertEqual(result.mentions[0].evidence, 'Somlóvásárhely')
        self.assertEqual(result.mentions[0].context_hints, ())
        self.assertTrue(result.multiple_candidates)
        self.assertFalse(result.incident_location_verified)


class TransportRouteTests(unittest.TestCase):
    places = (Settlement('b', 'Berettyóújfalu', ('Berettyóújfalun',)),
              Settlement('k', 'Biharkeresztes'),
              Settlement('p', 'Püspökladány', ('Püspökladányba',)))

    def review(self, text):
        return review_locations('', text, '', self.places)

    def test_destination_context_with_unlisted_foreign_origin(self):
        text = 'A Nagyváradról Püspökladányba tartó vonat Berettyóújfalun megállt.'
        result = self.review(text)
        destination = next(m for m in result.mentions if m.settlement_id == 'p')
        hint, = destination.context_hints
        self.assertEqual(hint.kind, 'transport_route_reference')
        self.assertEqual(text[hint.start:hint.end], hint.evidence)
        self.assertEqual(hint.evidence, 'Nagyváradról Püspökladányba tartó vonat')
        self.assertEqual(next(m for m in result.mentions if m.settlement_id == 'b').context_hints, ())
        self.assertEqual(len(result.mentions), 2)
        self.assertFalse(result.incident_location_verified)

    def test_repeated_town_event_and_bus_route_are_distinct(self):
        text = 'Berettyóújfalun történt. Berettyóújfalu és Biharkeresztes között pótlóbuszokkal közlekednek.'
        result = self.review(text)
        self.assertEqual(result.mentions[0].context_hints, ())
        for mention in result.mentions[1:]:
            hint, = mention.context_hints
            self.assertEqual(hint.kind, 'transport_route_reference')
            self.assertEqual(text[hint.start:hint.end], hint.evidence)
        self.assertTrue(result.multiple_candidates)
        self.assertFalse(result.incident_location_verified)

    def test_between_towns_without_transport_stays_unclassified(self):
        for text in ('Berettyóújfalu és Biharkeresztes között tűz keletkezett.',
                     'Berettyóújfalu és Biharkeresztes között. Pótlóbuszok járnak.',
                     'Berettyóújfalu és Biharkeresztes között\npótlóbuszok járnak.',
                     'Nagyváradról Püspökladányba tartó. Vonat érkezett.',
                     'Nagyváradról Püspökladányba tartó vonatvezető.'):
            self.assertFalse(any(h.kind == 'transport_route_reference'
                                 for m in self.review(text).mentions for h in m.context_hints))

    def test_truncation_never_extracts_route_candidates(self):
        result = review_locations('', 'Berettyóújfalu és Biharkeresztes között pótlóbuszok',
                                  '', self.places, input_truncated=True)
        self.assertEqual(result.mentions, ())
