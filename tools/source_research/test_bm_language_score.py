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

    def test_unlinked_responder_is_visible_and_scored_by_span(self):
        gold,probe=self.sample()
        probe['results'][0]['description']=dict(text='falvi',role_review=dict(mentions=[dict(start=0,end=5,evidence='falvi',settlements=[],roles=[dict(role='responder')])]),fire_review=dict(involvement=[]))
        gold[0]['mention_roles']=[dict(field='description',start=0,end=5,evidence='falvi',role='responder')]
        r=score(gold,probe)['records'][0]
        self.assertEqual(r['unlinked_responders'][0]['evidence'],'falvi')
        self.assertEqual(len(r['mention_role_comparison']['matched']),1)
        self.assertEqual(r['responders_found'],[])
        gold[0]['mention_roles'][0]['evidence']='wrong'
        with self.assertRaises(ValueError):score(gold,probe)

    def test_extra_role_is_not_hidden_by_correct_place_name(self):
        gold,probe=self.sample()
        probe['results'][0]['description']=dict(text='Place',role_review=dict(mentions=[dict(start=0,end=5,evidence='Place',settlements=['Place'],roles=[dict(role='responder')])]),fire_review=dict(involvement=[]))
        gold[0]['mention_roles']=[]
        r=score(gold,probe)['records'][0]
        self.assertEqual(len(r['mention_role_comparison']['extra']),1)
        self.assertEqual(r['mention_role_comparison']['matched'],[])

    def test_missed_extinguishing_is_counted_without_claiming_current_status(self):
        gold,probe=self.sample()
        self.assertIsNone(score(gold,probe)['records'][0]['reported_extinguishing_matches'])
        gold[0]['reported_extinguished']=True
        result=score(gold,probe)
        self.assertFalse(result['records'][0]['reported_extinguishing_matches'])
        self.assertTrue(result['extinguishing_accuracy_assessed'])
        self.assertFalse(result['no_fire_verified'])
