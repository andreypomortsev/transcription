"""
Test Cases for lex_podcast.py
"""
import csv
import datetime
import random
from unittest import TestCase
from unittest.mock import Mock, patch

from requests import Response

from parsing import lex_podcast

PODCASTS_DATA = {}


class TestLexPodcastParser(TestCase):
    """Tests Cases for Lex Podcasts parser"""

    @classmethod
    def setUpClass(cls) -> None:
        """Load test_data responses needed by tests"""
        global PODCASTS_DATA
        with open("tests/fixtures/test_data.csv") as csv_data:
            reader = csv.reader(csv_data, delimiter=";")
            PODCASTS_DATA = list(reader)

    def setUp(self) -> None:
        self.podcast = dict(zip(PODCASTS_DATA[0], random.choice(PODCASTS_DATA[1:])))

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_convert_to_timestamp_with_good_path(self):
        """Test convert_to_timestamp function with a valid input"""
        date_str = "2022-11-04 16:09:32"
        expected_date = datetime.date(2022, 11, 4)
        expected_time = datetime.time(16, 9, 32)
        self.assertEqual(
            lex_podcast.convert_to_timestamp(date_str), (expected_date, expected_time)
        )

    def test_convert_to_timestamp_with_a_sad_path(self):
        """Test convert_to_timestamp function with a invalid input"""
        date_str = "2022-11-04T16:09:32Z"
        self.assertEqual(lex_podcast.convert_to_timestamp(date_str), (0, 0))
        self.assertEqual(lex_podcast.convert_to_timestamp(""), (0, 0))

    def test_get_youtube_id_with_a_valid_link(self):
        """Test get_youtube_id with valid link"""
        valid_url = self.podcast["youtube_url"]
        youtube_id = lex_podcast.get_youtube_id(valid_url)
        valid_id = valid_url[-11:]
        self.assertEqual(youtube_id, valid_id)

    def test_get_youtube_id_half_a_valid_link(self):
        """Test get_youtube_id with a half valid link"""
        invalid_url = "cseicjahcdc" + self.podcast["youtube_url"]
        youtube_id = lex_podcast.get_youtube_id(invalid_url)
        valid_id = invalid_url[-11:]
        self.assertEqual(youtube_id, valid_id)

    def test_get_youtube_id_half_an_invalid_link(self):
        """Test get_youtube_id with invalid input"""
        invalid_url = "cseicjahcdc"
        self.assertIsNone(lex_podcast.get_youtube_id(invalid_url))
        # Check if it handles integers
        invalid_url = 12
        self.assertIsNone(lex_podcast.get_youtube_id(invalid_url))
        # Check if it handles None
        invalid_url = None
        self.assertIsNone(lex_podcast.get_youtube_id(invalid_url))

    @patch("googleapiclient.discovery.build")
    def test_get_date_time_with_valid_input(self, mock_build):
        """Test get_date_time with valid input"""
        youtube_video_id = "abcde123456"
        api_key = "secretapikey"

        with patch.object(lex_podcast, "convert_to_timestamp") as mock_convert:
            # Mock the API response
            mock_response = {
                "items": [{"snippet": {"publishedAt": "2023-06-15T13:45:30Z"}}]
            }

            date_time = datetime.datetime(2023, 6, 15, 13, 45, 30)
            # Configure the mock object
            mock_request = mock_build.return_value.videos.return_value.list
            mock_request.return_value.execute.return_value = mock_response
            mock_convert.return_value = date_time

            # Call the function
            result = lex_podcast.get_date_time(youtube_video_id, api_key)

            # Assert the result
            expected = lex_podcast.convert_to_timestamp(date_time)
            self.assertEqual(result, expected)
