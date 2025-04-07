import os
from datetime import datetime  # 🔥 FIXED: Import datetime for timestamps
import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
from google.generativeai import configure as gemini_configure, GenerativeModel
import groq
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

# Initialize models
def init_models():
    # Groq client
    groq_api_key = MODEL_API_KEYS["groq"]
    if groq_api_key:
        st.session_state.groq_client = groq.Client(api_key=groq_api_key)
    
    # Gemini
    gemini_api_key = MODEL_API_KEYS["gemini"]
    if gemini_api_key:
        gemini_configure(api_key=gemini_api_key)
        st.session_state.gemini_model = GenerativeModel("gemini-pro")
    
    # DeepSeek
    deepseek_api_key = MODEL_API_KEYS["deepseek"]
    if deepseek_api_key:
        st.session_state.deepseek_client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"
        )

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
            # Placeholder for OpenAI (update if using real API)
            return f"GPT-3.5 response to: {prompt}"

        else:
            return f"Model {st.session_state.current_model} not properly configured"
    
    except Exception as e:
        return f"Error generating response: {str(e)}"

# Main Chat UI
def show_chat_ui():
    st.title("VerseAI")
    st.markdown("### A Multiverse of AI Models")

    # Model selector
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

    # Sidebar
    with st.sidebar:
        st.header("Chat History")
        if st.button("Clear Current Chat"):
            st.session_state.generated = []
            st.session_state.past = []

        st.subheader("Previous Conversations")
        for model, history in st.session_state.model_history.items():
            if history:
                with st.expander(f"{model} Chats"):
                    for i, chat in enumerate(history[-5:]):
                        if st.button(f"Chat {i+1} - {model}"):
                            st.session_state.current_model = model
                            st.session_state.past = chat['past']
                            st.session_state.generated = chat['generated']
                            st.rerun()

    # Chat input/output
    response_container = st.container()
    input_container = st.container()

    with input_container:
        with st.form(key='input_form', clear_on_submit=True):
            user_input = st.text_area("You:", key='input', height=100)
            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            output = generate_response(user_input)

            st.session_state.past.append(user_input)
            st.session_state.generated.append(output)

            # Save conversation
            st.session_state.model_history[st.session_state.current_model].append({
                "past": st.session_state.past.copy(),
                "generated": st.session_state.generated.copy(),
                "timestamp": datetime.now().isoformat()  # ✅ Works now
            })

    # Show messages
    if st.session_state.generated:
        with response_container:
            for i in range(len(st.session_state.generated)):
                message(st.session_state.past[i], is_user=True, key=str(i) + '_user')
                message(st.session_state.generated[i], key=str(i))

# Run the app
def main():
    init_session_state()
    init_models()
    show_chat_ui()

if __name__ == "__main__":
    main()
