import unittest
from datetime import date
from datefilter import local_day,day_scope
from smart import candidates
class V7Tests(unittest.TestCase):
 def test_midnight_boundary(self):
  a={'game_start_time':'2026-11-18T04:59:00Z'}
  b={'game_start_time':'2026-11-18T05:00:00Z'}
  self.assertEqual(local_day(a,'America/New_York'),date(2026,11,17))
  self.assertEqual(local_day(b,'America/New_York'),date(2026,11,18))
 def test_unknown_and_close_time_not_used(self):
  rows=[{'close_time':'2026-11-17T22:00:00Z'}, {'game_start_time':'2026-11-17T14:00:00Z'}]
  verified,unknown,other=day_scope(rows,'America/New_York',date(2026,11,17))
  self.assertEqual(len(verified),1);self.assertEqual(len(unknown),1);self.assertEqual(len(other),0)
 def test_naive_start_rejected(self):
  self.assertIsNone(local_day({'game_start_time':'2026-11-17T19:00:00'},'America/New_York'))
 def test_same_day_combo(self):
  rows=[{'ticker':str(i),'event_ticker':str(i),'title':str(i),'yes_ask':.5,'game_start_time':'2026-11-17T19:00:00Z'} for i in range(6)]
  selected,_,_=day_scope(rows,'America/New_York',date(2026,11,17))
  self.assertTrue(candidates(selected,6))
if __name__=='__main__':unittest.main()
