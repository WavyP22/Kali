import unittest
from marketfilter import market_type, game_eligible, preference_rank
class TestMarketFilter(unittest.TestCase):
 def test_futures(self):
  for title in ['Will Seattle receive a Pro Basketball expansion team before Jan 1, 2028?', 'Will Mike Brown be out before Jul 1, 2027?', 'Who will win the championship?']:
   self.assertFalse(game_eligible({'title':title}))
 def test_spreads(self):
  for title in ['Lakers -5.5 points','Will Celtics win by 6+ points?','Knicks cover the spread']:
   self.assertEqual(market_type({'title':title}),'Game Lines (Spreads)')
 def test_types(self):
  self.assertEqual(market_type({'title':'New York wins the 1st half'}),'Moneyline / Winner')
  self.assertEqual(market_type({'title':'Over 221.5 points'}),'Totals (Over/Under)')
  self.assertFalse(game_eligible({'title':'Random sports news'}))
 def test_priority(self):
  self.assertLess(preference_rank({'title':'Team -4.5 points'}),preference_rank({'title':'Team wins'}))
if __name__=='__main__':unittest.main()
