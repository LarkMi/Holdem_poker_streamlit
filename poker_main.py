import streamlit as st
from poker_pages import login_page, room, in_room, game
from poker_action import init_server_state
from streamlit import session_state


def init():
    if 'state' not in session_state:
        session_state.state = 'login'
    if 'chips' not in session_state:
        session_state.chips = 2000
    if 'name' not in session_state:
        session_state.name = None
    if 'room' not in session_state:
        session_state.room = 'null'
    if 'game_count' not in session_state:
        session_state.game_count = 1
    init_server_state()

if __name__ == '__main__':
    #st.write(session_state)
    init()
    with st.sidebar:
        st.title('德州扑克')
        if session_state.state != 'login':
            st.header('User: {}'.format(session_state.name))

    if session_state.state == 'login':
        login_page()
    elif session_state.state == 'room':
        room()
    elif session_state.state == 'in_room':
        in_room()        
    elif session_state.state == 'game':
        game()
        
