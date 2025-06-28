import streamlit as st
from chatbot import answer_query  # Instead of answer_query_with_langchain
import time

# Configure page
st.set_page_config(
    page_title="Rajagiri Chatbot",
    page_icon="🏫",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .stChatInput {
        bottom: 20px;
    }
    .stChatMessage {
        padding: 12px 16px;
        border-radius: 15px;
        margin-bottom: 8px;
    }
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] > [data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
    .header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header with college logo
st.markdown('<div class="header"><h1>🏫 Rajagiri College Assistant</h1><p>Ask me about admissions, courses, facilities, placements and more!</p></div>', unsafe_allow_html=True)

# Initialize chat history
if "history" not in st.session_state:
    st.session_state.history = []
    st.session_state.last_query = None

# Suggested questions
suggested_questions = [
    "What are the undergraduate courses offered?",
    "How do I apply for admission?",
    "What are the hostel facilities?",
    "Tell me about placement statistics",
    "What's the fee structure for MBA?"
]

# Display suggested questions
st.markdown("**Try asking:**")
cols = st.columns(2)
for i, question in enumerate(suggested_questions):
    with cols[i % 2]:
        if st.button(question, use_container_width=True):
            st.session_state.last_query = question

# Chat input
query = st.chat_input("Ask me anything about Rajagiri College...")

# Use the suggested question if clicked
current_query = query if query else st.session_state.last_query

if current_query:
    # Clear the last query after using it
    st.session_state.last_query = None
    
    # Add user message to history
    st.session_state.history.append(("user", current_query))
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(current_query)
    
    # Generate response
    with st.spinner("Searching Rajagiri resources..."):
        start_time = time.time()
        answer = answer_query(current_query)
        processing_time = time.time() - start_time
        
        # Add slight delay for natural feel if response was fast
        if processing_time < 2:
            time.sleep(1.5)
        
        # Add assistant response to history
        st.session_state.history.append(("assistant", answer))
    
    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(answer)

# Display chat history (without the last query if it's being processed)
for role, message in st.session_state.history[:-2 if current_query else None]:
    with st.chat_message(role):
        st.markdown(message)