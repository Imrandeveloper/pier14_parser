import os
import sys
import json
import logging
import requests
import time

from splinter import Browser

from utils import prepare_logs_dir

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

"""Settings for local testing on Linux/Mac with Chrome driver"""

LINUX_PLATFORM = 'linux'
MAC_PLATFORM = 'darwin'

WEB_DRIVERS = {
    LINUX_PLATFORM: 'chromedriver_linux_x64',
    MAC_PLATFORM: 'chromedriver_darwin'
}

try:
    DRIVER_PATH = os.path.join(CURRENT_PATH, 'drivers',
                               WEB_DRIVERS[sys.platform])
except Exception as e:
    raise Exception

prepare_logs_dir()

logging.basicConfig(filename='logs/exchanger.log', level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%d-%m-%y %H:%M')


class Exchanger:
    """
    Class to apply for job with user data
    """
    DOWNLOADS_DIR = 'downloads'

    def __init__(self, vacancy_url, user_data):
        """
        Init class
        :param vacancy_url: url of vacancy page
        :param user_data: dict with user data
        """
        self.browser = self._setup_browser()
        self.vacancy_url = vacancy_url
        self.user_data = user_data

    @staticmethod
    def _setup_browser():
        """
        Prepare splinter browser
        :return: Browser object
        """
        logging.info('##### Prepare browser #####')
        options = {'executable_path': DRIVER_PATH, 'headless': True}
        return Browser('chrome', **options)

    def _open_page(self):
        """
        Visit vacancy page and apply for a job
        """
        logging.info('Open vacancy page {}'.format(self.vacancy_url))
        self.browser.visit(self.vacancy_url)
        self.browser.find_by_id("bottom_apply").click()

    def _fill_inputs(self):
        """
        Fill required fields
        """
        logging.info('Fill inputs')
        time.sleep(3)
        #Here there is problem with "not unique" names. So we need to search
        #correct object
        inputs = self.browser.find_by_name('user[first_name]')
        for field in inputs:
            try:
                field.value = self.user_data['first_name']
            except Exception as e:
                logging.info("error: {}".format(str(e)))

        inputs = self.browser.find_by_name('user[last_name]')
        for field in inputs:
            try:
                field.value = self.user_data['last_name']
            except Exception as e:
                logging.info("error: {}".format(str(e)))

        inputs = self.browser.find_by_name('user[email]')
        for field in inputs:
            try:
                field.value = self.user_data['email']
            except Exception as e:
                logging.info("error: {}".format(str(e)))

        inputs = self.browser.find_by_name('user[password]')
        for field in inputs:
            try:
                field.value = self.user_data['password']
            except Exception as e:
                logging.info("error: {}".format(str(e)))

        inputs = self.browser.find_by_name('user[password_confirmation]')
        for field in inputs:
            try:
                field.value = self.user_data['password']
            except Exception as e:
                logging.info("error: {}".format(str(e)))

    def _download_file(self):
        """
        Download cv file
        :return: str file path
        """
        logging.info('Download cv file')
        file_url = self.user_data['cv_path']
        r = requests.get(file_url, allow_redirects=True)
        filename = file_url.rsplit('/', 1)[1]

        downloads_dir = os.path.join(CURRENT_PATH, self.DOWNLOADS_DIR)

        # create directory to save downloaded cv file if it does not exists
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)
        file_path = os.path.join(downloads_dir, filename)
        try:
            open(file_path, 'wb').write(r.content)
        except Exception as e:
            logging.info('Can not download file: {}'.format(str(e)))
        return file_path

    def _upload_file(self):
        """
        Upload file
        """
        file_path = self._download_file()
        logging.info('Try to attach file')
        try:
            self.browser.attach_file('documents[file_name_1]', file_path)
        except Exception as e:
            logging.info('Can not upload file: {}'.format(str(e)))

    def _second_step(self):
        while self.browser.is_element_not_present_by_name('jobber[gender]'):
            time.sleep(1)
        if self.user_data['gender'] == 'M':
            self.browser.select('jobber[gender]','Male')
        else:
            self.browser.select('jobber[gender]', 'Female')

        # The same problem as before with "not unique" names.
        inputs = self.browser.find_by_name('jobber[birth_date]')
        for field in inputs:
            try:
                field.value = self.user_data['birthday']
            except Exception as e:
                logging.info("error: {}".format(str(e)))

        inputs = self.browser.find_by_name('user[mobile_phone]')
        for field in inputs:
            try:
                field.value = self.user_data['phone'].split('49')[1]
            except Exception as e:
                logging.info("error: {}".format(str(e)))

        inputs = self.browser.find_by_name('location[zip_code]')
        for field in inputs:
            try:
                field.value = self.user_data['postal_code']
            except Exception as e:
                logging.info("error: {}".format(str(e)))

        self.browser.find_by_id('jobber_accept_form_button').last.click()
        self.browser.is_element_not_present_by_css('.load_success', 5)
        if self.browser.is_element_present_by_css('.load_success'):
            return True
        else:
            return False

    def run(self):
        """
        Run process of applying job
        """
        logging.info('start')
        self._open_page()
        logging.info('fill')
        self._fill_inputs()
        logging.info('upload')
        self._upload_file()
        self.browser.find_by_xpath('//input[@value="Absenden"]').last.click()
        self.browser.find_by_xpath('//input[@value="Ja"]').last.click()
        if self._second_step():
            logging.info("Success")
        else:
            logging.info("Failed")


if __name__ == "__main__":
    url = 'https://pier14.jacando.com/de/de/job/7L6rnMmC'
    data = json.load(open('test_user_data.json'))
    parser = Exchanger(user_data=data, vacancy_url=url)
    parser.run()
