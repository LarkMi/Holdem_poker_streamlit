import streamlit as st

from streamlit_server_state import server_state, server_state_lock, force_rerun_bound_sessions
from collections import defaultdict


st.session_state.room = st.text_input('room:')

with server_state_lock['rooms']:
    if 'rooms' not in server_state:
        server_state['rooms'] = defaultdict(list)

with server_state_lock[st.session_state.room]:
    if st.session_state.room not in server_state:
        pass

if st.button('test'):
    with server_state_lock[st.session_state.room]:
        server_state.rooms[st.session_state.room].append(1)
    force_rerun_bound_sessions(st.session_state.room)

st.write("Count = ", server_state['rooms'])