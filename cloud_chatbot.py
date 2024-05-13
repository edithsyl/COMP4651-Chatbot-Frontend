import json
import random
import requests
import streamlit as st
import textract

import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from pathlib import Path

from openai import AzureOpenAI
from io import StringIO

"st.session_state object:", st.session_state      # for testing

apis = {
    "CHAT": "https://httpbin.org/get",# "https://v1/chat",
    "TRANSLATE": "https://httpbin.org/get",# "https://v1/translate",
    # "DRAW":  "https://httpbin.org/get",# "https://v1/media",
    # "MUSIC": "https://httpbin.org/get",#  "https://v1/music",
}

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

# with session_file_path.open("rb") as file:
#     sessions = yaml.load(file, Loader=SafeLoader)

# Create the authenticator object
authenticator = stauth.Authenticate(    
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# retrieve the name, authentication status, and username from Streamlit's session state using st.session_state["name"], st.session_state["authentication_status"], and st.session_state["username"]
authenticator.login()

if st.session_state["authentication_status"] == False:
    st.error("Username/password is incorrect")

if st.session_state["authentication_status"] == None:
    st.warning("Please enter your username and password")

if st.session_state["authentication_status"]: # USER AUTHENTICATION is success

    

# ------ MAIN PAGE ----- #

    if 'display' not in st.session_state:
        st.session_state['display'] = 'HOME' # or 'CHATROOM'

    if 'mode' not in st.session_state:
        st.session_state['mode'] = 'chat'

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
        authenticator.logout()  

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
        st.subheader("Welcome, "+st.session_state["name"])
        # Chat, Translate = st.tabs(["💬 Chat", "🗣️ Translate"])
        st.caption("Start a new chat below")
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role":"assistant", "content": {"type":"text", "text": "welcome!!"}}]

        for msg in st.session_state.messages:
            st.chat_message(msg['role']).write(msg["content"]["text"])

        if user_resp := st.chat_input("say something"):
            # if not open_api_key:
            #     st.info("Please add your Azure OpenAI API key to continue.")
            #     st.stop()
            st.session_state['messages'].append({"role": "user", "content":{"type":"text" ,"text":user_resp }})
            st.chat_message("user").write(user_resp)

    elif st.session_state['display'] == 'CHATROOM':
        st.subheader("Welcome to chat session: "+st.session_state['s_id'])
        for msg in st.session_state.messages:
            st.chat_message(msg['role']).write(msg["content"]["text"])
        if user_resp := st.chat_input("say something"):
            # if not open_api_key:
            #     st.info("Please add your Azure OpenAI API key to continue.")
            #     st.stop()
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
        # r = requests.post(apis.get(st.session_state['mode']), data=test)
        # st.caption("print r: "+r.text)
        # --------- sending requests ---------
        
        # --------- from original code ---------
        # if "messages" not in st.session_state:
        #     st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

        # for msg in st.session_state.messages:
        #     st.chat_message(msg["role"]).write(msg["content"])

        # if prompt := st.chat_input():
        #     if not openai_api_key:
        #         st.info("Please add your Azure OpenAI API key to continue.")
        #         st.stop()

        #     st.session_state.messages.append(
        #         {"role": "user", "content": prompt}
        #     )
        #     st.chat_message("user", avatar="🙋‍♂️").write(prompt)

        #     # setting up the OpenAI model
        #     client = AzureOpenAI(
        #         api_key=openai_api_key,
        #         api_version="2023-12-01-preview",
        #         azure_endpoint="https://hkust.azure-api.net/",
        #     )
        #     response = client.chat.completions.create(
        #         model=model_name,
        #         messages=st.session_state.messages
        #     )

        #     msg = response.choices[0].message.content
        #     st.session_state.messages.append({"role": "assistant", "content": msg})
        #     st.chat_message("assistant").write(msg)
            # --------- from original code end ---------