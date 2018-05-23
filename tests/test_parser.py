import os
import sys
import unittest

from pyquery import PyQuery as pq

sys.path.append('..')

from pier14_parser import Pier14Parser

from unittest.mock import patch
from utils import prepare_logs_dir

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_DIR_NAME = 'data'
TEST_DATA_DIR = os.path.join(CURRENT_DIR, TEST_DATA_DIR_NAME)

LOGS_DIR = 'logs'
LOGS_PATH = os.path.join(CURRENT_DIR, LOGS_DIR)

LIST_PAGE_FILENAME = 'test_list.html'
LIST_PAGE_FILEPATH = os.path.join(TEST_DATA_DIR, LIST_PAGE_FILENAME)
VACANCY_PAGE_FILENAME = 'test_vacancy.html'
VACANCY_PAGE_FILEPATH = os.path.join(TEST_DATA_DIR, VACANCY_PAGE_FILENAME)

prepare_logs_dir(LOGS_PATH)


class ParserTestCase(unittest.TestCase):
    """
    Parser tests
    """
    TEST_LIST = [
        {'id': '7L6rnMmC',
         'url': 'https://pier14.jacando.com/de/de/job/7L6rnMmC',
         'title': 'Restaurantfachleute und Servicekräfte (m/w) ',
         'company_name': 'Pier14 Unternehmensgruppe'}
    ]

    def setUp(self):
        self.parser = Pier14Parser()

    def test_get_vacancies(self):
        page = pq(filename=LIST_PAGE_FILEPATH)
        with patch.object(Pier14Parser, '_get_page',
                          return_value=page):
            self.parser._get_vacancies()

    def test_get_description(self):
        page = pq(filename=VACANCY_PAGE_FILEPATH)
        self.parser.vacancy_list = self.TEST_LIST
        with patch.object(Pier14Parser, '_get_page',
                          return_value=page):
            self.parser._get_descriptions()

    def test_get_id(self):
        id = self.parser._get_job_id(self.TEST_LIST[0]['url'])
        self.assertEqual(id, '7L6rnMmC')


if __name__ == '__main__':
    unittest.main()
