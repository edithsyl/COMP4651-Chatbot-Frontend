import requests
import streamlit as st
import json, time, random # for requests try/except
from apis import apis

# helper function to send request
def sendReq(endpoint: str, body={}, h={'Accept': 'application/json'}, attempt=0):
    st.info(f"sendReq \n endpoint: {endpoint},  \nbody: {body}  \nh: {h}  \nattempt: {attempt}", icon="📮")
    try:
        res = requests.post(endpoint, data=body, headers=h)
        res_obj = res.json() 
    except Exception as err:
        if attempt == 5:
            st.error(f"sendReq failed after 5 attempts", icon="📮")
        st.warning(f"sendReq failed, err: {err}, attempt: {attempt}, res: {res}", icon="📮")
        time.sleep(2**5 + random.random()*0.01) # exponential backoff
        return sendReq(endpoint, body, h, attempt+1)
    else:
        return res_obj

# --------------- auth helper functions start ----------------- #
# FUNC 1: send request for login
def check_credentials():
    # 1. send request to login endpoint
    login_body = {"email": st.session_state["email"], "password": st.session_state["password"]}
    login_r_obj = sendReq(apis.get("LOGIN"), login_body)

    # 2. if login success, aka token is in obj, set session state and user info
    if "token" in login_r_obj:
        st.info(f"login_r_obj: {login_r_obj}", icon="⭐️")
        st.session_state['authentication_status']=True
        st.session_state['login_tok'] = login_r_obj['token']
        st.session_state['username'] = 'alice' # username, user id, token <- decoded from the jwt token (do it later)
        st.rerun() # refresh page
    elif "error" in login_r_obj:
        st.error(f"error: {login_r_obj['error']}", icon="🚨")
    else:
        st.error("invalid")

# FUCN 2: send request for signup
def create_new_user():
    # TODO: 1. connect to backend: call to see if there is duplicated username/ email, if yes, ask for input again
    # 2. post a request to backend: create new user and auto login
    new_user_body = {'username': st.session_state["username"], 'email': st.session_state["email"], 'password': st.session_state["password"]}
    signup_r_obj = sendReq(apis.get("SIGNUP"), new_user_body)
    if "created" in signup_r_obj:
        if signup_r_obj["created"]:
            if "token" in signup_r_obj:
                tokenVal = signup_r_obj["token"]
                st.info(f"token is {tokenVal}", "⭐️")
                st.session_state['authentication_status']=True
                st.session_state['login_tok'] = signup_r_obj["token"]
                st.session_state['username'] = 'alice'
                st.info(f"token is set to {st.session_state['login_tok']}", "䷍")
                st.rerun() # refresh page
            else:
                st.error(f"no token error: {signup_r_obj}", "🚨")
        else:
            st.error(f"created is false error: {signup_r_obj}", "🚨")
    else:
        st.error(f"created does not exist error: {signup_r_obj}", "🚨")

# FUNC 3: delete session_states for logout in sidebar
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

# -------------------- auth helper functions end ---------------------- #

# -------------- auth: login & signup component start ----------------- #
def auth():
    placeholder = st.empty()

    # use tabs to switch between login vs signup
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

# ------------- auth: login & signup component end --------------- #


# check current status to decide show auth component or home interface
if "login_tok" not in st.session_state:
    st.session_state['authentication_status'] = False

# if user is not authenticated => show auth component
if not st.session_state['authentication_status']:
    auth()
elif st.session_state["authentication_status"]: # USER AUTHENTICATION is success => go to Main page
    # ------------- initialize session states start ------------ #
    if 'display' not in st.session_state:
        st.session_state['display'] = 'HOME' # or 'CHATROOM'

    if 'mode' not in st.session_state:
        st.session_state['mode'] = 'chat'

    if 'sessionIds' not in st.session_state:
        # request chat sessions and add to session_state
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {st.session_state['login_tok']}"}
        session_ids_r_obj = sendReq(apis.get("GET-CHAT-SESSIONS"), h=headers)
        if 'sessionIds' in session_ids_r_obj:
            st.session_state['sessionIds'] = session_ids_r_obj['sessionIds']
        elif 'error' in session_ids_r_obj:
            st.error(f"err: {session_ids_r_obj['error']}", icon="🚨")
    # ------------- initialize session states end ---------------- #

    # -------- on click function for past session buttons -------- #
    def openSession_func(s_id: str):
        st.session_state['display'] = 'CHATROOM'
        st.session_state['s_id'] = s_id
        st.session_state['messages'] = [{"role": "user", "content": {"type": "text", "text": "history"}}]
        # the above code is hard coded
        # connect to backend: get chat history and put into messages

        # request s_id session histories
        open_session_headers = {"Content-Type": "application/json", "Authorization": f"Bearer {st.session_state['login_tok']}"}
        open_session_body = {"sessionId": s_id}

        session_hists_r = sendReq(apis.get("GET-CHAT-HISTORIES"), body=open_session_body, h=open_session_headers) # ERROR: don't know why it return string "<Response [400]>"
        st.session_state['wtf'] = session_hists_r
        session_hists_r_obj = session_hists_r.__str__()
        st.warning(f"session_hists_r: {session_hists_r_obj}", icon="🔥")

        # ERROR: I comment out below code becoz session_hists_r err is unresolved
        # st.write(f'session_hists_r_obj: {session_hists_r_obj}') #test
        # if 'histories' in session_hists_r_obj:
        #     st.session_state['histories'] = session_hists_r_obj['histories']
        # elif 'error' in session_ids_r_obj:
        #     st.error(st.session_state['error'], icon="🚨")

        st.session_state['mode'] = "chat" # hard coded
        # connect to backend: get chat history as well as the session mode

    # ------ on click function for create new session button ------ #
    def createSession_func(mode):
        # 1. set endpoint depending on mode
        endpoint = None
        if mode=="TRANSLATE":
            endpoint=apis.get("CREATE-TRANSLATE-SESSION")
        if mode=="CHAT":
            endpoint=apis.get("CREATE-CHAT-SESSION")
        else:
            endpoint=apis.get("CREATE-CHAT-SESSION") # default

        # 2. request create new session
        create_session_headers = {"Content-Type": "application/json", "Authorization": f"Bearer {st.session_state['login_tok']}"}
        create_session_r_obj = sendReq(endpoint, h=create_session_headers)

        # 3. check if response contains sessionId
        # ---- Yes => success, add the sessionId to session_state
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

    # -------------------- on click functions end -------------------- #

    # --------------------- home interface start --------------------- #
    with st.sidebar:
        # logout button
        st.button('logout', on_click=logout_func) 

        st.title("Chatrooms")

        # buttons for select mode and create new session
        mode = st.radio("Select mode for new chat session", ["chat", "translate"])
        newchat = st.button('➕ Create', use_container_width=100, on_click=createSession_func, args=(mode,)) # create new session button
        
        # past session buttons
        for session_id in st.session_state['sessionIds']:
            st.button(session_id, use_container_width=100, on_click=openSession_func, args=(session_id,))

    # content on main page
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