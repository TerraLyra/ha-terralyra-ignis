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
