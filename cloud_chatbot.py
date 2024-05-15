import requests
import streamlit as st
import json, time, random # for requests try/except
from apis import apis

def sendReq(endpoint: str, body: dict, headers={'Accept': 'application/json'}, attempt=0):
    try:
        res = requests.post(endpoint, data=body, headers=headers)
        res_obj = res.json() 
    except Exception as err: #(requests.exceptions.ConnectionError, ValueError, json.decoder.JSONDecodeError):
        st.warning(f"sendReq failed, err: {err}, attempt: {attempt}, res: {res}", icon="📮")
        time.sleep(2**5 + random.random()*0.01) #exponential backoff
        return sendReq(endpoint, body, headers, attempt+1)
    else:
        return res_obj

# # ---------- custom login widget end ------------
def check_credentials():
    login_body = {"email": st.session_state["email"], "password": st.session_state["password"]}
    # headers = {'Accept': 'application/json'}
    # login_r = requests.post(apis.get("LOGIN"), data=login_body, headers={'Accept': 'application/json'})
    # login_r_obj = login_r.json() 

    login_r_obj = sendReq(apis.get("LOGIN"), login_body)
    st.info(f"login_r_obj: {login_r_obj}")
    if "token" in login_r_obj:
        # login success, set session state and user info
        st.error(f"login_r_obj: {login_r_obj}", icon="🚨")
        st.session_state['authentication_status']=True
        st.session_state['login_tok'] = login_r_obj['token']
        # username, user id, token <- decoded from the jwt token (do it later)
        st.session_state['username'] = 'alice'
        st.rerun()
    elif "error" in login_r_obj:
        st.error(f"error: {login_r_obj['error']}", icon="🚨")
    else:
        st.error("invalid")

def create_new_user():
    new_user_body = {'username': st.session_state["username"], 'email': st.session_state["email"], 'password': st.session_state["password"]}
    # connect to backend: call to see if there is duplicated username/ email
    # if yes, ask for input again
    # else post a request to backend: create new user and auto login
    # signup_r = requests.post(apis.get("SIGNUP"), data=new_user_body, headers={'Accept': 'application/json'})
    signup_r_obj = sendReq(apis.get("SIGNUP"), new_user_body)# signup_r.json() 
    if "created" in signup_r_obj:
        if signup_r_obj["created"]:
            if "token" in signup_r_obj:
                st.session_state['authentication_status']=True
                st.session_state['login_tok'] = signup_r_obj["token"]
                st.session_state['username'] = 'alice'
                st.rerun()
            else:
                st.error(f"no token error: {signup_r_obj}", "🚨")
        else:
            st.error(f"created is false error: {signup_r_obj}", "🚨")
    else:
        st.error(f"created does not exist error: {signup_r_obj}", "🚨")


# ---------- def login page-----#
def login():
    placeholder = st.empty()
    tabLogin, tabSignup = placeholder.tabs(['login', 'sign up'])
    with tabLogin:
        login_form = tabLogin.form('Login', clear_on_submit=False)
        
        login_form.subheader('Login')
        st.session_state["email"] = login_form.text_input('Email').lower()
        st.session_state["password"] = login_form.text_input('Password', type='password')
        lg = login_form.form_submit_button('Login')
        if lg: 
            check_credentials()

    with tabSignup:
        signup_form = tabSignup.form("Sign Up", clear_on_submit=False)
        signup_form.subheader("Sign Up")
        st.session_state["username"] = signup_form.text_input('username')
        st.session_state["email"] = signup_form.text_input('Email').lower()
        st.session_state["password"] = signup_form.text_input('Password', type='password')
        su = signup_form.form_submit_button("Sign Up")
        if su:
            create_new_user()

def logout_func():
    st.session_state['authentication_status']=False
    st.session_state['username'] = ""
    st.session_state['email'] = ""
    st.session_state['password'] = ""
    if "login_tok" in st.session_state:
        del st.session_state["login_tok"]
    if "messages" in st.session_state:
        del st.session_state["messages"]
    if "mode" in st.session_state:
        del st.session_state["mode"]
    if "display" in st.session_state:
        del st.session_state["display"]
    if "sessionIds" in st.session_state:
        del st.session_state["sessionIds"]

if "login_tok" not in st.session_state:
    st.session_state['authentication_status'] = False
