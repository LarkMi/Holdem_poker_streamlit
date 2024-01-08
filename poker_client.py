import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh
import os
from threading import Thread
from poker_sever import sever_run


if 'id_psw' not in os.listdir():
    t = Thread(target=sever_run)
    t.start()

url = 'http://127.0.0.1:5678'

def login():

    name = str(st.text_input(label='输入用户名:'))
    pwd = str(st.text_input(label='输入密码:'))
    col1, col2 = st.columns(2)
    with col1:
        if st.button(label='登录'):
            req = requests.post(url='{}/login'.format(url),json={'name':name,'pwd':pwd})
            if req.text == 'login success':
                st.session_state.state = 'room'
                st.session_state.name = name
                st.rerun()
            else:
                st.warning(req.text)
    with col2:
        if st.button('注册'):
            req = requests.post(url='{}/signup'.format(url),json={'name':name,'pwd':pwd}).text
            st.warning(req)

def room():
    rooms = requests.get('{}/room'.format(url)).json()
    choose_room = st.radio('选择要加入的房间:',options=rooms)
    if choose_room:
        choose_room = choose_room[:choose_room.index(' ')]
    
        if st.button(label='加入'):
            req = requests.post(url='{}/join_room'.format(url),json={'room_name':choose_room,'player_name':st.session_state.name}).text
            if req == 'join success':
                st.session_state.state = 'in_room'
                st.session_state.room = choose_room
            elif req == 'join game':
                st.session_state.state = 'game'
                st.session_state.room = choose_room
            else:
                st.warning('该房间已满员')
    
    create_room = st.text_input(label='输入创建的房间名:')
    if st.button(label='创建'):
        req = requests.post(url='{}/create_room'.format(url),json={'room_name':create_room,'player_name':st.session_state.name}).text
        if req == 'create success':
            st.session_state.room = create_room
            st.session_state.state = 'in_room'
        else:
            st.warning('该房间已存在')


def in_room():
    col1, col2 = st.columns(2)
    with col1:
        st.title('**Room: {}**'.format(st.session_state.room))
    with col2:
        if st.button('退出'):
            requests.post('{}/exit_room'.format(url),json={'room_name':st.session_state.room,'name':st.session_state.name})
            st.session_state.state = 'room'
            return
    req = requests.post(url='{}/get_room_info'.format(url),json={'room_name':st.session_state.room,'name':st.session_state.name,'chips':st.session_state.chips}).json()
    #st.write(req)
    st.header('以下玩家已加入')
    for each in req['players']:
        if each == req['owner']:
            st.write('***{}**'.format(each))
        else:
            st.write(each)
    st.session_state.players = req['players']
    st.session_state.chips = st.slider('带入筹码量:',min_value =2000, max_value=10000, step =1000)
    if req['game'] != None:
        
        if req['game'] == 1:
            st.session_state.state = 'game'
            return             
        if st.button('加入游戏'):
            requests.post(url='{}/join_game'.format(url),json={'room_name':st.session_state.room,'name':st.session_state.name,'buy_in':st.session_state.chips}).json()
            st.session_state.state = 'game'
        return 
    if st.session_state.name == req['owner']:
        if st.button('开始'):
            if len(req['players']) == 1 or len(req['players']) > 8:
                st.warning('人数需要在2 - 8人')
            else:
                #time.sleep(1)
                requests.post(url='{}/start_game'.format(url),json={'room_name':st.session_state.room})
                st.session_state.state = 'game'
    else:
        st.subheader('等待游戏开始')

@st.cache_data
def encode_cards(cards:list):
    #cards: [(1,2),(2,3)]
    decors = [':red[♥',':red[♦','♠','♣']
    s = ['J','Q','K','A']
    for i in range(len(cards)):
        size, decor = cards[i]
        if size >= 11:
            size = s[size-11]
        cards[i] = '{}{}{}'.format(decors[decor-1],size,']' if decor < 3 else '')
    #print(' '.join(cards))
    return ' '.join(cards)

def action(act):
    requests.post('{}/action'.format(url),json={'room_name':st.session_state.room,'player':st.session_state.name,'action':act})

def game():
    col1, col2 = st.columns(2)
    with col2:
        st.divider()
        if st.button('退出'):
            requests.post('{}/exit_room'.format(url),json={'room_name':st.session_state.room,'name':st.session_state.name})
            st.session_state.state = 'room'
            return 
    games_info = requests.post('{}/get_game_info'.format(url),json={'room_name':st.session_state.room}).json()
    with col1:
        st.title('**Room: {}**——第{}局'.format(st.session_state.room,games_info['game_count']))

    if st.session_state.name not in games_info['players_in_game'] and st.session_state.name not in games_info['add_player']:
        st.session_state.state = 'in_room'
        return 
    game_page(games_info)

