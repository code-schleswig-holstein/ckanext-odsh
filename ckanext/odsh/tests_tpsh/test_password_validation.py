# encoding: utf-8

import nose.tools as nt
from ckanext.odsh.logic.action import check_password

class Test_PasswordValidation(object):

    @staticmethod
    def assert_password_invalid(password):
        assert not check_password(password)
    
    @staticmethod
    def assert_password_valid(password):
        assert check_password(password)
    
    def test_valid_password(self):
        self.assert_password_valid('Passwort1 :) :P :D')
    
    def test_umlaute(self):
        self.assert_password_valid('Pässword')
    
    def test_no_uppercase(self):
        self.assert_password_invalid('passwort1')
    
    def test_no_lowercase(self):
        self.assert_password_invalid('PASSWORT1')
    
    def test_no_letters(self):
        self.assert_password_invalid('37459073245!!?===))/=$§äüöÄÜÖ')
    
    def test_only_letters(self):
        self.assert_password_invalid('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
    
    def test_to_short(self):
        self.assert_password_invalid('Pw123')