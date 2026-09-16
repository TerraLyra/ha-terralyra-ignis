import json
import unittest
from act_feed import InvalidFeed
from act_summary import summarize_feed


def feed(*records):
    return ('<rss version="2.0"><channel>'+''.join(records)+'</channel></rss>').encode()


def record(kind, identity='secret-id', title='private title'):
    return (f'<item><type>{kind}</type><guid>{identity}</guid><cadid>{identity}</cadid>'
            f'<title>{title}</title><description>Updated: 16 Sep 2026 22:54:31.2</description>'
            '<g:point xmlns:g="http://www.georss.org/georss">-35.31234 149.12345</g:point></item>')


class SummaryTests(unittest.TestCase):
    def test_mixed_feed_and_duplicates(self):
        result = summarize_feed(feed(record('GRASS AND BUSH FIRE', title='TEST ONLY'),
                                     record('AMBULANCE RESPONSE'), record('UNKNOWN', 'other')))
        self.assertEqual(result['record_count'], 3)
        self.assertEqual(result['categories'], {'medical':1,'unknown':1,'vegetation_fire_candidate':1})
        self.assertEqual(result['exercise_evidence'], {'marked':1,'not_established':2})
        self.assertEqual(result['repeated_matching_id_groups'], 1)
        self.assertEqual(result['records_in_repeated_matching_id_groups'], 2)
        self.assertEqual(result['times']['updated'], {'timezone_unverified':3})
        self.assertEqual(result['production_readiness'], 'not_established')

    def test_no_raw_details_in_serialized_output(self):
        result = json.dumps(summarize_feed(feed(record('AMBULANCE RESPONSE'))))
        for secret in ('secret-id','private title','-35.31234','149.12345','22:54:31'):
            self.assertNotIn(secret,result)

    def test_missing_data_counted(self):
        result = summarize_feed(feed('<item><type>UNKNOWN</type></item>'))
        self.assertEqual(result['identity'], {'missing':1})
        self.assertEqual(result['location'], {'missing':1})
        self.assertEqual(result['times']['call'], {'missing':1})

    def test_malformed_tail_cannot_return_partial_result(self):
        with self.assertRaises(InvalidFeed):
            summarize_feed(feed(record('GRASS AND BUSH FIRE'))[:-5])

    def test_planned_burn_is_counted_separately(self):
        result = summarize_feed(feed(record('HAZARD REDUCTION BURN','a'),
                                     record('GRASS AND BUSH FIRE','b')))
        self.assertEqual(result['categories'], {'planned_burn':1,'vegetation_fire_candidate':1})
        self.assertEqual(result['record_count'],2)
        self.assertEqual(result['production_readiness'],'not_established')

    def test_limits_propagate(self):
        with self.assertRaises(InvalidFeed):
            summarize_feed(feed(record('UNKNOWN'),record('UNKNOWN')),max_items=1)
        with self.assertRaises(InvalidFeed):
            summarize_feed(feed(),max_bytes=1)

    def test_empty_and_order_independence(self):
        self.assertEqual(summarize_feed(feed())['record_count'],0)
        a,b=record('UNKNOWN','a'),record('AMBULANCE RESPONSE','b')
        self.assertEqual(summarize_feed(feed(a,b)),summarize_feed(feed(b,a)))
