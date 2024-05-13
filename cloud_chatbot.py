import json
import random
import requests
import streamlit as st
import textract

# custom login component
import time
from typing import Optional
from streamlit_authenticator.utilities.validator import Validator
from streamlit_authenticator.utilities.exceptions import DeprecationError
from streamlit_authenticator.authenticate.cookie import CookieHandler
from streamlit_authenticator.authenticate.authentication import AuthenticationHandler
from customAuthentication import CustomAuthenticationHandler
from customCookie import CustomCookieHandler
# custom login component

import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from pathlib import Path

from openai import AzureOpenAI
from io import StringIO

from apis import apis

"st.session_state object:", st.session_state      # for testing

# ---------- def custom login widget ------------
class CustomAuthenticate:
    def __init__(self):
        """
        Create a new instance of "Authenticate".
        """
        self.authentication_handler     =   CustomAuthenticationHandler()
        self.cookie_handler             =   CustomCookieHandler("random_cookie_name", "random_signature_key", 30)


    def customLogin(self, location: str='main', max_concurrent_users: Optional[int]=None,
                max_login_attempts: Optional[int]=None, fields: dict=None,
                clear_on_submit: bool=False) -> tuple:
            """
            Creates a login widget.

            Parameters
            ----------
            location: str
                Location of the login widget i.e. main or sidebar.
            max_concurrent_users: int
                Maximum number of users allowed to login concurrently.
            max_login_attempts: int
                Maximum number of failed login attempts a user can make.
            fields: dict
                Rendered names of the fields/buttons.
            clear_on_submit: bool
                Clear on submit setting, True: clears inputs on submit, False: keeps inputs on submit.

            Returns
            -------
            str
                Name of the authenticated user.
            bool
                Status of authentication, None: no credentials entered, 
                False: incorrect credentials, True: correct credentials.
            str
                Username of the authenticated user.
            """
            if fields is None:
                fields = {'Form name':'Custom Login', 'Email':'Email', 'Password':'Password','Login':'Login'}
            if location not in ['main', 'sidebar']:
                # Temporary deprecation error to be displayed until a future release
                raise DeprecationError("""Likely deprecation error, the 'form_name' parameter has been replaced with the 'fields' parameter. For further information please 
                    refer to https://github.com/mkhorasani/Streamlit-Authenticator/tree/main?tab=readme-ov-file#authenticatelogin""")
                # raise ValueError("Location must be one of 'main' or 'sidebar'")
            if not st.session_state['authentication_status']:
                token = self.cookie_handler.get_cookie()
                if token:
                    self.authentication_handler.execute_login(token=token)
                time.sleep(0.7)
                if not st.session_state['authentication_status']:
                    login_form = st.form('Login', clear_on_submit=clear_on_submit)
                    
                    login_form.subheader('Login' if 'Form name' not in fields else fields['Form name'])
                    email = login_form.text_input('Email' if 'Email' not in fields
                        else fields['Email']).lower()
                    password = login_form.text_input('Password' if 'Password' not in fields
                        else fields['Password'], type='password')
                    if login_form.form_submit_button('Login' if 'Login' not in fields
                        else fields['Login'], on_click=self.authentication_handler.check_credentials, args=(email, password, )):
                        
                        if st.session_state['authentication_status'] == True:
                            # self.authentication_handler.execute_login(email=email)
                            self.cookie_handler.set_cookie()
            return (st.session_state['name'], st.session_state['authentication_status'],
                    st.session_state['email'])
    
    def logout(self, button_name: str='Logout', location: str='main', key: Optional[str]=None):
        """
        Creates a logout button.

        Parameters
        ----------
        button_name: str
            Rendered name of the logout button.
        location: str
            Location of the logout button i.e. main or sidebar or unrendered.
        key: str
            Unique key to be used in multi-page applications.
        """
        if location not in ['main', 'sidebar','unrendered']:
            raise ValueError("Location must be one of 'main' or 'sidebar' or 'unrendered'")
        if location == 'main':
            if st.button(button_name, key):
                self.authentication_handler.execute_logout()
                self.cookie_handler.delete_cookie()
        elif location == 'sidebar':
            if st.sidebar.button(button_name, key):
                self.authentication_handler.execute_logout()
                self.cookie_handler.delete_cookie()
        elif location == 'unrendered':
            if st.session_state['authentication_status']:
                self.authentication_handler.execute_logout()
                self.cookie_handler.delete_cookie()

# ---------- custom login widget end ------------

