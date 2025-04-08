import os
from datetime import datetime
import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
import groq

# Load environment variables
load_dotenv()

# Configuration
MODELS = {
    "Gemma2-9b-it": "GEMMA",
    "Llama3-8b-8192": "META LLAMA 3",
    "llama-3.1-8b-instant": "META LLAMA 3.1",
    "Llama3-70b-8192": "META LLAMA 3.2",
    "llama-3.3-70b-versatile": "META LLAMA 3.3",
}
MODEL_API_KEYS = {
    "groq": os.getenv("GROQ_API_KEY")
}

# Initialize session state
def init_session_state():
    if 'current_model' not in st.session_state:
        st.session_state.current_model = list(MODELS.keys())[0]

    if 'verseai_model_history' not in st.session_state:
        st.session_state.verseai_model_history = {model: [] for model in MODELS.keys()}

    if 'verseai_generated' not in st.session_state:
        st.session_state.verseai_generated = []

    if 'verseai_past' not in st.session_state:
        st.session_state.verseai_past = []

# Initialize models
def init_models():
    # Groq client
    groq_api_key = MODEL_API_KEYS.get("groq")
    if groq_api_key:
        st.session_state.groq_client = groq.Client(api_key=groq_api_key)
    else:
        st.error("GROQ_API_KEY not found in environment variables")

# Generate response
def generate_response(prompt: str) -> str:
    try:
        completion = st.session_state.groq_client.chat.completions.create(
            model=st.session_state.current_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return completion.choices[0].message.content

    except Exception as e:
        return f"Error generating response: {str(e)}"

# Main Chat UI
def show_chat_ui():
    st.set_page_config(page_icon="֎", layout="wide", page_title="VerseAI")
    st.title("֎ VerseAI")  # Added icon to the title as well
    st.markdown("<h5 style='font-size: 1em;'>A Multiverse of AI</h5>", unsafe_allow_html=True)

    # Model selector
    current_model_display_name = st.selectbox(
        "Pick your AI:",
        options=list(MODELS.values()),
        index=list(MODELS.values()).index(MODELS.get(st.session_state.current_model, list(MODELS.values())[0])),
        key="model_selector"
    )

    # Determine the actual model ID based on the selected display name
    selected_model_id = [key for key, value in MODELS.items() if value == current_model_display_name][0]

    # Check if model changed
    if selected_model_id != st.session_state.current_model:
        st.session_state.current_model = selected_model_id
        st.session_state.verseai_generated = []
        st.session_state.verseai_past = []
        st.rerun()

    # Sidebar
    with st.sidebar:
        st.header("Chat History")
        if st.button("Clear Current Chat"):
            st.session_state.verseai_generated = []
            st.session_state.verseai_past = []

        st.subheader("Previous Convos")
        for model_id, history in st.session_state.verseai_model_history.items():
            if history:
                display_name = MODELS.get(model_id, model_id)  # Get custom name or fallback
                with st.expander(f"{display_name} Chats"):
                    for i, chat in enumerate(history):
                        chat_title = chat.get('timestamp', f'Chat {i+1}')
                        if st.button(f"{chat_title} - {display_name}", key=f"load_chat_{model_id}_{i}"):
                            st.session_state.current_model = model_id
                            st.session_state.verseai_past = chat['past']
                            st.session_state.verseai_generated = chat['generated']
                            st.rerun()
                    if st.button(f"Delete All {display_name} Chats", key=f"delete_all_{model_id}"):
                        del st.session_state.verseai_model_history[model_id]
                        st.rerun()

    # Chat input/output
    response_container = st.container()
    input_container = st.container()

    with input_container:
        prompt = st.chat_input("Wyd? Lemme know...")
        if prompt:
            output = generate_response(prompt)
            st.session_state.verseai_past.append(prompt)
            st.session_state.verseai_generated.append(output)

            # Save conversation
            st.session_state.verseai_model_history[st.session_state.current_model].append({
                "past": st.session_state.verseai_past.copy(),
                "generated": st.session_state.verseai_generated.copy(),
                "timestamp": datetime.now().isoformat()
            })

    # Show messages
    if st.session_state.verseai_generated:
        with response_container:
            for i in range(len(st.session_state.verseai_generated)):
                message(st.session_state.verseai_past[i], is_user=True, key=str(i) + '_user')
                message(st.session_state.verseai_generated[i], key=str(i))

# Run the app
def main():
    init_session_state()
    init_models()
    show_chat_ui()

if __name__ == "__main__":
    main()
