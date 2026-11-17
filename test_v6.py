import unittest
from classify import classify
from smart import candidates
class V6Tests(unittest.TestCase):
 def test_levels(self):
  self.assertEqual(classify({'sport':'NCAA Womens College Basketball WCBB'}),('Basketball','WCBB'))
  self.assertEqual(classify({'sport':'NBA games'}),('Basketball','NBA'))
  self.assertEqual(classify({'sport':'CBB games'}),('Basketball','CBB'))
 def test_combos(self):
  rows=[dict(title=str(i),ticker=str(i),event_ticker=str(i),yes_ask=.5,level='NBA') for i in range(6)]
  for n in range(2,7):
   c=candidates(rows,n)
   self.assertTrue(c)
   self.assertEqual(c[0]['legs'],n)
   self.assertEqual(c[0]['status'],'UNVERIFIED — NOT A FAVORABLE PICK')
 def test_no_same_event(self):
  rows=[dict(title=str(i),ticker=str(i),event_ticker='same',yes_ask=.5) for i in range(6)]
  self.assertEqual(candidates(rows,2),[])
if __name__=='__main__':unittest.main()
