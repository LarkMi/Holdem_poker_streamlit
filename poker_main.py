import streamlit as st
import pickle
import os

def login():
    name = st.text_input(label='输入用户名:')
    if st.button('登录'):
        st.session_state['login'] = name
        st.experimental_rerun()
        
def main():
    with st.sidebar:
        st.header('德州扑克')
        st.write('User: {}'.format(st.session_state['login']))
    
    room = st.radio(
        "选择游戏房间",
        key="visibility",
        options=pickle.load('room'),
    )
    
if __name__ == '__main__':
    if 'room' not in os.listdir():
        pickle.dump([],open('room','wb'))
    st.write(st.session_state)
    if 'login' not in st.session_state:
        login()
    else:
        main()