# ------ USER AUTHENTICATION ----- #
# Import the YAML dummy file
file_path = Path(__file__).parent / "user_credentials.yaml"
# session_file_path = Path(__file__).parent / "sessions.yaml"
# connect to backend: get all sessions from that user (post: get session ID by user)
# current hardcode:
sessions = {"sessionIds": [
        "6641e7a9a9af8ede1899ea75",
        "6641e7a9a9af8ede1899ea76",
        "6641ed29a77b0206c5675339"]}

with file_path.open("rb") as file:
    config = yaml.load(file, Loader=SafeLoader)

# custom
cauth = CustomAuthenticate()
cauth.customLogin()

if st.session_state["authentication_status"] == False:
    st.error("Email/password is incorrect")

if st.session_state["authentication_status"] == None:
    st.warning("Please enter your email and password")

if st.session_state["authentication_status"]: # USER AUTHENTICATION is success


# ------ MAIN PAGE ----- #

    if 'display' not in st.session_state:
        st.session_state['display'] = 'HOME' # or 'CHATROOM'

    if 'mode' not in st.session_state:
        st.session_state['mode'] = 'chat'

    if 'session_history' not in st.session_state:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {st.session_state['login_tok']}"}
        session_history_r = requests.post(apis.get("GET-CHAT-SESSIONS"), headers=headers)
        session_history_r_obj = session_history_r.json() 
        st.session_state['session_history'] = session_history_r_obj

    # ------ function for  ------ #
    def openSession(s_id):
        st.session_state['display'] = 'CHATROOM'
        st.session_state['s_id'] = s_id
        st.session_state['messages'] = [{"role": "user", "content": {"type": "text", "text": "history"}}]
        # the above code is hard coded
        # connect to backend: get chat history and put into messages
        st.session_state['mode'] = "chat" # hard coded
        # connect to backend: get chat history as well as the session mode
        
    
    def createSession(u_id, mode):
        st.session_state['display'] = 'HOME'
        st.session_state['s_id'] = str(len(sessions['sessionIds'])+1)
        st.session_state['mode'] = mode
        sessions['sessionIds'].append(str(len(sessions['sessionIds'])+1))
        if 'messages' in st.session_state:
            del st.session_state['messages']
        # the above line of code is hard coded
        # connect to backend: use the user id to generate a new session
        st.write(st.session_state['s_id'])
        st.write(st.session_state['mode'])

    
    with st.sidebar:
        # buttons
        cauth.logout()  

        # generate session buttons
        st.title("Chatrooms")
        user_id = 1 # hard code user id

        mode = st.radio("Select mode for new chat session", ["chat", "translate"])
        newchat = st.button('➕ Create', use_container_width=100, on_click=createSession, args=(user_id, mode,))
        
        
        for session_id in sessions['sessionIds']:
            st.button(session_id, use_container_width=100, on_click=openSession, args=(session_id,))

        # openai_api_key = st.text_input("Azure OpenAI API Key", key="chatbot_api_key", type="password")
        # "[Get an Azure OpenAI API key](https://itsc.hkust.edu.hk/services/it-infrastructure/azure-openai-api-service)"


    model_name = "gpt-35-turbo"
    if st.session_state['display'] == 'HOME':
        st.subheader("Welcome, "+st.session_state["login_tok"])
        # Chat, Translate = st.tabs(["💬 Chat", "🗣️ Translate"])
        st.caption("Start a new chat below")
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role":"assistant", "content": {"type":"text", "text": "welcome!!"}}]

        for msg in st.session_state.messages:
            st.chat_message(msg['role']).write(msg["content"]["text"])

        if user_resp := st.chat_input("say something"):
            st.session_state['messages'].append({"role": "user", "content":{"type":"text" ,"text":user_resp }})
            st.chat_message("user").write(user_resp)

    elif st.session_state['display'] == 'CHATROOM':
        st.subheader("Welcome to chat session: "+st.session_state['s_id'])
        for msg in st.session_state.messages:
            st.chat_message(msg['role']).write(msg["content"]["text"])
        if user_resp := st.chat_input("say something"):
            st.session_state['messages'].append({"role": "user", "content":{"type":"text" ,"text":user_resp }})
            st.chat_message("user").write(user_resp)
        
            
        # --------- sending requests ---------
        d = {  
                'id': 'value1', 
                'userId': 'value2',
                'sessionId': 'CHAT',
                'input':{
                    'role': 'user',
                    'content': {
                        'type': 'text',
                        'url': 'url',
                        'prompt': 'prompt'
                    }
                }
            }
        test = {"firstName": "John", "lastName": "Smith"}
