import unittest
import random
from parsing import *

class TestLexScrapping(unittest.TestCase):
    def setUp(self) -> None:
        # Download a random data from fixtures
        self.rand = random.randint(0, 100)
        return super().setUp()
    def tearDown(self) -> None:
        return super().tearDown()
    
    def test_load_api(self):
        """ Test download the api_key from .env """
        pass

    def test_get_description(self):
        """ Test get description from a podcast url """
        pass