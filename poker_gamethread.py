from poker_engine import Game
from poker_judge import Judge

from collections import defaultdict
import time

class GameThread():
    def __init__(self, players_info:dict):
        super().__init__()
        print('#########init game#########')
        self.judge = Judge()
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
        
        self.game = Game(games_info,self.judge)
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
            if self.game.games_info['chips'][each] < 20:
                self.remove_player.append(each)
        
        self.last_game['public_cards'] = self.public_cards.copy()
        if len(self.players_name) > 1:
            self.last_game['names'] = defaultdict(dict)
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
        self.ini_chips = games_info['chips'].copy()
        self.game = Game(games_info,self.judge)
        if len(games_info['names']) <= 2:
            self.player_to_action = games_info['names'][0]
        else:
            self.player_to_action = games_info['names'][2]
        self.mini_bet = 40
        self.max_bet = 20
        self.pot = 30
        self.public_cards = []
        self.max_bet_now = 0

        return
    
    def refresh(self, players, i, pre_state,now_state):
        #time.sleep(0.5)
        games_info = self.game.games_info
        
        #betted_chips = sorted(list(self.game.games_info['bet_chip'].values()))
        #self.mini_bet = max((betted_chips[-1] - betted_chips[-2]),20)
        self.mini_bet = 20
        self.max_bet = self.game.max_bet
        self.pot = self.game.pot
        
        if now_state == 'finished':
            if len(self.game.games_info['all_in_player']) > 0:
                self.public_cards = self.game.games_info['public_cards'].copy()
            #time.sleep(1)
            self.restart()
            return
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
            self.public_cards = self.game.games_info['public_cards'].copy()
            
            if self.player_to_action in self.remove_player:
                self.round(self.player_to_action,-2)
    def round(self,players,action):
        pre_state = self.game.current_state
        i = self.game.games_info['names'].index(players)
        self.game.round(players,action)
        now_state = self.game.current_state

        self.player_to_action = -1
        self.refresh(players, i, pre_state,now_state)
        return
        #t = Thread(target=self.refresh(players, i, pre_state,now_state))
        #t.start()
