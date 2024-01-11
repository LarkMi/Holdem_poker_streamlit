import streamlit as st
from poker_pages import login_page, room, in_room, game
from poker_action import init_server_state
from streamlit_server_state import server_state, server_state_lock
from collections import defaultdict
from streamlit.runtime.runtime import Runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx



session_id = get_script_run_ctx().session_id
st.write(Runtime.instance()._session_mgr.get_session_info(session_id))  # type: ignore  # noqa: E501

st.write(Runtime.instance()._session_mgr.get_session_info(session_id) is None)

def init():
    if 'state' not in st.session_state:
        st.session_state.state = 'login'
    if 'chips' not in st.session_state:
        st.session_state.chips = 2000
    if 'name' not in st.session_state:
        st.session_state.name = None
    if "rooms" not in server_state:
        with server_state_lock["rooms"]:
            server_state.rooms = defaultdict(dict)

if __name__ == '__main__':
    #st.write(st.session_state)
    init()
    with st.sidebar:
        st.title('德州扑克')
        if st.session_state.state != 'login':
            st.header('User: {}'.format(st.session_state.name))

    
    if st.session_state.state == 'login':
        login_page()
    elif st.session_state.state == 'room':
        room()
    elif st.session_state.state == 'in_room':
        in_room()        
    elif st.session_state.state == 'game':
        game()
        
