import unittest
from bm_language_score import score

class ScoreTests(unittest.TestCase):
    def sample(self):
        field=dict(role_review=dict(mentions=[dict(settlements=['Place'],roles=[dict(role='unknown')])]),fire_review=dict(involvement=[]))
        return [dict(id='x',title='Title',event_places=['Place'],responders=['Place'],involvement=[])], dict(results=[dict(title=dict(text='Title',**field),description=field)])

    def test_name_recognition_does_not_count_as_responder_or_event_role_accuracy(self):
        gold,probe=self.sample()
        result=score(gold,probe)
        self.assertEqual(result['records'][0]['event_names_found'],['Place'])
        self.assertEqual(result['records'][0]['responders_missed'],['Place'])
        self.assertFalse(result['event_role_accuracy_assessed'])
        self.assertFalse(result['no_fire_verified'])

    def test_misaligned_gold_is_rejected(self):
        gold,probe=self.sample()
        with self.assertRaises(ValueError):score([],probe)
        gold[0]['title']='Other'
        with self.assertRaises(ValueError):score(gold,probe)