def game_page(games_info):
    #st.write(games_info)
    my_name = st.session_state.name
    
    #st.write(games_info)
    
    public_cards = games_info['public_cards']
    hand_cards = games_info['hand_cards']
    
    public_cards = encode_cards(public_cards)
    
    col1, col2 = st.columns(2)
    with col1:
        container = st.container(border=True)
        container.subheader('公共牌: {}'.format(public_cards))
    with col2:
        container = st.container(border=True)
        container.subheader('底池: {}'.format(games_info['pot']))
    for each in hand_cards:
        hand_cards[each] = encode_cards(hand_cards[each])
    players = games_info['players_in_game'].copy()
    if my_name in players:
        players = players[players.index(my_name):] + players[:players.index(my_name)]
    #players.sort(key = lambda x : list(games_info['buy_in'].keys()).index(x))
    cols = st.columns(len(players))
    for i in range(len(cols)):
        with cols[i]:
            container = st.container(border=True)
            if players[i] == games_info['player_to_action']:
                container.write('▼')
            elif games_info['chips'][players[i]] <= 0:
                container.write('**:red[All in]**')
            elif players[i] in games_info['players']:
                container.write('**-**')
            else:
                container.write('**×**')
            container.text('{}'.format(players[i]))
            
            position = games_info['players_in_game'].index(players[i])
            betted_chips = games_info['bet_chip'][players[i]]-games_info['max_bet_now']
            #betted_chips = 0
            if position == 0:
                container.caption('小盲')
            elif position == len(players) -1 :
                container.caption('庄家')
            elif position == 1:
                container.caption('大盲')
            else:
                container.caption('.')
            if games_info['state'] != 'finished':
                if players[i] in games_info['players']:
                    container.caption(':red[+{}]'.format(betted_chips))
            container.caption('筹码: {}'.format(games_info['chips'][players[i]]))
            if players[i] == my_name or games_info['state'] == 'finished':
                container.write(hand_cards[players[i]])
            else:
                container.write('**&nbsp;?&nbsp;?**')
    if st.session_state.name == games_info['player_to_action']:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button('弃牌'):
                action(-2)
        if games_info['max_bet'] >= games_info['chips'][my_name] + games_info['bet_chip'][my_name]:
            with col2:
                if st.button('All in {}'.format(games_info['chips'][my_name])):
                    action(games_info['chips'][my_name])
        else:
            with col2:
                if st.button('跟注 {}'.format(games_info['max_bet']-games_info['bet_chip'][my_name])):
                    action(games_info['max_bet']-games_info['bet_chip'][my_name])        
            with col3:
                if games_info['mini_bet'] >= games_info['chips'][my_name]:
                    if st.button('All in {}'.format(games_info['chips'][my_name])):
                        action(games_info['chips'][my_name])
                else:
                    act = st.number_input(label=' ',min_value=min(games_info['mini_bet']+games_info['max_bet']-games_info['bet_chip'][my_name],games_info['chips'][my_name]),max_value=games_info['chips'][my_name],step=20)
                    if st.button('加注 {}'.format(act)):
                        action(act)
    
    with st.sidebar:
        container = st.container(border=True)
        container.subheader('总成绩:')
        for each in games_info['ini_chips']:
            grade = games_info['ini_chips'][each] - games_info['buy_in'][each]
            container.write('{}: :{}[{}{}]'.format(each,'red' if grade >= 0 else 'green','+' if grade >= 0 else '',grade))
        container = st.container(border=True)
        last_game = games_info['last_game']
        if last_game['names'] != {}:
            container.subheader('上一局结果:')
            container.write('公共牌: {}'.format(encode_cards(last_game['public_cards'])))
            last_game = last_game['names']
            for each in last_game:
                grade = last_game[each]['grade']
                container.write('{}: {} {} :{}{}]'.format(each,encode_cards(last_game[each]['hand_cards']),last_game[each]['type'],'red[+' if grade >=0 else 'green[',grade))
        
def init():
    if 'state' not in st.session_state:
        st.session_state.state = 'login'
    if 'chips' not in st.session_state:
        st.session_state.chips = 2000


if __name__ == '__main__':
    #st.write(st.session_state)
    init()
    with st.sidebar:
        st.title('德州扑克')
        if st.session_state.state != 'login':
            st.header('User: {}'.format(st.session_state.name))
            
    match st.session_state.state:
        case 'login':
            login()
        case 'room':
            room()
        case 'in_room':
            in_room()        
        case 'game':
            game()
    
    st_autorefresh(interval=800, limit=1000000, key="fizzbuzzcounter")

    