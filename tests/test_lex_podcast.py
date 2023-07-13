"""
Test Cases for Mocking Lab
"""
import csv
import datetime
from unittest import TestCase
from unittest.mock import Mock, patch

from requests import Response

from parsing import lex_podcast

PODCASTS_DATA = {}

class TestLexPodcastParser(TestCase):
    """Tests Cases for Lex Podcasts parser"""

    @classmethod
    def setUpClass(cls) -> None:
        """ Load test_data responses needed by tests """
        global PODCASTS_DATA
        with open('tests/fixtures/test_data.csv') as csv_data:
            reader = csv.reader(csv_data, delimiter=";")
            PODCASTS_DATA = list(reader)

    @classmethod
    def tearDownClass(cls) -> None:
        """ Delete test_data from RAM """
        global PODCASTS_DATA
        PODCASTS_DATA = {}

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################
    
    def test_convert_to_timestamp_with_good_path(self):
        """Test convert_to_timestamp function with a valid input"""
        date_str = '2022-11-04 16:09:32'
        expected_date = datetime.date(2022, 11, 4)
        expected_time = datetime.time(16, 9, 32)
        self.assertEqual(lex_podcast.convert_to_timestamp(date_str), (expected_date, expected_time))

    def test_convert_to_timestamp_with_sad_path(self):
        """Test convert_to_timestamp function with a invalid input"""
        date_str = '2022-11-04T16:09:32Z'
        self.assertEqual(lex_podcast.convert_to_timestamp(date_str), (0, 0))
        self.assertEqual(lex_podcast.convert_to_timestamp(''), (0, 0))

    @patch("")
    def test_get_youtube_id_valid(self):
        """Test get_youtube_id with valid link"""
        pass
