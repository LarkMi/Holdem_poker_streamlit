from streamlit_server_state import server_state, server_state_lock,force_rerun_bound_sessions
import pickle
import streamlit as st
from poker_gamethread import GameThread
from collections import defaultdict
from streamlit import session_state
import os

if 'id_pwd' not in os.listdir():
    with open('id_pwd','wb') as f:
        pickle.dump({},f)

def init_server_state():
    with server_state_lock["rooms"]:  # Lock the "count" state for thread-safety
        if "rooms" not in server_state:
            server_state.rooms = defaultdict(dict)
    with server_state_lock[session_state.room]:
        if session_state.room not in server_state:
            pass


def signup(name, pwd):
    names = pickle.load(open('id_pwd','rb'))
    if name in names:
        return '用户已存在'
    else:
        names[name] = pwd
        with open('id_pwd','wb') as f:
            pickle.dump(names,f)
        return '注册成功，请登录'
    
def login(name, pwd):
    names = pickle.load(open('id_pwd','rb'))
    if name not in names:
        return '不存在该用户，请注册'
    if pwd != names[name]:
        return '密码不正确'
    return 'login success'

def get_rooms():
    
    with server_state_lock.rooms:
        re = ['{} nums:{}'.format(key, len(value['players'])) for key, value in server_state.rooms.items()]
    return re
    
def create_room(room_name,player_name):
    with server_state_lock.rooms:
        rooms = server_state.rooms
    if room_name not in rooms:
        rooms[room_name] = {}
        rooms[room_name]['players'] = [player_name]
        rooms[room_name]['owner'] = player_name
        rooms[room_name]['buy_in'] = defaultdict(int)
        rooms[room_name]['game'] = None
        session_state.room = room_name
        session_state.state = 'in_room'
        force_rerun_bound_sessions('rooms')
        return 'create success'
    else:
        return 'create fail'

def join_room(room_name,player_name):
    with server_state_lock.rooms:
        rooms = server_state.rooms
    if len(rooms[room_name]['players']) < 8:
        if player_name in rooms[room_name]['players']:
            rooms[room_name]['game'].add_player[player_name] = 0
            return 'join game'
        rooms[room_name]['players'].append(player_name)
        session_state.room = room_name
        session_state.state = 'in_room'
        force_rerun_bound_sessions('rooms')

        return 'join success'
    else:
        return 'join fail'
    
def get_room_info(room_name,name,chips):
    with server_state_lock.rooms:
        rooms = server_state.rooms
    re = {}
    re['game'] = None
    re['players'] = rooms[room_name]['players']
    re['owner'] = rooms[room_name]['owner']
    re['buy_in'] = rooms[room_name]['buy_in']
    if rooms[room_name]['game'] != None:
        re['game'] = 0
        if name in rooms[room_name]['game'].players_name:
            re['game'] = 1
        re['last_game'] = rooms[room_name]['game'].last_game
        re['game_count'] = rooms[room_name]['game'].game_count
        return re
    rooms[room_name]['buy_in'][name] = chips

    return re

def exit_room(room_name, name):
    with server_state_lock.rooms:
        rooms = server_state.rooms
    if room_name not in rooms or rooms[room_name] == {}:
        session_state.state = 'room'
        session_state.room = 'null'
        force_rerun_bound_sessions('rooms')
        if room_name in rooms:rooms.pop(room_name)
        return 
    if rooms[room_name]['game'] != None:
        if name in rooms[room_name]['game'].add_player:
            rooms[room_name]['game'].add_player.pop(name)
        else:
            rooms[room_name]['game'].remove_player.append(name)
            if rooms[room_name]['game'].player_to_action == name:
                rooms[room_name]['game'].round(name,-2)
            if rooms[room_name]['game'].players_name == [] or sorted(rooms[room_name]['game'].players_name) == sorted(rooms[room_name]['game'].remove_player):
                rooms.pop(room_name)

    else:
        rooms[room_name]['players'].remove(name)
        rooms[room_name]['buy_in'].pop(name)
        if rooms[room_name]['players'] == []:
            rooms.pop(room_name)
    session_state.room = 'null'
    session_state.state = 'room'

    force_rerun_bound_sessions('rooms')
    return '0'

def refreash_buyin():
    with server_state_lock.rooms:
        rooms = server_state.rooms
    if rooms[session_state.room]['game'] == None:
        rooms[session_state.room]['buy_in'][session_state.name] = session_state.chips
        force_rerun_bound_sessions('rooms')
    elif session_state.name not in rooms[session_state.room]['game'].players_name:
        rooms[session_state.room]['buy_in'][session_state.name] = session_state.chips
        force_rerun_bound_sessions('rooms')

def start_game(room_name):
    with server_state_lock[room_name]:
        room = server_state.rooms[room_name]
    room['game'] = GameThread(room['buy_in'])
    session_state.state = 'game'
    force_rerun_bound_sessions(room_name)

    return '0'


def get_game_info(room_name):
    with server_state_lock.rooms:
        rooms = server_state.rooms
    game = rooms[room_name]['game']
    games_info = game.game.games_info
    re = {}
    re['players_in_game']   = game.players_name
    re['players']           = games_info['names'] + games_info['all_in_player']
    re['buy_in']            = rooms[room_name]['buy_in']
    re['chips']             = games_info['chips'].copy()
    re['bet_chip']          = games_info['bet_chip'].copy()
    re['hand_cards']        = games_info['hand_cards']
    re['public_cards']      = game.public_cards
    re['player_to_action']  = game.player_to_action
    re['max_bet']           = game.max_bet
    re['pot']               = game.pot
    re['state']             = game.game.current_state
    re['max_bet_now']       = game.max_bet_now
    re['last_game']         = game.last_game
    re['game_count']        = game.game_count
    re['ini_chips']         = game.ini_chips
    re['add_player']        = game.add_player
    
    return re

def action(room_name,name,act):
    with server_state_lock.rooms:
        rooms = server_state.rooms
    rooms[room_name]['game'].round(name,act)
    force_rerun_bound_sessions(room_name)

def join_game(room_name,name,buy_in):
    with server_state_lock.rooms:
        rooms = server_state.rooms
    rooms[room_name]['game'].add_player[name] = buy_in
    rooms[room_name]['buy_in'][name] += buy_in
    session_state.state = 'game'
    force_rerun_bound_sessions('rooms')
    
def restart_game(room_name):
    with server_state_lock.rooms:
        rooms = server_state.rooms
    rooms[room_name]['game'].restart()
    force_rerun_bound_sessions(session_state.room)
