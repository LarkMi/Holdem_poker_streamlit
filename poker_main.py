import streamlit as st


def login():
    name = st.text_input(label='输入用户名:')
    if st.button('登录'):
        st.session_state['login'] = name
        st.experimental_rerun()
        
def main():
    with st.sidebar:
        st.header('德州扑克')
        st.write('User: {}'.format(st.session_state['login']))
    
if __name__ == '__main__':
    st.write(st.session_state)
    if 'login' not in st.session_state:
        login()
    else:
        main()