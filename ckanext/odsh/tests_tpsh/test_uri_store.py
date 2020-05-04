import nose.tools as nt
from ckanext.odsh.uri_store import add_uri, get_id_from_uri, _set_uri_to_id, _get_uri_to_id

class Test_uri_store(object):
    def test_add_uri_adds_values_to_dict(self):
        _set_uri_to_id({u'http://some_uri': u'some_id'})
        dataset_dict = {
            'id': u'some_new_id',
            u'extras': [
                {u'key': u'uri', u'value': u'http://some_new_uri'},
            ]
        }
        add_uri(dataset_dict)
        nt.assert_equal(
            _get_uri_to_id().get('http://some_uri'),
            u'some_id'
        )
        nt.assert_equal(
            _get_uri_to_id().get('http://some_new_uri'),
            u'some_new_id'
        )
    
    def test_get_id_returns_id(self):
        _set_uri_to_id({u'http://some_uri': u'some_id'})
        uri = 'http://some_uri'
        id = get_id_from_uri(uri)
        id_expected = u'some_id'
        nt.assert_equal(id, id_expected)
    
    def test_get_id_from_uri_returns_None_if_dict_empty(self):
        _set_uri_to_id({})
        id = get_id_from_uri('some_uri')
        nt.assert_equal(id, None)
    
    def test_get_id_from_uri_returns_None_if_id_unknown(self):
        _set_uri_to_id({'uri_to_id': {u'http://some_uri': u'some_id'}})
        id = get_id_from_uri('some_unknown_id')
        nt.assert_equal(id, None)