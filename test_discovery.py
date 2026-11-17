import unittest
from unittest.mock import Mock
from discovery import sports_series,scan_series
class Tests(unittest.TestCase):
 def test_only_sports_series(self):
  s=Mock();s.get.return_value=Mock(status_code=200,json=lambda:{'series':[{'ticker':'A','category':'Sports'},{'ticker':'B','category':'Politics'}]})
  out,info=sports_series(s,1);self.assertEqual([x['ticker'] for x in out],['A'])
 def test_market_scan_no_fake_prices(self):
  s=Mock();s.get.return_value=Mock(status_code=200,json=lambda:{'events':[{'event_ticker':'E','markets':[{'ticker':'M','title':'X','yes_ask_dollars':'0.44'},{'ticker':'N','title':'Y'}]}]})
  rows,coverage=scan_series(s,[{'ticker':'S','title':'Test sport'}],1,1)
  self.assertEqual(len(rows),1);self.assertAlmostEqual(rows[0]['yes_ask'],.44)
 def test_scan_cap(self):
  s=Mock();s.get.return_value=Mock(status_code=200,json=lambda:{'events':[]})
  rows,c=scan_series(s,[{'ticker':'A'},{'ticker':'B'}],1,1)
  self.assertTrue(c['series_capped'])
if __name__=='__main__':unittest.main()
