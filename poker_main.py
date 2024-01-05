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
    
    room_list = pickle.load(open('room','rb'))
    
    room = st.radio(
        "选择游戏房间",
        key="visibility",
        options=room_list,
    )
    
    new_room = st.text_input(label='创建房间:')
    if st.button('创建'):
        if new_room not in room_list:
            room_list.append(new_room)
            pickle.dump(room_list,open('room','wb'))
        else:
            st.warning('房间已存在')
    
if __name__ == '__main__':
    if 'room' not in os.listdir():
        pickle.dump([],open('room','wb'))
    st.write(st.session_state)
    if 'login' not in st.session_state:
        login()
    else:
        main()