import streamlit as st
from copy import deepcopy
from poker_action import signup, login, get_rooms, restart_thread, create_room, join_room, get_room_info, refreash_buyin, exit_room, start_game, get_game_info, action, join_game, restart_game
from streamlit import session_state
import time
from threading import Thread

def login_page():
    
    name = str(st.text_input(label='输入用户名:'))
    pwd = str(st.text_input(label='输入密码:'))
    col1, col2 = st.columns(2)
    with col1:
        if st.button(label='登录'):
            req = login(name,pwd)
            if req == 'login success':
                session_state.state = 'room'
                session_state.name = name
                st.rerun()
            else:
                st.warning(req)
    with col2:
        if st.button('注册'):
            req = signup(name,pwd)
            st.warning(req)

def room():
    #st.write(server_state.rooms)
    rooms = get_rooms()
    choose_room = st.radio('选择要加入的房间:',options=rooms)
    if choose_room:
        choose_room = choose_room[:choose_room.rindex(' ')]
    
        if st.button(label='加入'):
            req = join_room(choose_room,session_state.name)
            if req == 'join fail':
                st.warning('该房间已满员')
    
    room_name = st.text_input(label='输入创建的房间名:')
    if st.button(label='创建'):
        req = create_room(str(room_name),session_state.name)
        if req == 'create success':
            session_state.room = room_name
            session_state.state = 'in_room'
            st.rerun()
        else:
            st.warning('该房间已存在')


def in_room():
    col1, col2 = st.columns(2)
    with col1:
        st.title('**Room: {}**'.format(session_state.room))
    with col2:
        st.divider()
        if st.button('退出'):
            exit_room(session_state.room,session_state.name)
            session_state.state = 'room'
            return
    req = get_room_info(session_state.room,session_state.name,session_state.chips)
    #st.write(req)
    st.write('**以下玩家已加入:**')
    for each in req['players']:
        if each == req['owner']:
            st.write('***{}**    买入: {}'.format(each,req['buy_in'][each]))
        else:
            st.write('{}    买入: {}'.format(each,req['buy_in'][each]))
    session_state.players = req['players']
    st.slider('带入筹码量:',key='chips',value=2000,min_value =2000, max_value=10000, step =1000,on_change=refreash_buyin)

    if req['game'] != None:
        session_state.game_count = req['game_count']

        if req['game'] == 1:
            session_state.state = 'game'
            st.rerun()
            return
        with st.sidebar:
            container = st.container(border=True)
            write_last_game(container,req['last_game'])
        
        if st.button('加入游戏'):
            join_game(session_state.room,session_state.name,session_state.chips)
            session_state.state = 'game'
        return 
    if session_state.name == req['owner']:
        if st.button('开始'):
            if len(req['players']) == 1 or len(req['players']) > 8:
                st.warning('人数需要在2 - 8人')
            else:
                #time.sleep(1)
                start_game(session_state.room)
    else:
        st.write('**等待房主开始游戏……**')

def encode_cards(cards:list):
    #cards: [(1,2),(2,3)]
    cards = deepcopy(cards)
    if not cards: return ''
    if type(cards[0]) == str:
        return ' '.join(cards)
    decors = [':red[♥',':red[♦','♠','♣']
    s = ['J','Q','K','A']
    for i in range(len(cards)):
        size, decor = cards[i]
        if size >= 11:
            size = s[size-11]
        cards[i] = '{}{}{}'.format(decors[decor-1],size,']' if decor < 3 else '')
    return ' '.join(cards)

def game():
    col1, col2 = st.columns(2)
    with col2:
        st.divider()
        if st.button('退出'):
            exit_room(session_state.room,session_state.name)
            return 
    games_info = get_game_info(session_state.room)
    with col1:
        st.title('**Room: {}**——第{}局'.format(session_state.room,games_info['game_count'])) 
    game_page(games_info)



