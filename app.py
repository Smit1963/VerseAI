import os
import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
import httpx
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from google.generativeai import configure as gemini_configure, GenerativeModel
import groq
from jose import jwt
from passlib.context import CryptContext
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
MODELS = {
    "Llama3-8b-8192": "groq",
    "Llama3-70b-8192": "groq",
    "Gemini-Pro": "gemini",
    "Gemma-7b": "groq",
    "DeepSeek": "deepseek",
    "GPT-3.5": "openai"
}

MODEL_API_KEYS = {
    "groq": os.getenv("GROQ_API_KEY"),
    "gemini": os.getenv("GEMINI_API_KEY"),
    "deepseek": os.getenv("DEEPSEEK_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY")
}

# Authentication setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# User model
class User:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = pwd_context.hash(password)

# Mock database
fake_users_db = {
    "admin": User("admin", "admin"),
    "user": User("user", "password")
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    if username not in fake_users_db:
        return False
    user = fake_users_db[username]
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None

# Initialize session state
def init_session_state():
    if 'current_model' not in st.session_state:
        st.session_state.current_model = "Llama3-8b-8192"
    
    if 'model_history' not in st.session_state:
        st.session_state.model_history = {model: [] for model in MODELS.keys()}
    
    if 'generated' not in st.session_state:
        st.session_state.generated = []
    
    if 'past' not in st.session_state:
        st.session_state.past = []
    
    if 'token' not in st.session_state:
        st.session_state.token = None
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'user' not in st.session_state:
        st.session_state.user = None

# Initialize models
def init_models():
    # Initialize Groq client
    groq_api_key = MODEL_API_KEYS["groq"]
    if groq_api_key:
        st.session_state.groq_client = groq.Client(api_key=groq_api_key)
    
    # Initialize Gemini
    gemini_api_key = MODEL_API_KEYS["gemini"]
    if gemini_api_key:
        gemini_configure(api_key=gemini_api_key)
        st.session_state.gemini_model = GenerativeModel("gemini-pro")
    
    # Initialize DeepSeek
    deepseek_api_key = MODEL_API_KEYS["deepseek"]
    if deepseek_api_key:
        st.session_state.deepseek_client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"
        )

# Authentication UI
def show_auth_ui():
    st.title("VerseAI - Login")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                user = authenticate_user(username, password)
                if user:
                    token = create_access_token({"sub": username})
                    st.session_state.token = token
                    st.session_state.logged_in = True
                    st.session_state.user = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")
            
            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords don't match")
                elif new_username in fake_users_db:
                    st.error("Username already exists")
                else:
                    fake_users_db[new_username] = User(new_username, new_password)
                    st.success("Registration successful! Please login.")

# Generate response
def generate_response(prompt: str) -> str:
    model_provider = MODELS[st.session_state.current_model]
    
    try:
        if model_provider == "groq":
            completion = st.session_state.groq_client.chat.completions.create(
                model=st.session_state.current_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return completion.choices[0].message.content
        
        elif model_provider == "gemini":
            response = st.session_state.gemini_model.generate_content(prompt)
            return response.text
        
        elif model_provider == "deepseek":
            response = st.session_state.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        
        elif model_provider == "openai":
            # Placeholder for OpenAI API
            return f"GPT-3.5 response to: {prompt}"
        
        else:
            return f"Model {st.session_state.current_model} not properly configured"
    
    except Exception as e:
        return f"Error generating response: {str(e)}"

# Main Chat UI
def show_chat_ui():
    st.title("VerseAI")
    st.markdown("### A Multiverse of AI Models")
    
    # Model selection dropdown
    current_model = st.selectbox(
        "Select AI Model",
        options=list(MODELS.keys()),
        index=list(MODELS.keys()).index(st.session_state.current_model),
        key="model_selector"
    )
    
    # Check if model changed
    if current_model != st.session_state.current_model:
        st.session_state.current_model = current_model
        st.session_state.generated = []
        st.session_state.past = []
        st.rerun()
    
    # Sidebar for chat history
    with st.sidebar:
        st.header("Chat History")
        if st.button("Clear Current Chat"):
            st.session_state.generated = []
            st.session_state.past = []
        
        st.subheader("Previous Conversations")
        for model, history in st.session_state.model_history.items():
            if history:
                with st.expander(f"{model} Chats"):
                    for i, chat in enumerate(history[-5:]):  # Show last 5 chats per model
                        if st.button(f"Chat {i+1} - {model}"):
                            st.session_state.current_model = model
                            st.session_state.past = chat['past']
                            st.session_state.generated = chat['generated']
                            st.rerun()
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
    
    # Chat container
    response_container = st.container()
    input_container = st.container()
    
    # User input form
    with input_container:
        with st.form(key='input_form', clear_on_submit=True):
            user_input = st.text_area("You:", key='input', height=100)
            submit_button = st.form_submit_button(label='Send')
        
        if submit_button and user_input:
            output = generate_response(user_input)
            
            st.session_state.past.append(user_input)
            st.session_state.generated.append(output)
            
            # Save to model history
            st.session_state.model_history[st.session_state.current_model].append({
                "past": st.session_state.past.copy(),
                "generated": st.session_state.generated.copy(),
                "timestamp": datetime.now().isoformat()
            })
    
    # Display chat messages
    if st.session_state.generated:
        with response_container:
            for i in range(len(st.session_state.generated)):
                message(st.session_state.past[i], is_user=True, key=str(i) + '_user')
                message(st.session_state.generated[i], key=str(i))

# Main app
def main():
    init_session_state()
    
    if not st.session_state.logged_in:
        show_auth_ui()
    else:
        init_models()
        show_chat_ui()

if __name__ == "__main__":
    main()
