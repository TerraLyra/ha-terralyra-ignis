from unittest import TestCase
from inpe_package import load
settings=load('settings').settings

class SettingsTests(TestCase):
    def test_disabled_default_and_sorted_scope(self):
        self.assertEqual(settings({}),(False,()))
        self.assertEqual(settings({'inpe_enabled':True,'inpe_states':['AM','AC']}),(True,('AC','AM')))
    def test_invalid_scope(self):
        for values in ([],['XX'],['AC','AC'],['AC','AM','SP','BA']):
            with self.assertRaises(ValueError): settings({'inpe_enabled':True,'inpe_states':values})
