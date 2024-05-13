"""
Script description: This module executes the logic for the login, logout, register user,
reset password, forgot password, forgot username, and modify user details widgets. 

Libraries imported:
- streamlit: Framework used to build pure Python web applications.
- typing: Module implementing standard typing notations for Python functions.
"""

from typing import Optional
import streamlit as st

from streamlit_authenticator.utilities.hasher import Hasher
from streamlit_authenticator.utilities.validator import Validator
from streamlit_authenticator.utilities.helpers import Helpers
from streamlit_authenticator.utilities.exceptions import (CredentialsError,
                                  ForgotError,
                                  LoginError,
                                  RegisterError,
                                  ResetError,
                                  UpdateError)


import requests
from apis import apis

import json

class CustomAuthenticationHandler:
    """
    This class will execute the logic for the login, logout, register user, reset password, 
    forgot password, forgot username, and modify user details widgets.
    """
    login_t = None

    def __init__(self, validator: Optional[Validator]=None):
        """
        Create a new instance of "AuthenticationHandler".

        Parameters
        ----------
        credentials: dict
            Dictionary of usernames, names, passwords, emails, and other user data.
        pre-authorized: list
            List of emails of unregistered users who are authorized to register.        
        validator: Validator
            Validator object that checks the validity of the username, name, and email fields.
        """
        # self.credentials                =   credentials
        # self.pre_authorized             =   pre_authorized
        # self.credentials['usernames']   =   {
        #                                     key.lower(): value
        #                                     for key, value in credentials['usernames'].items()
        #                                     }
        self.validator                  =   validator if validator is not None else Validator()

        if 'name' not in st.session_state:
            st.session_state['name'] = None
        if 'authentication_status' not in st.session_state:
            st.session_state['authentication_status'] = None
        if 'email' not in st.session_state:
            st.session_state['email'] = None
        if 'logout' not in st.session_state:
            st.session_state['logout'] = None

    def check_credentials(self, email: str, password: str) -> bool:
        """
        Checks the validity of the entered credentials.

        Parameters
        ----------
        email: str
            The entered email.
        password: str
            The entered password.

        Returns
        -------
        bool
            Validity of the entered credentials.
        """
        if email is not None:
            try:
                # --------- sending login requests ---------
                test = {"email": email, "password": password}
                login_r = requests.post(apis.get("LOGIN"), data=test)
                "login_r:", login_r.text     # for testing
                login_r_obj = login_r.json() 
                if login_r_obj["token"] is not None:
                    self.login_t = login_r_obj["token"] 
                    # st.session_state['authentication_status'] = True
                    return True
                else:
                    # st.session_state['authentication_status'] = False
                    raise RegisterError(login_r_obj["error"] )
                    return False
            except TypeError as e:
                print(e)
            except ValueError as e:
                print(e)
        else:
            st.session_state['authentication_status'] = False
            return False
        return None
    
    
    def _credentials_contains_value(self, value: str) -> bool:
        """
        Checks to see if a value is present in the credentials dictionary.

        Parameters
        ----------
        value: str
            Value being checked.

        Returns
        -------
        bool
            Presence/absence of the value, True: value present, False value absent.
        """
        return any(value in d.values() for d in self.credentials['usernames'].values())
    
    def execute_login(self, email: Optional[str]=None, token: Optional[dict]=None):
        """
        Executes login by setting authentication status to true and adding the user's
        username and name to the session state.

        Parameters
        ----------
        email: str
            The email of the user being logged in.
        token: dict
            The re-authentication cookie to retrieve the username from.
        """
        if st.session_state['FormSubmitter:Login-Login'] == True:
            st.session_state['email'] = email
            st.session_state['name'] =  self.login_t # self.credentials['email'][email]['name'] 
            st.session_state['authentication_status'] = True
            # self._record_failed_login_attempts(username, reset=True)
            # self.credentials['emails'][email]['logged_in'] = True
        # elif token:
        #     st.session_state['username'] = token['username']
        #     st.session_state['name'] = self.credentials['usernames'][token['username']]['name']
        #     st.session_state['authentication_status'] = True
        #     self.credentials['usernames'][token['username']]['logged_in'] = True

    def execute_logout(self):
        """
        Clears cookie and session state variables associated with the logged in user.
        """
        # self.credentials['usernames'][st.session_state['email']]['logged_in'] = False
        st.session_state['logout'] = True
        st.session_state['name'] = None
        st.session_state['email'] = None
        st.session_state['authentication_status'] = None
    def forgot_password(self, username: str) -> tuple:
        """
        Creates a new random password for the user.

        Parameters
        ----------
        username: str
            Username associated with the forgotten password.

        Returns
        -------
        tuple
            Username of the user; email of the user; new random password of the user.
        """
        if not self.validator.validate_length(username, 1):
            raise ForgotError('Username not provided')
        if username in self.credentials['usernames']:
            return (username, self.credentials['usernames'][username]['email'],
                    self._set_random_password(username))
        else:
            return False, None, None
    def forgot_username(self, email: str) -> tuple:
        """
        Retrieves the forgotten username of a user.

        Parameters
        ----------
        email: str
            Email associated with the forgotten username.

        Returns
        -------
        tuple
            Username of the user; email of the user.
        """
        if not self.validator.validate_length(email, 1):
            raise ForgotError('Email not provided')
        return self._get_username('email', email), email
    def _get_username(self, key: str, value: str) -> str:
        """
        Retrieves the username based on a provided entry.

        Parameters
        ----------
        key: str
            Name of the credential to query i.e. "email".
        value: str
            Value of the queried credential i.e. "jsmith@gmail.com".

        Returns
        -------
        str
            Username associated with the given key, value pair i.e. "jsmith".
        """
        for email, values in self.credentials['usernames'].items():
            if values[key] == value:
                return email
        return False
    def _record_failed_login_attempts(self, email: str, reset: bool=False):
        """
        Records the number of failed login attempts for a given username.
        
        Parameters
        ----------
        reset: bool            
            Reset failed login attempts option, True: number of failed login attempts
            for the user will be reset to 0, 
            False: number of failed login attempts for the user will be incremented.
        """
        if reset:
            self.credentials['emails'][email]['failed_login_attempts'] = 0
        else:
            self.credentials['emails'][email]['failed_login_attempts'] += 1

    def _register_credentials(self, email: str, name: str, password: str, pre_authorization: bool, domains: list):
        """
        Adds the new user's information to the credentials dictionary.

        Parameters
        ----------
        username: str
            Username of the new user.
        name: str
            Name of the new user.
        password: str
            Password of the new user.
        email: str
            Email of the new user.
        pre-authorization: bool
            Pre-authorization requirement, True: user must be pre-authorized to register, 
            False: any user can register.
        domains: list
            Required list of domains a new email must belong to i.e. ['gmail.com', 'yahoo.com'], 
            list: the required list of domains, None: any domain is allowed.
        """
        if not self.validator.validate_email(email):
            raise RegisterError('Email is not valid')
        if self._credentials_contains_value(email):
            raise RegisterError('Email already taken')
        if domains:
            if email.split('@')[1] not in ' '.join(domains):
                raise RegisterError('Email not allowed to register')
        if not self.validator.validate_username(username):
            raise RegisterError('Username is not valid')
        if username in self.credentials['usernames']:
            raise RegisterError('Username already taken')
        if not self.validator.validate_name(name):
            raise RegisterError('Name is not valid')
        self.credentials['usernames'][username] = \
            {'name': name, 'password': Hasher([password]).generate()[0], 'email': email,
             'logged_in': False}
        if pre_authorization:
            self.pre_authorized['emails'].remove(email)
    def register_user(self, new_password: str, new_password_repeat: str, pre_authorization: bool,
                      new_username: str, new_name: str, new_email: str,
                      domains: Optional[list]=None) -> tuple:
        """
        Validates a new user's username, password, and email. Subsequently adds the validated user 
        details to the credentials dictionary.

        Parameters
        ----------
        new_password: str
            Password of the new user.
        new_password_repeat: str
            Repeated password of the new user.
        pre-authorization: bool
            Pre-authorization requirement, True: user must be pre-authorized to register, 
            False: any user can register.
        new_username: str
            Username of the new user.
        new_name: str
            Name of the new user.
        new_email: str
            Email of the new user.
        domains: list
            Required list of domains a new email must belong to i.e. ['gmail.com', 'yahoo.com'], 
            list: the required list of domains, None: any domain is allowed.

        Returns
        -------
        tuple
            Email of the new user; username of the new user; name of the new user.
        """
        if not self.validator.validate_length(new_password, 1) \
            or not self.validator.validate_length(new_password_repeat, 1):
            raise RegisterError('Password/repeat password fields cannot be empty')
        if new_password != new_password_repeat:
            raise RegisterError('Passwords do not match')
        if pre_authorization:
            if new_email in self.pre_authorized['emails']:
                self._register_credentials(new_username, new_name, new_password, new_email,
                                            pre_authorization, domains)
                return new_email, new_username, new_name
            else:
                raise RegisterError('User not pre-authorized to register')
        else:
            self._register_credentials(new_username, new_name, new_password, new_email,
                                        pre_authorization, domains)
            return new_email, new_username, new_name

    def reset_password(self, username: str, password: str, new_password: str,
                       new_password_repeat: str) -> bool:
        """
        Validates the user's current password and subsequently saves their new password to the 
        credentials dictionary.

        Parameters
        ----------
        username: str
            Username of the user.
        password: str
            Current password of the user.
        new_password: str
            New password of the user.
        new_password_repeat: str
            Repeated new password of the user.

        Returns
        -------
        bool
            State of resetting the password, True: password reset successfully.
        """
        if self.check_credentials(username, password):
            if not self.validator.validate_length(new_password, 1):
                raise ResetError('No new password provided')
            if new_password != new_password_repeat:
                raise ResetError('Passwords do not match')
            if password != new_password:
                self._update_password(username, new_password)
                return True
            else:
                raise ResetError('New and current passwords are the same')
        else:
            raise CredentialsError('password')
    def _set_random_password(self, username: str) -> str:
        """
        Updates the credentials dictionary with the user's hashed random password.

        Parameters
        ----------
        username: str
            Username of the user to set the random password for.

        Returns
        -------
        str
            New plain text password that should be transferred to the user securely.
        """
        self.random_password = Helpers.generate_random_pw()
        self.credentials['usernames'][username]['password'] = \
            Hasher([self.random_password]).generate()[0]
        return self.random_password
    def _update_entry(self, username: str, key: str, value: str):
        """
        Updates the credentials dictionary with the user's updated entry.

        Parameters
        ----------
        username: str
            Username of the user to update the entry for.
        key: str
            Updated entry key i.e. "email".
        value: str
            Updated entry value i.e. "jsmith@gmail.com".
        """
        self.credentials['usernames'][username][key] = value
    def _update_password(self, username: str, password: str):
        """
        Updates the credentials dictionary with the user's hashed reset password.

        Parameters
        ----------
        username: str
            Username of the user to update the password for.
        password: str
            Updated plain text password.
        """
        self.credentials['usernames'][username]['password'] = Hasher([password]).generate()[0]
    def update_user_details(self, new_value: str, username: str, field: str) -> bool:
        """
        Validates the user's updated name or email and subsequently modifies it in the
        credentials dictionary.

        Parameters
        ----------
        new_value: str
            New value for the name or email.
        username: str
            Username of the user.
        field: str
            Field to update i.e. name or email.

        Returns
        -------
        bool
            State of updating the user's detail, True: details updated successfully.
        """
        if field == 'name':
            if not self.validator.validate_name(new_value):
                raise UpdateError('Name is not valid')
        if field == 'email':
            if not self.validator.validate_email(new_value):
                raise UpdateError('Email is not valid')
            if self._credentials_contains_value(new_value):
                raise UpdateError('Email already taken')
        if new_value != self.credentials['usernames'][username][field]:
            self._update_entry(username, field, new_value)
            if field == 'name':
                st.session_state['name'] = new_value
            return True
        else:
            raise UpdateError('New and current values are the same')
        
    def getLoginT(self)->str:
        return self.login_t