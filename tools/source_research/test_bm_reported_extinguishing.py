import unittest
from bm_reported_extinguishing import reported_extinguishing

class ExtinguishingTests(unittest.TestCase):
    def test_completed_forms_and_original_spans(self):
        for verb in ['elfojtották','eloltották','oltották el','fojtották el','eloltotta']:
            text=f'A lángokat három vízsugárral {verb}.'
            r=reported_extinguishing(text)
            self.assertEqual(r[0]['kind'],'reported_extinguished')
            self.assertEqual(text[r[0]['start']:r[0]['end']],r[0]['evidence'])
            self.assertEqual(text[r[0]['verb_start']:r[0]['verb_end']],verb)

    def test_negated_conditional_and_attempts_are_not_completion(self):
        for text in ['A tüzet nem oltották el.', 'Ha a tüzet eloltották volna, hazamehettek volna.',
                     'Állítólag eloltották a tüzet.', 'A gyakorlaton eloltották a tüzet.',
                     'Megpróbálták eloltani a tüzet.', 'A lángokat oltják.',
                     'Eloltották a lámpát.']:
            self.assertFalse(any(e['kind']=='reported_extinguished' for e in reported_extinguishing(text)),text)

    def test_one_incident_completion_is_not_global_status(self):
        r=reported_extinguishing('A tüzet eloltották. Máshol még ég a növényzet.')
        self.assertEqual(len(r),1)
        self.assertNotIn('Máshol',r[0]['evidence'])

    def test_fire_in_other_clause_does_not_make_lamp_extinguishing_fire_completion(self):
        for text in ['Tűz van, a lámpát eloltották.', 'Tűz van és a lámpát eloltották.',
                     'A tüzet oltják; a lámpát eloltotta.']:
            self.assertFalse(reported_extinguishing(text),text)

    def test_historical_and_quoted_completion_are_separate(self):
        self.assertEqual(reported_extinguishing('Tegnap eloltották a tüzet.')[0]['kind'],'historical_extinguishing')
        self.assertEqual(reported_extinguishing('„Eloltották a tüzet” – mondta.')[0]['kind'],'uncertain_extinguishing')

    def test_separate_clauses_retain_only_supported_completion(self):
        text='A lángokat eloltották, de a melléképület még ég.'
        r=reported_extinguishing(text)
        self.assertEqual(len(r),1)
        self.assertEqual(r[0]['kind'],'reported_extinguished')
        self.assertNotIn('melléképület',r[0]['evidence'])
        self.assertEqual(text[r[0]['start']:r[0]['end']],r[0]['evidence'])
