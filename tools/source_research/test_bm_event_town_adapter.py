import unittest
from bm_event_town_adapter import event_town_evidence
from bm_location_candidates import Settlement

class EventTownTests(unittest.TestCase):
    def sample(self):
        text='Gyöngyösön egy ház ég.'
        field=dict(text=text,role_review=dict(mentions=[dict(start=0,end=10,evidence='Gyöngyösön',settlements=['Gyöngyös'],linkage='lemma_or_exact',roles=[dict(role='unknown')])]),fire_review=dict(evidence=[dict(kind='involved_candidate',start=0,end=len(text),evidence=text)]))
        return dict(title=field,description=dict(text='',role_review=dict(mentions=[]),fire_review=dict(evidence=[])))

    def test_positive_locative_links_to_shared_identity_without_coordinates(self):
        r=event_town_evidence(self.sample(),(Settlement('hu:1','Gyöngyös'),))
        self.assertEqual(r['event_settlement_ids'],['hu:1'])
        self.assertFalse(r['creates_incident'])

    def test_non_event_roles_and_missing_fire_never_promote(self):
        for role in ['responder','organization','direction','street','negated','between_places']:
            fields=self.sample();fields['title']['role_review']['mentions'][0]['roles']=[dict(role=role)]
            self.assertEqual(event_town_evidence(fields,(Settlement('hu:1','Gyöngyös'),))['event_settlement_ids'],[])
        fields=self.sample();fields['title']['fire_review']['evidence']=[]
        self.assertEqual(event_town_evidence(fields,(Settlement('hu:1','Gyöngyös'),))['event_settlement_ids'],[])

    def test_ambiguous_identity_and_changed_evidence(self):
        self.assertEqual(event_town_evidence(self.sample(),(Settlement('a','Gyöngyös'),Settlement('b','Gyöngyös')))['event_settlement_ids'],[])
        fields=self.sample();fields['title']['text']='changed'
        with self.assertRaises(ValueError):event_town_evidence(fields,(Settlement('a','Gyöngyös'),))
