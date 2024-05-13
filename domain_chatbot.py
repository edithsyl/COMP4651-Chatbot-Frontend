import streamlit as st
import json
from openai import AzureOpenAI

# Initial message content as a JSON object
initial_content = {
    "isNextState": False,
    "resp": "I am a chatbot to provide personalized weight loss advice. Nice to meet you! 😊",
    "data": ""
}

initial_content['prompt'] = json.dumps(initial_content)

states = {
    'Greeting': {
        'next': 'CollectAge',
        'description': "Greet the user and introduce the chatbot's purpose.",
        'collectedDataName': None  # No data collected in this state
    },
    'CollectAge': {
        'next': 'CollectGender',
        'description': "Ask the user for their age.",
        'collectedDataName': 'age'  # Collecting age
    },
    'CollectGender': {
        'next': 'CollectCurrentWeight',
        'description': "Ask the user for their gender.",
        'collectedDataName': 'gender'  # Collecting gender
    },
    'CollectCurrentWeight': {
        'next': 'CollectHeight',
        'description': "Ask the user for their current weight.",
        'collectedDataName': 'currentWeight'  # Collecting current weight
    },
    'CollectHeight': {
        'next': 'CollectActivityLevel',
        'description': "Ask the user for their height.",
        'collectedDataName': 'height'  # Collecting height
    },
    'CollectActivityLevel': {
        'next': 'CollectGoalWeight',
        'description': "Ask the user about their activity level.",
        'collectedDataName': 'activityLevel'  # Collecting activity level
    },
    'CollectGoalWeight': {
        'next': 'ProvideAdvice',
        'description': "Ask the user for their weight loss goal.",
        'collectedDataName': 'goalWeight'  # Collecting goal weight
    },
    'ProvideAdvice': {
        'next': 'Unhandled',
        'description': "Provide personalized weight loss advice based on the user's inputs.",
        'collectedDataName': None  # No data collected in this state
    },
    'Unhandled': {
        'next': None,
        'description': "Handle any unrelated or unclear inputs by guiding the user back to the conversation or asking for clarification.",
        'collectedDataName': None  # Varies based on the user input
    }
}


def next_state(current_state):
    """
    Determines the next state based on the current state.

    Parameters:
    - current_state: The current state of the conversation.

    Returns:
    - The name of the next state.
    """
    # Get the next state from the current state's information
    next_state = states[current_state]['next']

    # If there's no next state defined, it means we're at the end of the flow or in an unhandled situation
    if not next_state:
        return None

    return next_state


def create_model_prompt(user_content):
    current_state = st.session_state['current_state']
    # Assuming `states` is your state management dictionary
    state_description = states[current_state]['description']
    next_state = states[current_state]['next']
    next_state_description = states[next_state]['description'] if next_state else states[current_state]['description']

    # Assuming `collected_data` is a dictionary holding data collected so far
    collected_data_json = json.dumps(st.session_state.get('user_data', {}))

    prompt = f"""
    Answer with a json object in a string without linebreaks, with a isNextState field as a boolean value, a resp field with text value, a data field as a string value (the value of the current collected data, if applicable, not all the collected data till now).
    You are a chatbot designed to collect user data and provide weight loss suggestions. 
    The current state of your conversation with the user is {current_state}, which means {state_description}. 
    If the goal of the current state is satisfied, the next state is {next_state}, which means {next_state_description}.
    The new response from the user is: {user_content}.
    The collected data is: {collected_data_json}.

    Decide whether the goal of the current state is satisfied. If yes, make isNextState as true, otherwise as false. 
    If the isNextState is true, and the current state is about collecting data, put the collected data value (only the value of the current data collection goal) in the data field, otherwise leave it empty.
    Provide your response to the user in the resp field. 
    If isNextState is true, proceed with the action of the next state (such as asking questions or give the weight loss guidance); otherwise, try to reach the goal by giving a response.   
    """

    return prompt


def get_response_from_model(client):
    # Send the prompt to the model. Assume `client` is your OpenAI API client initialized elsewhere
    print(st.session_state.messages)
    # process st.session_state.messages to make it as {role: string, content: string} format
    msgs = [{"role": m['role'], "content": m['content']['prompt']} for m in st.session_state.messages]
    response = client.chat.completions.create(
        model=model_name,
        messages=msgs,
    )

    # Parse the model's response
    model_response = response.choices[0].message.content

    # to see if the response is a JSON string
    print(model_response)

    # Assuming the model's response is a JSON string; parse it
    response_data = json.loads(model_response)

    return response_data


if 'current_state' not in st.session_state:
    st.session_state['current_state'] = 'Greeting'
    st.session_state['user_data'] = {}

with st.sidebar:
    openai_api_key = st.text_input("Azure OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an Azure OpenAI API key](https://itsc.hkust.edu.hk/services/it-infrastructure/azure-openai-api-service)"

model_name = "gpt-35-turbo"

st.title("💬 Healthcare Chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": initial_content}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"]['resp'])

if user_resp := st.chat_input():
    if not openai_api_key:
        st.info("Please add your Azure OpenAI API key to continue.")
        st.stop()

    st.session_state.messages.append(
        {"role": "user", "content": {'prompt': create_model_prompt(user_resp), 'resp': user_resp}}
    )
    st.chat_message("user").write(user_resp)

    # setting up the OpenAI model
    client = AzureOpenAI(
        api_key=openai_api_key,
        api_version="2023-12-01-preview",
        azure_endpoint="https://hkust.azure-api.net/",
    )
    model_resp = get_response_from_model(client)

    # state transition
    if model_resp['isNextState']:
        if states[st.session_state['current_state']]['collectedDataName']:
            st.session_state['user_data'][states[st.session_state['current_state']]['collectedDataName']] = model_resp[
                'data']
        st.session_state['current_state'] = next_state(st.session_state['current_state'])

    # ensure the consistency
    model_resp['prompt'] = json.dumps(model_resp)

    st.session_state.messages.append({"role": "assistant", "content": model_resp})
    st.chat_message("assistant").write(model_resp['resp'])
