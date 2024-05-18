import requests
import streamlit as st
import time, random # for requests try/except

# helper function to send request
def sendReq(endpoint: str, body={}, h={'Accept': 'application/json'}, attempt=0):
    # st.info(f"sendReq \n endpoint: {endpoint},  \nbody: {body}  \nh: {h}  \nattempt: {attempt}", icon="📮") # test
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