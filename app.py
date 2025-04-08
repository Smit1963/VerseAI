import os
from datetime import datetime
import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
import groq

# Load environment variables
load_dotenv()

# Configuration - All available Groq models
MODELS = {
    "Llama3-8b-8192": "groq",
    "Llama3-70b-8192": "groq",
    "Mixtral-8x7b-Instruct-v0.1": "groq",
    "Gemma2-9b-it": "groq",
}

MODEL_API_KEYS = {
    "groq": os.getenv("GROQ_API_KEY")
}

# Initialize session state
def init_session_state():
    if 'current_model' not in st.session_state:
        st.session_state.current_model = list(MODELS.keys())[0]  # Default to the first model

    if 'model_history' not in st.session_state:
        st.session_state.model_history = {model: [] for model in MODELS.keys()}

    if 'generated' not in st.session_state:
        st.session_state.generated = []

    if 'past' not in st.session_state:
        st.session_state.past = []

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
    st.title("Groq AI Chat")
    st.markdown("### Fast LLMs powered by Groq")

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
                    for i, chat in enumerate(history):
                        chat_title = chat.get('timestamp', f'Chat {i+1}')
                        if st.button(f"{chat_title} - {model}", key=f"load_chat_{model}_{i}"):
                            st.session_state.current_model = model
                            st.session_state.past = chat['past']
                            st.session_state.generated = chat['generated']
                            st.rerun()
                    if st.button(f"Delete All {model} Chats", key=f"delete_all_{model}"):
                        del st.session_state.model_history[model]
                        st.rerun()

    # Chat input/output
    response_container = st.container()
    input_container = st.container()

    with input_container:
        with st.form(key='input_form'):  # Removed clear_on_submit for persistent input
            user_input = st.text_area("You:", key='input', height=100)
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                # Type here feature is the default behavior of st.text_area
                pass
            with col2:
                submit_button = st.form_submit_button(label='✈️ Send') # Aeroplane emoji

            if submit_button and user_input:
                output = generate_response(user_input)
                st.session_state.past.append(user_input)
                st.session_state.generated.append(output)

                # Save conversation
                st.session_state.model_history[st.session_state.current_model].append({
                    "past": st.session_state.past.copy(),
                    "generated": st.session_state.generated.copy(),
                    "timestamp": datetime.now().isoformat()
                })
                st.session_state["input"] = "" # Clear the input area after sending

        # Implement Enter key to send
        st.markdown(
            """
            <script>
                const inputElement = document.querySelector('#input_form textarea');
                inputElement.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        const submitButton = document.querySelector('#input_form button[type="submit"]');
                        submitButton.click();
                    }
                });
            </script>
            """,
            unsafe_allow_html=True,
        )

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
