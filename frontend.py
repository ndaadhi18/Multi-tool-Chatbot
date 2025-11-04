import streamlit as st
from backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid


# **************************** UTILITY-FUNCS ********************
def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id':thread_id}})
    return state.values.get('messages', [])

def delete_conversation(thread_id):
    try:
        chatbot.checkpointer.remove({"configurable": {"thread_id": thread_id}})
    except Exception as e:
        print("Error removing from DB:", e)

    if thread_id in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].remove(thread_id)

    if st.session_state.get("thread_id") == thread_id:
        reset_chat()
    else:
        st.rerun()




# **************************** SESSION-SETUP ********************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

add_thread(st.session_state['thread_id'])

# ****************************** SIDE-BAR **********************
st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('➕ New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for idx, thread_id in enumerate(st.session_state['chat_threads'][::-1], start=1):
    label = f"Conversation {idx}"

    # Use container for neat layout
    with st.sidebar.container():
        row = st.container()
        col1, col2 = row.columns([6, 1])

        with col1:
            if st.button(label, key=f"thread_{thread_id}", use_container_width=True):
                st.session_state['thread_id'] = thread_id
                messages = load_conversation(thread_id)

                formatted = []
                for msg in messages:
                    role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
                    formatted.append({'role': role, 'content': msg.content})
                st.session_state['message_history'] = formatted
                st.rerun()

        with col2:
            delete_clicked = st.button("🗑", key=f"delete_{thread_id}", help="Delete conversation", use_container_width=True)

            if delete_clicked:
                delete_conversation(thread_id)



# ***************************** MAIN-UI ************************
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

user_input = st.chat_input('Type Here')

if user_input:
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {"thread_id": st.session_state["thread_id"]},
        "run_name": "chat_turn",
    }

    with st.chat_message("assistant"):
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )