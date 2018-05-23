import os
import logging

import requests

from lxml import etree
from pyquery import PyQuery as pq
from fake_useragent import UserAgent

from utils import prepare_logs_dir

# prepare all necessary for logs
prepare_logs_dir()
logging.basicConfig(filename='logs/parser.log', level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%d-%m-%y %H:%M')


class Pier14Parser:
    """
     http://pier14.de website parser
    """
    # Url  to get vacancy list
    MAIN_URL = "https://pier14.jacando.com/de/de/job-suche"
    CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
    # Config path for xml export
    OUTPUT_DIR = "parsed_xml"
    OUTPUT_FILENAME = "vacancies.xml"
    DIR_TO_EXPORT = os.path.join(CURRENT_DIR, OUTPUT_DIR)
    # the maximum number of attempts to obtain a response,
    # in case the server responded with an error
    ATTEMPTS_COUNT = 3
    # Base url to get vacancy
    BASE_VACANCY_URL = "https://pier14.jacando.com/de/de/job/"

    UA_SUFFIX = 'JobUFO GmbH'

    def __init__(self):
        """
        Init class
        """
        self.vacancy_list = []
        self.user_agent = UserAgent()

    @property
    def _request_settings(self):
        """
        Settings to make requests with random user agent
        :return: dict with settings
        """
        return {
            'timeout': 10,
            'headers': {'User-Agent': '{} {}'.format(self.user_agent.random,
                                                     self.UA_SUFFIX)},
            'verify': False,
        }

    @staticmethod
    def _get_job_id(link):
        """
        Fetching job id from vacancy url
        :param link: vacancy url
        :return: Job ID
        """
        try:
            id = link.rsplit('/', 1)[1]
            return id
        except Exception as e:
            logging.info(
                "Can not get identifier from url {} {}".format(link, str(e)))
            return ""

    def _get_page(self, url):
        """
        Trying to get page content from url
        :param url: page url
        :return: page content as PQuery object
        """
        current_attempt = 1
        res = None
        while True:
            logging.info("Trying to get page {}, attempts count: {}"
                         ''.format(url, self.ATTEMPTS_COUNT))
            try:
                response = requests.get(url, **self._request_settings)
                res = pq(response.content)
            except Exception as e:
                logging.info("Cannot get page {} \nError: {}"
                             ''.format(url, e))
            if (current_attempt == self.ATTEMPTS_COUNT) or res:
                break
            current_attempt += 1
        return res

    def _get_vacancies(self):
        """
        Getting vacancy list from main page.
        :return: True: if vacancies has been taken,False: if something
         went wrong. All errors will be in logs.
        """
        page = self._get_page(self.MAIN_URL)
        if page:
            logging.info("Parsing vacancy list")
            # Find category divs on page
            divs = page.find('div[class="large-text bold mrg-t5 mrg-b5'
                             ' title-color search_sort_category_title"]:eq(1)'
                             ).nextAll()
            divs.wrap('<body></body>')
            content = divs.find('div[class="pure-g"]').children()

            for div in content.items():
                vacancy_id = self._get_job_id(div.attr('data-job_url'))
                self.vacancy_list.append({
                    'id': vacancy_id,
                    'url': self.BASE_VACANCY_URL + vacancy_id,
                    'title': div.find('h3').text()[:-1],
                    'company_name': div.find('span[id="company-name"]').text()
                })
            logging.info("Vacancies count : {}".format(len(self.vacancy_list)))

            if len(self.vacancy_list) > 0:
                return True
        else:
            logging.info("No page received. Revocation")
        logging.info('No vacancies found')
        return False

    def _get_descriptions(self):
        """
        Getting vacancy descriptions from vacancies page using
        prepared vacancy list
        :return: True: if all descriptions has been taken
        False : if parser has not found description on page, program will be
        stopped
        """
        for vacancy in self.vacancy_list:
            vacancy_page = self._get_page(vacancy['url'])
            if vacancy_page:
                logging.info("Parsing description of vacancy id: {}"
                             .format(vacancy['id']))
                description = vacancy_page.find(
                    'meta[name="description"]').attr('content')
                keys = vacancy_page.find(
                    'meta[name="keywords"]').attr('content').split(',')
                locations = keys[1]
                top_location = keys[2]
                if description == "":
                    logging.info("Cannot get vacancy description. Revocation")
                    return False
                else:
                    vacancy.update({'description': description,
                                    'locations': locations,
                                    'top_location': top_location})
            else:
                logging.info("Cannot get vacancy details page. Revocation")
                return False
        return True

    def _export_to_xml(self):
        """
        Export vacancies to xml file
        :return: xml file path
        """
        root = etree.Element('vacancies')
        for data in self.vacancy_list:
            vacancy = etree.SubElement(root, 'position')
            etree.SubElement(vacancy, 'link').text = data["url"]
            etree.SubElement(vacancy, 'identifier').text = data["id"]
            etree.SubElement(vacancy, 'title').text = data["title"]
            etree.SubElement(vacancy, 'start_date')
            etree.SubElement(vacancy, 'kind')
            etree.SubElement(vacancy, 'description').text = \
                etree.CDATA(data["description"])
            etree.SubElement(vacancy, 'top_location').text = data[
                "top_location"]
            locations = etree.SubElement(vacancy, 'locations')
            for location in data["locations"].split('&'):
                etree.SubElement(locations, 'location').text = location
            etree.SubElement(vacancy, 'images')
            company = etree.SubElement(vacancy, 'company')
            etree.SubElement(company, 'name').text = data["company_name"]
            address = etree.SubElement(company, 'address')
            etree.SubElement(address, 'street')
            etree.SubElement(address, 'zip')
            etree.SubElement(address, 'city')
            etree.SubElement(vacancy, 'contact_email').text = \
                'fallback@jobufo.com'

        # create directory to save parsed xml if it does not exists
        if not os.path.exists(self.DIR_TO_EXPORT):
            os.makedirs(self.DIR_TO_EXPORT)

        filepath = os.path.join(self.DIR_TO_EXPORT, self.OUTPUT_FILENAME)

        tree = etree.ElementTree(root)
        tree.write(filepath, pretty_print=True, xml_declaration=True,
                   encoding='utf-8')
        return filepath

    def run(self):
        """
        The main function that controls the rest
        :return:
        """
        if self._get_vacancies():
            if self._get_descriptions():
                self._export_to_xml()


if __name__ == "__main__":
    parser = Pier14Parser()
    parser.run()