if not st.session_state['authentication_status']:
    login()

# ----- login page end here -----#

elif st.session_state["authentication_status"]: # USER AUTHENTICATION is success => go to Main page
# ------ MAIN PAGE ----- #
    if 'display' not in st.session_state:
        st.session_state['display'] = 'HOME' # or 'CHATROOM'

    if 'mode' not in st.session_state:
        st.session_state['mode'] = 'chat'

    if 'session_history' not in st.session_state:
        # request chat sessions and add to session_state
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {st.session_state['login_tok']}"}
        session_ids_r = requests.post(apis.get("GET-CHAT-SESSIONS"), headers=headers)
        session_ids_r_obj = session_ids_r.json() 
        if 'sessionIds' in session_ids_r_obj:
            st.session_state['sessionIds'] = session_ids_r_obj['sessionIds']
        elif 'error' in session_ids_r_obj:
            st.error(st.session_state['error'], icon="🚨")

    # ------ function for  ------ #
    def openSession(s_id: str):
        st.session_state['display'] = 'CHATROOM'
        st.session_state['s_id'] = s_id
        st.session_state['messages'] = [{"role": "user", "content": {"type": "text", "text": "history"}}]
        # the above code is hard coded
        # connect to backend: get chat history and put into messages

        # request s_id session histories
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {st.session_state['login_tok']}"}
        body = {"sessionId": s_id}
        session_hists_r = requests.post(apis.get("GET-CHAT-HISTORIES"), headers=headers, data=body) # ERROR: don't know why it return string "<Response [400]>"
        st.session_state['wtf'] = session_hists_r
        session_hists_r_obj = session_hists_r.__str__()
        st.warning(f"session_hists_r: {session_hists_r_obj}", icon="🔥")
        # session_hists_r_obj = session_hists_r.json()  # ERROR: comment out becoz session_hists_r err is unresolved
        # st.write(f'session_hists_r_obj: {session_hists_r_obj}') #test
        # if 'histories' in session_hists_r_obj:
        #     st.session_state['histories'] = session_hists_r_obj['histories']
        # elif 'error' in session_ids_r_obj:
        #     st.error(st.session_state['error'], icon="🚨")

        st.session_state['mode'] = "chat" # hard coded
        # connect to backend: get chat history as well as the session mode
        
    
    def createSession(mode):
        # 1. set endpoint depending on mode
        endpoint = None
        if mode=="TRANSLATE":
            endpoint=apis.get("CREATE-TRANSLATE-SESSION")
        if mode=="CHAT":
            endpoint=apis.get("CREATE-CHAT-SESSION")
        else:
            endpoint=apis.get("CREATE-CHAT-SESSION") # default
        # 2. request create new session
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {st.session_state['login_tok']}"}
        create_session_r = requests.post(endpoint, headers=headers)

        # 3. check if response contains sessionId
        # ---- Yes => success, add the sessionId to session_state
        create_session_r_obj = create_session_r.json() 
        if 'sessionId' in create_session_r_obj:
            st.session_state['s_id'] = create_session_r_obj['sessionId']
            st.session_state['sessionIds'].append(create_session_r_obj['sessionId'])
        elif 'error' in create_session_r_obj:
            st.error(st.session_state['error'], icon="🚨")

        st.session_state['display'] = 'HOME'
        st.session_state['mode'] = mode

        # 4. remove previous messages from other session
        if 'messages' in st.session_state:
            del st.session_state['messages']

        st.write(st.session_state['s_id'])
        st.write(st.session_state['mode'])
    # ------------- func end ------------- #
    
    with st.sidebar:
        st.button('logout', on_click=logout_func) # logout button

        st.title("Chatrooms")

        # select mode when creating new session
        mode = st.radio("Select mode for new chat session", ["chat", "translate"])
        newchat = st.button('➕ Create', use_container_width=100, on_click=createSession, args=(mode,)) # create new session button
        
        # past session buttons
        for session_id in st.session_state['sessionIds']:
            st.button(session_id, use_container_width=100, on_click=openSession, args=(session_id,))

    model_name = "gpt-35-turbo"
    if st.session_state['display'] == 'HOME':
        st.subheader("Welcome, "+st.session_state["login_tok"])
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




"st.session_state object:", st.session_state      # for testing