"use strict";

function isPasswordValid(password) {
    if (password.length == 0) return true;
    var minimumLength = 8;
    var isValid = 
        (password.length >= minimumLength) &&
        (atLeastOneUpperCaseLetter(password)) &&
        (atLeastOneLowerCaseLetter(password)) &&
        (atLeastOneNoneLetter(password));
    return isValid

    function atLeastOneUpperCaseLetter(password) {
        return (password !== password.toLowerCase())
    }

    function atLeastOneLowerCaseLetter(password) {
        return (password !== password.toUpperCase())
    }

    function atLeastOneNoneLetter(password) {
        return /[\W\d_]/.test(password)
    }
}


function showPasswordStatus(isValid, inputElement) {
    if (isValid) {
        messageText = '';
    } else {
        messageText = 'Passwörter müssen länger als 8 Zeichen sein und Großbuchstaben, Kleinbuchstaben und andere Zeichen enthalten.'
    }
    get_error_element(inputElement).innerHTML = messageText;

    function get_error_element(inputElement) {
        // assumes that there is an element after input_element's parent that
        // contains a class "inline-error"
        var currentNode = inputElement.parentNode
        do {
            currentNode = currentNode.nextElementSibling;
        } while (
            (currentNode !== null) &&
            !(currentNode.classList.contains('inline-error'))
        )
        return currentNode
    }
}


function setSubmitButtonState(isPasswordValid) {
    var submitButton = document.getElementsByName('save')[0];
    submitButton.disabled = !isPasswordValid;
}


ckan.module('tpsh_validate_password', function ($) {
    return {
        initialize: function () {
            $.proxyAll(this, /_on/);
            this.el.on('input', this._onChange);
        },
        
        _onChange: function(event) {
            var inputElement = event.target;
            var newPassword = inputElement.value;
            var isValid = isPasswordValid(newPassword);
            showPasswordStatus(isValid, inputElement);
            setSubmitButtonState(isValid);
        }
    };
});