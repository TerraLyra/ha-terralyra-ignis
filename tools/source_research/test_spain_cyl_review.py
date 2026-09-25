import json
import unittest
from spain_cyl_review import inspect_response


class SpainReviewTests(unittest.TestCase):
    def review(self, row):
        return inspect_response(json.dumps({'total_count': 10, 'results': [row]}).encode())

    def test_partial_response_is_not_complete(self):
        result = self.review({'termino_municipal': 'Town'})
        self.assertFalse(result['response_complete'])
        self.assertFalse(result['results'][0]['incident_id_verified'])

    def test_conflict_retains_original_data(self):
        row = {'termino_municipal': 'Town', 'situacion_actual': 'CONTROLADO',
               'fecha_extinguido': '2026-09-17', 'hora_extinguido': '14:03'}
        result = self.review(row)['results'][0]
        self.assertEqual(result['source'], row)
        self.assertIn('extinction_time_status_conflict', result['issues'])

    def test_no_incident_is_not_promoted(self):
        result = self.review({'termino_municipal': 'SIN INCIDENCIAS'})['results'][0]
        self.assertEqual(result['record_kind'], 'no_incident_notice')
        self.assertFalse(result['incident_location_verified'])

    def test_coordinate_bounds_and_semantics(self):
        for point, issue in (({'lat': 41, 'lon': -4}, 'geometry_semantics_unverified'),
                             ({'lat': 91, 'lon': 0}, 'invalid_geometry'),
                             ({'lat': True, 'lon': 0}, 'invalid_geometry')):
            self.assertIn(issue, self.review({'posicion': point})['results'][0]['issues'])

    def test_times_and_dst_are_not_guessed(self):
        for day in ('2026-03-29', '2026-10-25'):
            result = self.review({'fecha_del_parte': day, 'hora_del_parte': '02:30'})['results'][0]
            self.assertFalse(result['timestamp_semantics_verified'])
            self.assertEqual(result['source']['hora_del_parte'], '02:30')
        result = self.review({'fecha_del_parte': '2026-02-30', 'hora_del_parte': '25:99'})['results'][0]
        self.assertIn('invalid_fecha_del_parte', result['issues'])
        self.assertIn('invalid_hora_del_parte', result['issues'])

    def test_structure_and_limits(self):
        for payload in ([], {}, {'total_count': True, 'results': []},
                        {'total_count': 0, 'results': [{}]}, {'total_count': 101, 'results': [{}]*101}):
            with self.assertRaises(ValueError):
                inspect_response(json.dumps(payload).encode())


class SharedPointTests(unittest.TestCase):
    def test_repeated_snapshots_are_not_different_onsets(self):
        from spain_cyl_review import repeated_point_evidence
        row = dict(posicion={'lat': 41, 'lon': -4}, fecha_de_inicio='2026-09-17', hora_de_inicio='13:21')
        self.assertEqual(repeated_point_evidence([row, dict(row)]), [])
        changed = {**row, 'fecha_de_inicio': '2026-07-27'}
        result = repeated_point_evidence([row, row, changed])
        self.assertEqual(result[0]['distinct_onset_values'], 2)
        self.assertEqual(result[0]['row_indexes'], [0, 1, 2])

    def test_missing_onsets_and_invalid_points_do_not_group(self):
        from spain_cyl_review import repeated_point_evidence
        self.assertEqual(repeated_point_evidence([{'posicion': {'lat': 41, 'lon': -4}}]), [])
