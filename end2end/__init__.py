import os

from django.test import LiveServerTestCase
from django.contrib.auth.models import User

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options


class BaseTestCase(LiveServerTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def setUp(self):
        self.username = 'admin'
        self.password = 'admin'
        self.email = 'admin@archlinux.org'

        User.objects.create_superuser(
            username=self.username,
            password=self.password,
            email=self.email
        )

        options = Options()
        if os.getenv('ARCHWEB_HEADLESS', True):
            options.add_argument("--headless")
            # Required for travisci
            options.add_argument("--no-sandbox")
        self.selenium = webdriver.Chrome(chrome_options=options)
        super(BaseTestCase, self).setUp()

        self.login()

    def tearDown(self):
        # Call tearDown to close the web browser
        self.selenium.quit()
        super(BaseTestCase, self).tearDown()

    def login(self):
        self.get('/devel/')
        username = self.selenium.find_element_by_id("id_username")
        username.send_keys("admin")
        password = self.selenium.find_element_by_id("id_password")
        password.send_keys("admin")
        password.send_keys(Keys.RETURN)

    def get(self, url):
        self.selenium.get('{}{}'.format(self.live_server_url,  url))

    def submit(self):
        self.selenium.find_element_by_xpath('//input[@type="submit"]').click()
