import random
from collections import defaultdict
import math
import logging
from typing import TypedDict
from poker_judge import Judge


class Games_info(TypedDict):
    names: list[str]
    small_blind   : int
    big_blind     : int
    chips         : dict
    bet_chip      : dict
    public_cards  : list
    all_in_player : list
    card_point    : dict

class Game(object):
    
    def __init__(self, games_info:Games_info, judge=Judge(), logging_level = logging.WARNING, log_filename=None):
        '''
        games_info : dict
            keys:
                names         : list
                small_blind   : int
                big_blind     : int
                chips         : {name: chip}
                bet_chip      : {name: chip}
                public_cards  : list
                all_in_player : list
                card_point    : {name: card_point}
        judge : Judge
        '''
        
        self.judge = judge
        self.players_name         = games_info['names']
        self.players_nums         = len(self.players_name)
        self.effective_nums       = 0
        
        small_blind_name, big_blind_name    = self.players_name[:2]
        
        small_blind, big_blind = games_info['small_blind'], games_info['big_blind']
        
        games_info['bet_chip'][small_blind_name]   += small_blind
        games_info['bet_chip'][big_blind_name]     += big_blind
        
        self.max_bet = big_blind
        
        self.pot = small_blind + big_blind
        
        games_info['chips'][small_blind_name]    -= small_blind
        games_info['chips'][big_blind_name]      -= big_blind
        
        self.cards = [(i,j) for j in range(1,5) for i in range(2,15)] # (size, decor)
        random.shuffle(self.cards)
        random.shuffle(self.cards)
        random.shuffle(self.cards)
        hand_cards = defaultdict(list)
        for _ in range(2):
            for each in self.players_name:
                hand_cards[each].append(self.cards.pop())
        
        games_info['hand_cards'] = hand_cards
        
        self.games_info = games_info
        
        self.current_state = 'pre-flop'
        
        self.last_player = big_blind_name
        
        
        logger = logging.getLogger()
        logger.setLevel(logging_level)
        if log_filename != None:
            logger.addHandler(logging.FileHandler(log_filename, mode='w'))
        logger.info('Game started, now is pre-flop')
        
    def actions(self, player, action):
        '''
        player: player name
        actions: bet chip
        '''
        if player == 'null' and action == -1:
            return 
        
        betted_chip, chip = self.games_info['bet_chip'][player], self.games_info['chips'][player]
        
        need_to_call = min(self.max_bet - betted_chip, chip)
        
        names = self.games_info['names'][:]
        
        if action < need_to_call:
            action = 0
        elif action == need_to_call:
            action = 1
        if action == 0:
            self.games_info['names'].remove(player)
            pot_changed = 0
            logging.info('Player: {} fold'.format(player))
        elif action == 1:
            pot_changed = self.max_bet - betted_chip
            logging.info('Player: {} call {}'.format(player, pot_changed))
        else:
            pot_changed = action
            logging.info('Player: {} raise {}'.format(player, pot_changed))
        
        if chip <= pot_changed:
            pot_changed = chip
            self.games_info['all_in_player'].append(player)
            logging.info('Player: {} all in'.format(player))
        
        self.pot += pot_changed
        
        if betted_chip + pot_changed > self.max_bet:
            self.max_bet = betted_chip + pot_changed
            self.effective_nums = 1
            self.last_player = names[names.index(player) - 1]
        elif action != 0:
            self.effective_nums += 1
        
        if player in self.games_info['all_in_player']:
            self.games_info['names'].remove(player)
            self.effective_nums -= 1
            
        self.games_info['bet_chip'][player]   += pot_changed
        self.games_info['chips'][player]      -= pot_changed

    def finish(self):
        self.games_info['public_cards'] = [(14,1),(14,2),(14,3),(14,4),(13,1)]
        self.games_info['names'] += self.games_info['all_in_player']
        if len(self.games_info['names']) == 0: return
        if self.current_state != 'finish' or len(self.games_info['names']) == [1]:
            self.current_state = 'finished'
            winner = self.games_info['names'][0]
            self.games_info['chips'][winner] += self.pot
            logging.info('Only Player: {} left, winning {}'.format(winner, self.pot))
            logging.debug(str(self.games_info))
            logging.shutdown()
            return 
            
        self.current_state = 'finished'
        points = []
        for each in self.games_info['names']:
            card_type, card = self.judge.get_cards_type(self.games_info['hand_cards'][each], self.games_info['public_cards'])
            card_point = self.judge.get_card_point(card_type, card)
            logging.info('Player: {} card type: {} card point: {}'.format(each, card_type, card_point))
            points.append((card_point,each, self.games_info['bet_chip'][each]))
            self.games_info['card_point'][each] = card_point
        points.sort(key= lambda x:x[2])
        sub_pot = defaultdict(dict)
        for _, name, bet_c in points:
            if bet_c in sub_pot:
                sub_pot[bet_c]['names'].append(name)
                continue
            sub_pot_c = 0
            for each in self.games_info['bet_chip']:
                b = self.games_info['bet_chip'][each]
                b1 = min(b, bet_c)
                sub_pot_c += b1
                self.games_info['bet_chip'][each] -= b1
            sub_pot[bet_c]['names']   = [name]
            sub_pot[bet_c]['sub_pot'] = sub_pot_c
        points.sort(key = lambda x:(x[0],-x[2]))

        assert len(points) != 0, '1#,len(points) == 0, {}, pot:{}'.format(self.games_info,self.pot)+str(winning_player) + str(sub_pot) + str(self.players_name)
        while self.pot > 0:
            max_point = points[-1][0]
            winning_player = []
            while points[-1][0] == max_point:
                _, name, bet_c = points.pop()
                winning_player.append((name, bet_c))
                if not points:break
            winning_player_name = [x[0] for x in winning_player]
            
            for name, bet_c in winning_player:
                winning_num = len(winning_player_name)

                for b in sub_pot:
                    if b <= bet_c:
                        winning_pot = math.ceil(sub_pot[b]['sub_pot']/winning_num)
                        for each in winning_player_name:
                            self.pot -= winning_pot
                            self.games_info['chips'][each] += winning_pot
                            logging.info('Player: {} win {}'.format(each, winning_pot))
                        sub_pot[b]['sub_pot'] = 0
                for n in name:
                    if n in winning_player_name:
                        winning_player_name.remove(n)
            if len(points) == 0:
                self.pot = 0
        
        self.wining_info = defaultdict(int)
        logging.debug(str(self.games_info))
        logging.shutdown()
    
    def pre_flop(self, player, action):
        self.actions(player, action)
        if self.effective_nums == len(self.games_info['names']) and player == self.last_player:
            self.current_state    = 'flop round'
            logging.info('Now is flop round')
            self.cards.pop()
            for _ in range(3):
                self.games_info['public_cards'].append(self.cards.pop())
            if len(self.games_info['names']) <= 1 and len(self.games_info['all_in_player']) > 0:
                if len(self.games_info['names']) == 1:
                    self.last_player    = self.games_info['names'][-1]
                    self.effective_nums = 0
                    self.flop_round(self.last_player, 1)
                else:
                    self.last_player = 'null'
                    self.flop_round('null', -1)
                return 
            self.last_player = self.games_info['names'][-1]
            self.effective_nums   = 0
            
            

    def flop_round(self, player, action):
        self.actions(player, action)
        if self.effective_nums == len(self.games_info['names']) and player == self.last_player:
            self.current_state    = 'turn round'
            logging.info('Now is turn round')
            self.cards.pop()
            self.games_info['public_cards'].append(self.cards.pop())

            if len(self.games_info['names']) <= 1 and len(self.games_info['all_in_player']) > 0:
                if len(self.games_info['names']) == 1:
                    self.last_player    = self.games_info['names'][-1]
                    self.effective_nums = 0
                    self.turn_round(self.last_player, 1)
                else:
                    self.last_player = 'null'
                    self.turn_round('null', -1)
                return 
            self.last_player = self.games_info['names'][-1]
            self.effective_nums   = 0
            
    
    def turn_round(self, player, action):
        self.actions(player, action)
        if self.effective_nums == len(self.games_info['names']) and player == self.last_player:
            self.current_state    = 'river round'
            logging.info('Now is river round')
            self.cards.pop()
            self.games_info['public_cards'].append(self.cards.pop())
            if len(self.games_info['names']) <= 1 and len(self.games_info['all_in_player']) > 0:
                if len(self.games_info['names']) == 1:
                    self.last_player    = self.games_info['names'][-1]
                    self.effective_nums = 0
                    self.river_round(self.last_player, 1)
                else:
                    self.last_player = 'null'
                    self.river_round('null', -1)
                return 
            self.last_player = self.games_info['names'][-1]
            self.effective_nums   = 0
    
    def river_round(self, player, action):
        self.actions(player, action)
        if self.effective_nums == len(self.games_info['names']) and player == self.last_player:
            self.current_state = 'finish'
            logging.info('Game finish')
            self.finish()
            
            
    def round(self, player, action):
        logging.debug(str(self.games_info))
        logging.debug('pot: {}'.format(self.pot))
        logging.debug('Player: {} Action: {}'.format(player, action))
        if self.current_state == 'pre-flop':
            self.pre_flop(player,action)
        elif self.current_state == 'flop round':
            self.flop_round(player,action)
        elif self.current_state == 'turn round':
            self.turn_round(player,action)
        elif self.current_state == 'river round':
            self.river_round(player,action)
        
        if self.current_state != 'finished':
            if len(self.games_info['names']) + len(self.games_info['all_in_player']) == 1:
                self.finish()
        