def game_page(games_info):
    #st.write(games_info)
    my_name = session_state.name
    
    #st.write(games_info)
    
    public_cards = deepcopy(games_info['public_cards'])
    hand_cards = deepcopy(games_info['hand_cards'])
    
    public_cards = encode_cards(public_cards).split(' ')

    if public_cards  == ['']:
        public_cards = []
        session_state.public_cards = []
    
    col1, col2 = st.columns(2)
    with col1:
        container = st.container(border=True)
        container.subheader('公共牌: {}'.format(' '.join(session_state.public_cards)))
    
    if len(public_cards) != len(session_state.public_cards):
        session_state.public_cards.append(public_cards[len(session_state.public_cards)])
        
        time.sleep(1.5)
        st.rerun()
    elif games_info['state'] == 'finished':
        if session_state.name == games_info['restart_name']:
            restart_thread(session_state.room)
        
        
    if session_state.name not in games_info['players_in_game'] and session_state.name not in games_info['add_player']:
        session_state.state = 'in_room'
        time.sleep(2)
        st.rerun()
    
    
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
                if games_info['state'] != 'finished':
                    continue
                else:
                    container.write('**-**')
                # container.write('**×**')
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
                    container.caption(':blue[+{}]'.format(betted_chips))
            container.caption('筹码量: {}'.format(games_info['chips'][players[i]]))
            if players[i] == my_name or games_info['state'] == 'finished':
                container.write('**{}**'.format(hand_cards[players[i]]))
            else:
                container.write('**&nbsp;?&nbsp;?**')
            
    if session_state.name == games_info['player_to_action']:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button('弃牌') and session_state.game_count == games_info['game_count']:
                action(session_state.room,session_state.name,-2)
        if games_info['max_bet'] >= games_info['chips'][my_name] + games_info['bet_chip'][my_name]:
            with col2:
                if st.button('All in {}'.format(games_info['chips'][my_name])):
                    action(session_state.room,session_state.name,games_info['chips'][my_name])
        else:
            with col2:
                call = games_info['max_bet']-games_info['bet_chip'][my_name]
                text = '过牌' if call == 0 else '跟注 {}'.format(call)
                if st.button(text):
                    action(session_state.room,session_state.name,call)        
            with col3:
                    act = st.number_input(label=' ',min_value=min(20+games_info['max_bet']-games_info['bet_chip'][my_name],games_info['chips'][my_name]),max_value=games_info['chips'][my_name],step=20,label_visibility='collapsed')
                    if st.button('加注 {}'.format(act)):
                        action(session_state.room,session_state.name,act)
    session_state.game_count = games_info['game_count']
    if len(games_info['players_in_game']) <= 1:
        if games_info['add_player'] != {}:
            st.write('已加入玩家: {}'.format(' '.join(games_info['add_player'].keys())))
            if st.button('重新开始'):
                restart_game(session_state.room)
            else:
                st.warning('玩家还未加入')
    
    with st.sidebar:
        container = st.container(border=True)
        container.subheader('总成绩:')
        grade = {}
        for each in games_info['ini_chips']:
            grade[each] = games_info['ini_chips'][each] - games_info['buy_in'][each]
            if each in games_info['add_player']:
                grade[each] = games_info['ini_chips'][each] - games_info['buy_in'][each] +  games_info['add_player'][each]

        for each in grade:
            container.write('{}: :{}[{}{}]'.format('**:rainbow[{}]**'.format(each) if grade[each] == max(grade.values()) else each,'red' if grade[each] >= 0 else 'green','+' if grade[each] >= 0 else '',grade[each]))
        container = st.container(border=True)
        write_last_game(container,games_info['last_game'])
        

def write_last_game(container,last_game):
    if last_game['names'] != {}:
        container.subheader('上一局结果:')
        container.write('公共牌: {}'.format(encode_cards(last_game['public_cards'])))
        last_game = last_game['names']
        for each in last_game:
            grade = last_game[each]['grade']
            container.write('{}: {} {} :{}{}]'.format(each,encode_cards(last_game[each]['hand_cards']),last_game[each]['type'],'red[+' if grade >=0 else 'green[',grade))
