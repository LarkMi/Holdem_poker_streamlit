from flask import Flask
from flask import request
from collections import defaultdict
from poker_engine import Game, Judge
from threading import Thread
import time
import os
import pickle

app = Flask(__name__)
#app.debug = True
names = {}
rooms = defaultdict(dict) #{'room_name':{'players','owner','game','buy_in'}}
judge = Judge()

class GameThread():
    def __init__(self, players_info:dict):
        super().__init__()
        print('#########init game#########')
        self.game_count = 1
        self.players_name = list(players_info.keys()).copy()
        games_info = {}
        games_info['names'] = list(players_info.keys()).copy()
        games_info['small_blind'] = 10
        games_info['big_blind'] = 20
        games_info['chips'] = players_info.copy()
        games_info['bet_chip'] = defaultdict(int)
        for each in games_info['chips']:
            games_info['bet_chip'][each] = 0
        games_info['public_cards'] = []
        games_info['all_in_player'] = []
        games_info['card_point'] = defaultdict(int)
        
        self.ini_chips = games_info['chips'].copy()
        
        self.game = Game(games_info,judge)
        if len(games_info['names']) <= 2:
            self.player_to_action = games_info['names'][0]
        else:
            self.player_to_action = games_info['names'][2]
        self.mini_bet = 40
        self.max_bet = 20
        self.pot = 30
        self.public_cards = []
        self.remove_player = []
        self.add_player = {}
        self.max_bet_now = 0
        self.last_game = {
            'public_cards':[],
            'names':defaultdict(dict)
        }
    
    def restart(self):
        #print(self.players_name)
        
        for each in self.game.games_info['chips']:
            if self.game.games_info['chips'][each] <= 0:
                self.remove_player.append(each)
        
        self.last_game['public_cards'] = self.public_cards.copy()
        for each in self.players_name:
            self.last_game['names'][each]['hand_cards'] = self.game.games_info['hand_cards'][each].copy()
            self.last_game['names'][each]['grade'] = self.game.games_info['chips'][each] - self.ini_chips[each]
            if len(self.last_game['public_cards']) == 5:
                self.last_game['names'][each]['type'] = self.game.judge.get_cards_type(self.game.games_info['hand_cards'][each],self.last_game['public_cards'])[0]
            else:
                self.last_game['names'][each]['type'] = ' '
        
        self.game_count += 1
        while self.remove_player != []:
            x = self.remove_player.pop()
            if x in self.players_name:
                self.players_name.remove(x)
        while self.add_player != {}:
            for name, chip in list(self.add_player.items()):
                if name not in self.players_name:
                    self.players_name.append(name)
                    self.game.games_info['chips'][name] += chip
                self.add_player.pop(name)
        if len(self.players_name) <= 1:
            return 
        self.players_name = self.players_name[1:] +[self.players_name[0]]
        games_info = {}
        games_info['names'] = self.players_name.copy()
        games_info['small_blind'] = 10
        games_info['big_blind'] = 20
        games_info['chips'] = self.game.games_info['chips'].copy()
        games_info['bet_chip'] = defaultdict(int)
        for each in games_info['chips']:
            games_info['bet_chip'][each] = 0
        games_info['public_cards'] = []
        games_info['all_in_player'] = []
        games_info['card_point'] = defaultdict(int)
        #print(self.players_name)
        self.ini_chips = games_info['chips'].copy()
        self.game = Game(games_info,judge)
        if len(games_info['names']) <= 2:
            self.player_to_action = games_info['names'][0]
        else:
            self.player_to_action = games_info['names'][2]
        self.mini_bet = 40
        self.max_bet = 20
        self.pot = 30
        self.public_cards = []
        self.max_bet_now = 0
    
    def refresh(self, players, i, pre_state,now_state ):
        #print(players,pre_state,now_state)
        time.sleep(0.5)
        games_info = self.game.games_info
        
        betted_chips = sorted(list(self.game.games_info['bet_chip'].values()))
        #self.mini_bet = max((betted_chips[-1] - betted_chips[-2]),20)
        self.mini_bet = 20
        self.max_bet = self.game.max_bet
        self.pot = self.game.pot
        
        if now_state == 'finished':

            time.sleep(5)
            self.restart()
        else:
            if pre_state != now_state:
                self.player_to_action = games_info['names'][0]
                self.mini_bet = 20
                self.max_bet_now = self.game.max_bet
            else:
                if players in games_info['names']:
                    if games_info['names'][-1] == players:
                        i = 0
                    else:
                        i = i+1
                elif i == len(games_info['names']):
                    i = 0
                self.player_to_action = games_info['names'][i]
            self.public_cards = self.game.games_info['public_cards']
            
            if self.player_to_action in self.remove_player:
                self.round(self.player_to_action,-2)
    def round(self,players,action):
        pre_state = self.game.current_state
        i = self.game.games_info['names'].index(players)
        self.game.round(players,action)
        now_state = self.game.current_state
        self.player_to_action = -1
        t = Thread(target=self.refresh(players, i, pre_state,now_state))
        t.start()

