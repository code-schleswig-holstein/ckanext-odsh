
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains


from seleniumrequests import Chrome
import uuid
import pdb


class SeleniumCkanApp:

    def __init__(self):
        self.base_url = "http://141.91.184.85"
        self.driver = Chrome()

    def login(self):
        self.driver.get(self.url("/user/login"))
        assert "Open Data Schleswig-Holstein" in self.driver.title
        elem = self.driver.find_element_by_id("field-login")
        elem.clear()
        elem.send_keys("sysadmin")
        elem = self.driver.find_element_by_id("field-password")
        elem.clear()
        elem.send_keys("OpenData!0619")
        elem.send_keys(Keys.RETURN)
        print(self.driver.title)
        assert "Datens" in self.driver.title
        # assert "No results found." not in driver.page_source

    def create_package(self):
        guid = str(uuid.uuid4())
        title = 'test_' + guid
        data = {"name": title, "title": title, "notes": "This is an automated Upload", "owner_org": "stadt-norderstedt", "license_id": "http://dcat-ap.de/def/licenses/dl-by-de/2.0",
                "extras": [{"key": "licenseAttributionByText", "value": "Test Lizenz"}, {"key": "issued", "value": "2019-04-23T09:18:11"}, {
                    "key": "spatial_uri", "value": "http://dcat-ap.de/def/politicalGeocoding/regionalKey/010600063063"}, {"key": "temporal_start", "value": "1989-01-01T00:00:00"}, {"key": "temporal_end", "value": "1993-12-19T00:00:00"}], "tags": [{"name": "Test"}], "resources": [{"name": "A distribution for this dataset", "format": "HTML", "url": "https://www.google.de/"}],
                "groups": [{"id": "econ"}]
                }
        response = self.driver.request('POST', self.url(
            '/api/3/action/package_create'), data)
        pdb.set_trace()

    def url(self, path):
        return self.base_url + path

    def got_to_url(self, path):
        self.driver.get(self.url(path))

    def close():
        driver.close()

    def get_slave_flag(self):
        return self.findElementByXPath("//meta[@data-name='type']").get_attribute("content")

    def findElementByXPath(self, xpath):
        return self.driver.find_element(By.XPATH, xpath)

    def findElementByName(self, name):
        return self.driver.find_element_by_name(name)

    def findElementById(self, id):
        return self.driver.find_element_by_id(id)

    def findElementByClassName(self, clazz):
        return self.driver.find_element_by_class_name(clazz)

    def fill_form(self, data, keyprefix=''):
        for key, value in data.iteritems():
            elem = self.driver.find_element_by_id(keyprefix + key)
            elem.send_keys(value)

    def select_by_visible_text(self, fieldId, text):
        select = Select(self.driver.find_element_by_id(fieldId))
        select.select_by_visible_text(text)

    def select_by_value(self, fieldId, value):
        select = Select(self.driver.find_element_by_id(fieldId))
        select.select_by_value(value)

    def clickOnElement(self, elem):
        loc = elem.location
        action = ActionChains(self.driver)
        action.move_by_offset(loc['x'], loc['y'])
        action.click().perform()

    def currentUrl(self):
        return self.driver.current_url

    def onMaster(self):
        cont = self.get_slave_flag()
        return cont == u'0'
