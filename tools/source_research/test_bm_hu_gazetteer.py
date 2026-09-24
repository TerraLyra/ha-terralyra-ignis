"""Country filtering, stable identity and evidence-only matching regressions."""
import sqlite3
import tempfile
from pathlib import Path
import unittest
import zipfile

from bm_hu_gazetteer import build, load_places, load_review_places
from bm_bundled_places import load_hungarian_places
from bm_location_candidates import MAX_SETTLEMENTS, Settlement, review_locations


def row(identifier, name, code='PPL', country='HU'):
    return '\t'.join([str(identifier), name, '', '', '47', '19', 'P', code,
                      country, '', '01', '', '', '', '0', '', '', 'Europe/Budapest', '2026-09-24'])


class HungarianGazetteerTests(unittest.TestCase):
    def test_filter_and_homonyms_keep_upstream_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory)/'HU.zip', Path(directory)/'names.sqlite3'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('HU.txt', '\n'.join([
                    row(1, 'Gersekarát'), row(2, 'Gersekarát'),
                    row(3, 'Historical', 'PPLH'), row(4, 'Part', 'PPLX'),
                    row(5, 'Foreign', country='AT'), row(6, 'Somlóvásárhely')]))
            build(source, target)
            places = load_places(target)
            self.assertEqual([p.identifier for p in places], ['geonames:1','geonames:2','geonames:6'])
            review = review_locations('Tűz Gersekaráton', '', '', places)
            self.assertTrue(review.multiple_candidates)
            self.assertFalse(review.incident_location_verified)
            self.assertEqual([m.evidence for m in review.mentions], ['Gersekaráton']*2)
            before = target.read_bytes()
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('HU.txt', row(1, 'A')+'\n'+row(1, 'B'))
            with self.assertRaises(sqlite3.IntegrityError):
                build(source, target)
            self.assertEqual(target.read_bytes(), before)

    def test_bundled_expansion_recognizes_both_missing_names(self):
        places = load_places()
        self.assertGreater(len(places), 5000)
        review = review_locations('Gersekaráton', 'Somlóvásárhelyen', '', places)
        self.assertEqual({m.settlement_name for m in review.mentions}, {'Gersekarát', 'Somlóvásárhely'})
        self.assertFalse(review.incident_location_verified)
        for mention in review.mentions:
            self.assertEqual(getattr(review, mention.field)[mention.start:mention.end], mention.evidence)

    def test_expansion_retains_existing_name_coverage(self):
        combined = load_review_places()
        self.assertTrue({p.name for p in load_hungarian_places()} <= {p.name for p in combined})
        self.assertEqual(len({p.identifier for p in combined}), len(combined))

    def test_bound_is_enforced_without_truncation(self):
        with self.assertRaises(ValueError):
            review_locations('', '', '', (Settlement('a', 'A'),)*(MAX_SETTLEMENTS+1))
