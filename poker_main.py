import streamlit as st
from poker_pages import login_page, room, in_room, game
from poker_action import init_server_state

def init():
    if 'state' not in st.session_state:
        st.session_state.state = 'login'
    if 'chips' not in st.session_state:
        st.session_state.chips = 2000
    if 'name' not in st.session_state:
        st.session_state.name = None
    init_server_state()

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