import pickle
from collections import Counter

class Judge(object):
    
    def __init__(self) -> None:
        '''
        dic_point:
            keys: Straight Flush Flush OnePair Straight High-Card TwoPair Three-of-a-Kind Full House Four-of-a-Kind
            High-Card: dict
                keys: 0705040302 : point(0)
        '''
        with open('dic_point.dic', 'rb') as f:
            self.dic_point = pickle.load(f)


    def detect_flush(self, cards):
        c = Counter([x[1] for x in cards])
        for each in c:
            if c[each] >= 5:
                return True, each
        return False, -1

    def detect_straight(self, cards):
        c = [x[0] for x in cards]
        c = list(set(c))
        c.sort(key=lambda x:-x)
        s = 0
        if len(c) < 5:
            return False, -1
        for i in range(len(c)-1):
            if c[i] == c[i+1] + 1:
                s += 1
                if s == 4:
                    return True, c[i] + 3
            else:
                s = 0
        
        if 14 in c:
            c.remove(14)
            c.append(1)
            s = 0
            for i in range(len(c)-1):
                if c[i] == c[i+1] + 1:
                    s += 1
                    if s == 4:
                        return True, c[i] + 3
                else:
                    s = 0
        
        return False, -1


    def get_cards_type(self, cards, public_cards):
        """_summary_

        Args:
            cards (list): hand card [(3,1),(2,3)]
            public_cards (lsit): public_cards [(3,2),(2,2),(5,1),(12,0),(11,1)]

        Returns:
            card type, eg: 'Straight Flush'
            card, eg 706050403, represent 76543
        """
        cards = cards + public_cards
        cards.sort(key=lambda x : (-x[0],x[1]))
        # detect straight flush
        is_flush, decor = self.detect_flush(cards)
        if is_flush:
            c = []
            for each in cards:
                if each[1] == decor:
                    c.append(each)
            is_straight, max_card = self.detect_straight(c)
            if is_straight:
                return 'Straight Flush', max_card * 10e7 + (max_card - 1) * 10e5 + (max_card - 2) * 10e3 + (max_card - 3) * 10e1 + max_card - 4
        
        # detect Four-of-a-Kind
        size = Counter([x[0] for x in cards])
        four = 0
        for each in size:
            if size[each] == 4:
                four = each
                for x, y in cards:
                    if x != four:
                        max_card = x
                        break
                return 'Four-of-a-Kind', four * 10e7 + four * 10e5 + four * 10e3 + four * 10e1 + x
        
        # detect Full House
        three = 0
        for x, y in cards:
            if three == 0:
                if size[x] == 3:
                    three = x
            else:
                for x, y in cards:
                    if size[x] == 2 and x != three:
                        return 'Full House', three * 10e7 + three * 10e5 + three * 10e3 + x * 10e1 + x
        
        # detect Flush
        if is_flush:
            f = []
            for x, y in cards:
                if y == decor:
                    f.append(x)
                    if len(f) == 5:
                        return 'Flush', sum([f[i] * 10**(8-i*2) for i in range(5)])
        
        # detect Straight 
        is_straight, max_card = self.detect_straight(cards)
        if is_straight:
            return 'Straight', max_card * 10e7 + (max_card - 1) * 10e5 + (max_card - 2) * 10e3 + (max_card - 3) * 10e1 + max_card - 4

        # detect Three-of-a-Kind
        for x, y in cards:
            if size[x] == 3:
                three = x
                s = sorted(list(set([x[0] for x in cards])))[::-1]
                s.remove(three)
                max_card, second_card = s[:2]
                return 'Three-of-a-Kind', three * 10e7 + three * 10e5 + three * 10e3 + max_card * 10e1 + second_card
        
        # detect TwoPair
        onepair = 0
        twopair = 0
        for x, y in cards:
            if onepair == 0:
                if size[x] == 2:
                    onepair = x
            else:
                if size[x] == 2 and x != onepair:
                    twopair = x
                    s = sorted(list(set([x[0] for x in cards])))[::-1]
                    s.remove(onepair)
                    s.remove(twopair)
                    max_card = s[0]
                    return 'TwoPair', onepair * 10e7 + onepair * 10e5 + twopair * 10e3 + twopair * 10e1 + max_card
        
        # detect OnePair
        onepair = 0
        for x, y in cards:
            if size[x] == 2:
                onepair = x
                s = sorted(list(set([x[0] for x in cards])))[::-1]
                s.remove(onepair)
                max_card, second_card, third_card = s[:3]
                return 'OnePair', onepair * 15 * 15 * 15 + max_card * 15 *15 + second_card * 15 + third_card
        
        # detect High-Card
        a,b,c,d,e = [x[0] for x in cards][:5]
        return 'High-Card', a * 10e7 + b * 10e5 + c * 10e3 + d * 10e1 + e
    
    def get_card_point(self, card_type, card):
        return self.dic_point[card_type][card]
    
    def get_card_point_directly(self, cards, public_cards):
        card_type, card = self.get_cards_type(cards, public_cards)
        return self.get_card_point(card_type, card)
