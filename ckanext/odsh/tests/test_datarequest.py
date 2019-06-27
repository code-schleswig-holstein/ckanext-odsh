
from ckanext.odsh.tests.test_helpers import AppProxy
import ckanext.odsh.tests.test_helpers as testhelpers
import ckan.tests.factories as factories
import uuid
import pdb
from ckanext.odsh.tests.harvest_sever_mock import HarvestServerMock
import ckanext.odsh.tests.harvest_sever_mock as harvest_sever_mock
import subprocess
import re

markdown = \
    """
Lorem markdownum supplex iniquis, nec nostram nam conde tympana, deae Mutinae
regna sepulcro; morae arces quae, pia? Rates Circe, quandoquidem Ausoniae, me,
cacumine apta, saevus abductas navigiis. Sacri ostendit *ad anas* amores nostras
[currebam celeres], milia gaudet eripitur superest circumque auras, [nec]. Si
haurit geminis agendum profana lacertis infamis?

> Dedit potuit perenni nesciet flumine. Et sui **ibis** mihi supponat, flamina
> mihi rogos, deus manum ora tenebras. Acta nec dominus aenum, haud de ripa
> instabilemque amnis erat nam Patraeque parabat quod membra quamquam.
"""


class TestDatarequest:

    def test_nologin_cannot_create_request(self):
        pass

    def _create_request(self):
        guid = str(uuid.uuid4())
        self._get_app().login()
        response = self.app.get('/datarequest/new')
        form = response.forms[0]
        title = 'datarequest_' + guid
        form['title'] = title
        form['description'] = markdown
        final_response = self.app.submit_form(form)


        id = re.search(
            '/datarequest/edit/([a-zA-Z0-9\-]*)">', final_response.body).group(1)
        return id

    def test_create_datarequest(self):
        # Act
        id = self._create_request()

        # Assert
        response = self.app.get('/datarequest')
        assert id in response

    def test_edit_datarequest(self):
        # Arrange
        id = self._create_request()

        # Act
        response = self.app.get('/datarequest/edit/'+id)
        form = response.forms[0]
        form['title'] = id+'edit_title'
        form['description'] = id+'edit_desc'
        final_response = self.app.submit_form(form)

        # Assert
        response = self.app.get('/datarequest/'+id)
        assert id+'edit_title' in response
        assert id+'edit_desc' in response

    def test_comment_datarequest(self):
        # Arrange
        id = self._create_request()
        guid = str(uuid.uuid4())

        # Act
        response = self.app.get('/datarequest/comment/'+id)
        form = response.forms[0]
        form['comment'] = markdown + guid
        final_response = self.app.submit_form(form)

        # Assert
        assert guid in final_response

    def test_close_datarequest(self):
        # Arrange
        id = self._create_request()

        # Act
        response = self.app.get('/datarequest/close/'+id)
        form = response.forms[0]
        final_response = self.app.submit_form(form)

        # Assert
        response = self.app.get('/datarequest/'+id)
        assert 'label-closed' in response

    def _get_app(self):
        if not hasattr(self, 'app'):
            app = AppProxy()
            self.app = app
        return self.app
