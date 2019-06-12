# coding: utf-8
from nosedep import depends

from ckanext.odsh.tests.ckan_selenium import SeleniumCkanApp
import pdb
import uuid


test_org = 'testherausgeber'


class TestSelenium:

    app = None

    @classmethod
    def setup_class(cls):
        TestSelenium.app = SeleniumCkanApp()
        # TestSelenium.app.login()

    def notest_edit_paths(self):
        paths = ['/organization/edit/' + test_org,
                 '/dataset/edit/testtesttest',
                 '/dataset/testtesttest/resource_edit/afaec407-d033-439d-a699-fe9279b20e6b',
                 '/dataset/new_resource/testtesttest',
                 '/dataset/new?group=',
                 '/harvest',
                 '/harvest/test2',
                 '/harvest/admin/test2'
                 ]
        for path in paths:
            TestSelenium.app.got_to_url(path)
            cont = TestSelenium.app.get_slave_flag()
            assert cont == u'0'

    def test_login(self):
        TestSelenium.app.login()
        assert '/dataset' in TestSelenium.app.currentUrl()

    @depends(after=test_login)
    def test_create_dataset(self):
        TestSelenium.app.got_to_url('/dataset/new?group=')
        # assert TestSelenium.app.onMaster()

        guid = str(uuid.uuid4())
        title = 'test_' + guid
        data = {"field-title": title, "field-notes": title, 'datepicker_start': '26.06.2019',
                'field-spatial_uri-value': 'http://dcat-ap.de/def/politicalGeocoding/districtKey/01001'}
        TestSelenium.app.fill_form(data)
        TestSelenium.app.select_by_visible_text(
            'field-license', 'Creative Commons CC Zero License (cc-zero)')

        elem = TestSelenium.app.findElementByClassName(
            'multiselect-native-select')
        TestSelenium.app.clickOnElement(elem)
        TestSelenium.app.findElementByXPath("//input[@value = 'soci']").click()
        TestSelenium.app.clickOnElement(elem)

        TestSelenium.app.findElementByName('save').click()
        TestSelenium.app.findElementByXPath("//a[text()='Link']").click()

        TestSelenium.app.fill_form(
            {'field-image-url': 'url.png', 'field-format': 'png'})
        TestSelenium.app.findElementById('form-submit-button').click()

        assert 'dataset/'+title in TestSelenium.app.currentUrl()
