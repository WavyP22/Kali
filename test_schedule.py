import unittest
from datetime import date
from unittest.mock import patch
from schedule import enrich_start_times, _contains_team

class ScheduleTests(unittest.TestCase):
    def test_team_matching(self):
        self.assertTrue(_contains_team('Boston Celtics vs New York Knicks', 'Boston Celtics'))
        self.assertFalse(_contains_team('Boston Celtics vs New York Knicks', 'Boston'))
    @patch('schedule.scoreboard_games')
    def test_exact_two_team_match(self, mock):
        mock.return_value = [{'teams':['Boston Celtics','New York Knicks'],'start':'2026-11-17T19:30:00+00:00','level':'NBA'}]
        rows=[{'sport':'NBA','title':'Boston Celtics to win','event_title':'Boston Celtics vs New York Knicks','game_start_time':''}]
        out=enrich_start_times(rows,date(2026,11,17),'America/New_York')
        self.assertEqual(out[0]['game_start_time'],'2026-11-17T19:30:00+00:00')
    @patch('schedule.scoreboard_games')
    def test_single_team_does_not_guess(self, mock):
        mock.return_value = [{'teams':['Boston Celtics','New York Knicks'],'start':'2026-11-17T19:30:00+00:00','level':'NBA'}]
        rows=[{'sport':'NBA','title':'Boston Celtics to win','game_start_time':''}]
        self.assertFalse(enrich_start_times(rows,date(2026,11,17),'America/New_York')[0]['game_start_time'])
    @patch('schedule.scoreboard_games')
    def test_ambiguous_matches_fail_closed(self, mock):
        mock.return_value = [{'teams':['Boston Celtics','New York Knicks'],'start':t,'level':'NBA'} for t in ('2026-11-17T19:30:00+00:00','2026-11-17T22:30:00+00:00')]
        rows=[{'sport':'NBA','event_title':'Boston Celtics vs New York Knicks','game_start_time':''}]
        self.assertFalse(enrich_start_times(rows,date(2026,11,17),'America/New_York')[0]['game_start_time'])
if __name__=='__main__':unittest.main()