@app.route('/signup', methods=['POST'])
def signup():
    post = request.get_json()
    name, pwd = post['name'], post['pwd']
    if name in names:
        return '用户已存在'
    else:
        names[name] = pwd
        with open('id_psw','wb') as f:
            pickle.dump(names,f)
        return '注册成功，请登录'



@app.route('/room', methods=['GET'])
def get_room():
    #print(['{}nums:{}'.format(key.ljust(20), len(value['players'])) for key, value in rooms.items()])
    return ['{} nums:{}'.format(key, len(value['players'])) for key, value in rooms.items()]

@app.route('/get_room_info', methods=['POST'])
def get_room_info():
    post = request.get_json()
    room_name = post['room_name']
    name, chips = post['name'], post['chips']
    re = {}
    re['game'] = None
    re['players'] = rooms[room_name]['players']
    re['owner'] = rooms[room_name]['owner']
    if rooms[room_name]['game'] != None:
        re['game'] = 0
        if name in rooms[room_name]['game'].players_name:
            re['game'] = 1
        return re
    rooms[room_name]['buy_in'][name] = chips

    return re

@app.route('/start_game', methods=['POST'])
def start_game():
    
    room_name = request.get_json()['room_name']
    rooms[room_name]['game'] = GameThread(rooms[room_name]['buy_in'])
    print(rooms)
    return '0'


@app.route('/action', methods=['POST'])
def action():
    post = request.get_json()
    room_name = post['room_name']
    player = post['player']
    action = post['action']
    rooms[room_name]['game'].round(player,action)
    return '0'

@app.route('/get_game_info', methods=['POST'])
def get_game_info():
    #print(rooms)
    room_name = request.get_json()['room_name']
    game = rooms[room_name]['game']
    games_info = game.game.games_info
    return_dic = {}
    return_dic['players_in_game'] = game.players_name
    return_dic['players'] = games_info['names'] + games_info['all_in_player']
    return_dic['buy_in'] = rooms[room_name]['buy_in']
    return_dic['chips'] = games_info['chips']
    return_dic['bet_chip'] = games_info['bet_chip']
    return_dic['hand_cards'] = games_info['hand_cards']
    return_dic['public_cards'] = game.public_cards
    return_dic['player_to_action'] = game.player_to_action
    return_dic['mini_bet'] = game.mini_bet
    return_dic['max_bet'] = game.max_bet
    return_dic['pot'] = game.pot
    return_dic['state'] = game.game.current_state
    return_dic['max_bet_now'] = game.max_bet_now
    return_dic['last_game'] = game.last_game
    return_dic['game_count'] = game.game_count
    return_dic['ini_chips'] = game.ini_chips
    return_dic['add_player'] = list(game.add_player.keys())
    
    return return_dic

@app.route('/exit_room', methods=['POST'])
def exit_room():
    post = request.get_json()
    room_name, name = post['room_name'], post['name']
    if rooms[room_name]['game'] != None:
        rooms[room_name]['game'].remove_player.append(name)
        if rooms[room_name]['game'].player_to_action == name:
            rooms[room_name]['game'].round(name,-2)
        
    else:
        rooms[room_name]['players'].remove(name)
        rooms[room_name]['buy_in'].pop(name)
    
    if rooms[room_name]['players'] == [] or rooms[room_name]['game'].players_name == []:
        rooms.pop(room_name)
    
    return '0'


@app.route('/login', methods=['POST'])
def login():
    post = request.get_json()
    name, pwd = post['name'], post['pwd']
    if name not in names:
        return '不存在该用户，请注册'
    if pwd != names[name]:
        return '密码不正确'
    return 'login success'

@app.route('/join_room', methods=['POST'])
def join_room():
    post = request.get_json()
    room_name = post['room_name']
    player_name = post['player_name']
    if len(rooms[room_name]['players']) < 8:
        if player_name in rooms[room_name]['players']:
            rooms[room_name]['game'].add_player[player_name] = 0
            return 'join game'
        rooms[room_name]['players'].append(player_name)
        return 'join success'
    else:
        return 'join fail'

@app.route('/join_game', methods=['POST'])
def join_game():
    post = request.get_json()
    room_name = post['room_name']
    player_name = post['name']
    buy_in = post['buy_in']
    rooms[room_name]['game'].add_player[player_name] = buy_in

    rooms[room_name]['buy_in'][player_name] += buy_in
    return '1'

@app.route('/create_room', methods=['POST'])
def create_room():
    post = request.get_json()
    room_name = post['room_name'].replace(' ','_')
    player_name = post['player_name']
    if room_name not in rooms:
        rooms[room_name]['players'] = [player_name]
        rooms[room_name]['owner'] = player_name
        rooms[room_name]['buy_in'] = defaultdict(int)
        rooms[room_name]['game'] = None
        return 'create success'
    else:
        return 'create fail'

def sever_run():
    if 'id_psw' in os.listdir():
        names = pickle.load(open('id_psw','rb'))
    else:
        names = {}
        with open('id_psw','wb') as f:
            pickle.dump(names,f)
    app.run(host = '0.0.0.0',port = 5678)

if __name__ == "__main__":
    sever_run()