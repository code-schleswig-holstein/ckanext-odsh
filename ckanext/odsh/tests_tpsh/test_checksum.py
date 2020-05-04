from mock import patch, mock_open
import nose.tools as nt
from ckanext.odsh.lib.uploader import _raise_validation_error_if_hash_values_differ, calculate_hash
import ckantoolkit as ct
import ckan.logic as logic
import hashlib

import os
path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)

class testHashException(object):     
     text = 'Transparenz SH'
     # hash produced by following command in bash:
     # echo -n "Transparenz SH" | md5sum
     hash_for_text = '791759e98a3ec4cc9c03141a3293292b'

     def test_without_hash(self):
          resource = {'package_id':'Test_id',}
          with patch("__builtin__.open", mock_open(read_data=self.text)) as mock_file:
               with open('some/file') as f:
                    assert _raise_validation_error_if_hash_values_differ(f, resource) == None

     def test_with_correct_hash(self):
          resource = {'package_id':'Test_id', 'hash':self.hash_for_text}
          with patch("__builtin__.open", mock_open(read_data=self.text)) as mock_file:
               with open('some/file') as f:
                    assert _raise_validation_error_if_hash_values_differ(f, resource) == None

     def test_with_wrong_hash(self):
          resource = {'package_id':'Test_id', 'hash':'incorrect_hash'}
          with patch("__builtin__.open", mock_open(read_data=self.text)) as mock_file:
               with open('some/file') as f:
                    with nt.assert_raises(logic.ValidationError) as e:
                         _raise_validation_error_if_hash_values_differ(f, resource)
          exception_upload = e.exception.error_dict.get('upload')
          assert exception_upload[0] == 'Berechneter Hash und mitgelieferter Hash sind unterschiedlich'
     
     def test_mock_file(self):
          with patch("__builtin__.open", mock_open(read_data=self.text)) as mock_file:
               with open('some/file') as f:
                    file_content = f.read()
          nt.assert_equal(file_content, self.text)
     
     def test_hash_of_empty_string(self):
          hash_empty_string = 'd41d8cd98f00b204e9800998ecf8427e'
          nt.assert_equal(hash_empty_string, hashlib.md5('').hexdigest())
     
     def test_pdf(self):
          # expected_hash_pdf produced by following command in bash:
          # md5sum test.pdf
          expected_hash_pdf = '66123edf64fabf1c073fc45478bf4a57'
          with open(dir_path + '/resources/test.pdf') as f:
               hash = calculate_hash(f)
          nt.assert_equal(hash, expected_hash_pdf)

               
               
               