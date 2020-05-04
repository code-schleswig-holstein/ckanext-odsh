import nose.tools as nt
from testfixtures import log_capture

from ckan.common import config
from ckanext.odsh.lib.odsh_icap_client import ODSHICAPRequest, _read_from_config

class Test_ODSHICAPRequest(object):
    def setUp(self):
        config.update({
            'ckanext.odsh.icap.host': 'some_host',
            'ckanext.odsh.icap.port': '123',
            'ckanext.odsh.icap.clientip': 'some_ip',
        })
    
    def tearDown(self):
        config.clear()

    def test_it_initializes_with_parameters_set_in_config(self):
        request = ODSHICAPRequest('some_filename', 'some_filebuffer')
        nt.assert_equal(request.HOST, 'some_host')
        nt.assert_equal(request.PORT, 123)
        nt.assert_equal(request.CLIENTIP, 'some_ip')
    
    @log_capture()
    def test_it_logs_missing_parameter_host_to_error_log(self, capture):
        del config['ckanext.odsh.icap.host']
        ODSHICAPRequest('some_filename', 'some_filebuffer')
        capture.check((
            'ckanext.odsh.lib.odsh_icap_client',
            'ERROR',
            "'key ckanext.odsh.icap.host is not defined in ckan config file.'"
        ))
    
    @log_capture()
    def test_it_logs_missing_parameter_port_to_error_log(self, capture):
        del config['ckanext.odsh.icap.port']
        ODSHICAPRequest('some_filename', 'some_filebuffer')
        capture.check((
            'ckanext.odsh.lib.odsh_icap_client',
            'ERROR',
            "'key ckanext.odsh.icap.port is not defined in ckan config file.'"
        ))
    
    @log_capture()
    def test_it_logs_missing_parameter_clientip_to_error_log(self, capture):
        del config['ckanext.odsh.icap.clientip']
        ODSHICAPRequest('some_filename', 'some_filebuffer')
        capture.check((
            'ckanext.odsh.lib.odsh_icap_client',
            'ERROR',
            "'key ckanext.odsh.icap.clientip is not defined in ckan config file.'"
        ))
    
    def test_read_from_config_raises_KeyError_if_host_not_defined_in_config(self):
        del config['ckanext.odsh.icap.host']
        with nt.assert_raises(KeyError):
            _read_from_config('ckanext.odsh.icap.host')
    
    def test_read_from_config_raises_KeyError_if_port_not_defined_in_config(self):
        del config['ckanext.odsh.icap.port']
        with nt.assert_raises(KeyError):
            _read_from_config('ckanext.odsh.icap.port')
    
    def test_read_from_config_raises_KeyError_if_clientip_not_defined_in_config(self):
        del config['ckanext.odsh.icap.clientip']
        with nt.assert_raises(KeyError):
            _read_from_config('ckanext.odsh.icap.clientip')
