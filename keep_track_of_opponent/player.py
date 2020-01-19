'''
Simple example pokerbot, written in Python.
'''
import random
import numpy as np
from collections import namedtuple


from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot


class Player(Bot):
    '''
    A pokerbot.
    '''

    def __init__(self):
        #statistics, counts, initialize dictionaries
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        self.netgain = 0
        #for i in range(13):
        #    self.incoming[i] = []
        #    self.outgoing[i] = []
        self.records = [[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0]]
        self.complete = [[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0]]
        self.VALUES = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
        self.wins_dict = {v : 1 for v in self.VALUES}
        self.showdowns_dict = {v : 2 for v in self.VALUES}
        self.allcard_winrate = []
        self.big_raise_times = 0
        self.games_played = 1

        #preflop stats for players. To get fraction, divide 1st element/2nd element
        self.my_preflop_bet = [0,0]
        self.opp_preflop_bet = [0,0]
        self.my_preflop_call = [0,0]
        self.opp_preflop_call = [0,0]
        self.my_preflop_raise = [0,0]
        self.opp_preflop_raise = [0,0]

        #flop stats for players, to get fractions, divide by my_flop_seen and opp_flop_seen
        self.my_flop_bet = [0,0]
        self.opp_flop_bet = [0,0]
        self.my_flop_call = [0,0]
        self.opp_flop_call = [0,0]
        self.my_flop_raise = [0,0]
        self.opp_flop_raise = [0,0]

        #turn stats for players
        self.my_turn_bet = [0,0]
        self.opp_turn_bet = [0,0]
        self.my_turn_call = [0,0]
        self.opp_turn_call = [0,0]
        self.my_turn_raise = [0,0]
        self.opp_turn_raise = [0,0]

        #river stats for players
        self.my_river_bet = [0,0]
        self.opp_river_bet = [0,0]
        self.my_river_call = [0,0]
        self.opp_river_call = [0,0]
        self.my_river_raise = [0,0]
        self.opp_river_raise = [0,0]

    def signchange(self,a,change):
        if a>-5 and a+change<-4:
            return True
        if a<5 and a+change>4:
            return True
        if abs(a+change)<4 and abs(a)>4:
            return True
        return False
    def non_straight_strength(self, cards):
        #0 = no pair, 1 = pair, 2 = 2 pair, 3 = 3 of a kind, 4 = flush
        #5 = full house, 6 = 4 of a kind
        rankcounts = [0,0,0,0,0,0,0,0,0,0,0,0,0]
        suitcounts = [0,0,0,0]
        for c in cards:
            rank = "23456789TJQKA".index(c[0])
            suit = "chsd".index(c[1])
            rankcounts[rank]+=1
            suitcounts[suit]+=1
        if max(suitcounts)>=5:
            return 4
        if max(rankcounts)==1:
            return 0
        elif max(rankcounts) == 2 and rankcounts.count(2)==1:
            return 1
        elif max(rankcounts) == 2 and rankcounts.count(2)>1:
            return 2
        elif max(rankcounts) == 3:
            numpairs=0
            for i in range(13):
                if rankcounts[i]>1:
                    numpairs+=1
            if numpairs==1:
                return 3
            else:
                return 5
        elif max(rankcounts) == 4:
            return 6
        return "something went wrong"
    def strongest_cards(self, cards):
        rankcounts = [0,0,0,0,0,0,0,0,0,0,0,0,0]
        suitcounts = [0,0,0,0]
        relevant = [[],[]]
        for c in cards:
            rank = "23456789TJQKA".index(c[0])
            suit = "chsd".index(c[1])
            rankcounts[rank]+=1
            suitcounts[suit]+=1
        most = 0
        secondmost = 0
        strength = self.non_straight_strength(cards)
        if strength == 0:
            most = 1
            secondmost = 0
        elif strength == 1:
            most = 2
            secondmost = 1
        elif strength == 2:
            most = 2
            secondmost = 2
        elif strength == 3:
            most = 3
            secondmost = 1
        elif strength == 4:
            s = "chsd"[suitcounts.index(max(suitcounts))]
            for c in cards:
                if c[1]==s:
                    relevant[0].append(c[0])
            return relevant
        elif strength == 5:
            most = 3
            secondmost = 2
        elif strength == 6:
            most = 4
            secondmost = 1
        for i in range(13):
            if rankcounts[i]==most:
                relevant[0].append("23456789TJQKA"[i])
            elif rankcounts[i]>=secondmost:
                relevant[1].append("23456789TJQKA"[i])
        return relevant
    def matchup(self, winning,losing): #figure out which cards won and lost the matchup, given 7-card hands.
        #"winning" and "losing" are sets of strongest cards
        difference = 1
        for card in winning[0]:
            if card not in losing[0]:
                difference = 0
        for card in losing[0]:
            if card not in winning[0]:
                difference = 0
        wincards = []
        losecards = []
        for card in winning[difference]:
            if card not in losing[difference]:
                wincards.append(card)
        for card in losing[difference]:
            if card not in winning[difference]:
                losecards.append(card)
        return [wincards,losecards]
    def compute_strength(self):
        #1 = strongest, 0 = weakest
        strengths = [0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5]
        for i in range(13):
            s = 0
            for bla in range(13):
                s+=self.complete[i][bla]
            strengths[i] = 0.5 + s/24.0

        return strengths
    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.
        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        my_cards = round_state.hands[active]  # your cards
        big_blind = bool(active)  # True if you are the big blind

        self.games_played += 1

        if round_num % 100 == 0:
            self.big_raise_times = 0
            self.games_played = 1

        pass

    #active is the person that is dealer
    def handle_round_over(self, game_state, terminal_state, active):
        self.netgain += terminal_state.deltas[active]
        previous_state = terminal_state.previous_state
        # print (terminal_state)
        if game_state.round_num == 999:
            print(self.compute_strength())
        if previous_state.street==5 and len(previous_state.hands[1-active])==2:
            #if the hand went to showdown
            tie=False
            if terminal_state.deltas[active]>0: #won
                goodcards = previous_state.hands[active]+previous_state.deck[:5]
                badcards = previous_state.hands[1-active]+previous_state.deck[:5]
            elif terminal_state.deltas[active]<0: #lost
                badcards = previous_state.hands[active]+previous_state.deck[:5]
                goodcards = previous_state.hands[1-active]+previous_state.deck[:5]         
            else: #tie
                tie=True
                goodcards = previous_state.hands[active]+previous_state.deck[:5]
                badcards = previous_state.hands[1-active]+previous_state.deck[:5]
            if self.non_straight_strength(goodcards) == self.non_straight_strength(badcards): #the hands are the same strength
                goodstrongest = self.strongest_cards(goodcards)
                badstrongest = self.strongest_cards(badcards)
                #print(goodcards)
                #print(badcards)
                m = self.matchup(goodstrongest,badstrongest)
                #print(m)
                #AAABC DE DF B>D>C
                if tie:
                    uniqueboardcards = []
                    for c in previous_state.deck[:5]:
                        count = 0
                        for d in previous_state.deck[:5]:
                            if d[0]==c[0]:
                                count+=1
                        if count==1:
                            uniqueboardcards.append(c[0])
                    differingholecards = []
                    for c in previous_state.hands[active]:
                        rank = c[0]
                        differing = True
                        for d in previous_state.hands[1-active]:
                            if d[0]==c[0]:
                                differing = False
                        if differing:
                            differingholecards.append(c[0])
                    for c in previous_state.hands[1-active]:
                        rank = c[0]
                        differing = True
                        for d in previous_state.hands[active]:
                            if d[0]==c[0]:
                                differing = False
                        if differing:
                            differingholecards.append(c[0])
                    if len(differingholecards)==4:
                        for c in uniqueboardcards:
                            for d in differingholecards:
                                c_num = "23456789TJQKA".index(c)
                                d_num = "23456789TJQKA".index(d)
                                if self.signchange(self.records[c_num][d_num],5):
                                    if self.records[c_num][d_num]+5 > 0:
                                        #c is better than d
                                        self.complete[c_num][d_num] = 1
                                        self.complete[d_num][c_num] = -1
                                        for bad in range(13):
                                            if self.complete[d_num][bad] == 1:
                                                self.complete[c_num][bad] = 1
                                                self.complete[bad][c_num] = -1
                                self.records[c_num][d_num] += 5
                                self.records[d_num][c_num] -= 5
                    #record a certain win for each single board card against each differing hole card.
                if len(m[0])==1:
                    for c in m[0]:
                        for d in m[1]:
                            c_num = "23456789TJQKA".index(c)
                            d_num = "23456789TJQKA".index(d)
                            if self.non_straight_strength(goodcards) >= 5:
                                change = 5000
                            else:
                                change = 5
                            if self.signchange(self.records[c_num][d_num],change):
                                self.complete[c_num][d_num] = 1
                                self.complete[d_num][c_num] = -1
                                for bad in range(13):
                                    if self.complete[d_num][bad] == 1:
                                        self.complete[c_num][bad] = 1
                                        self.complete[bad][c_num] = -1
                            self.records[c_num][d_num] += change
                            self.records[d_num][c_num] -= change
                    #record a win for the single winning card against the losing card(s).
                elif len(m[0])==2:
                    for c in m[0]:
                        for d in m[1]:
                            c_num = "23456789TJQKA".index(c)
                            d_num = "23456789TJQKA".index(d)
                            if self.signchange(self.records[c_num][d_num],1):
                                self.complete[c_num][d_num] = 1
                                self.complete[d_num][c_num] = -1
                                for bad in range(13):
                                    if self.complete[d_num][bad] == 1:
                                        self.complete[c_num][bad] = 1
                                        self.complete[bad][c_num] = -1
                            self.records[c_num][d_num] += 1
                            self.records[d_num][c_num] -= 1

        #Player statistics are updated at the end of each round, iterating through all previous states
        #0th index player is small blind

        #First, check for a player folding
        if terminal_state.deltas[active] > 0 and previous_state.pips[0] != previous_state.pips[1]:
            self.update_stats(self, previous_state.street, 'opp', 'fold')
        if terminal_state.deltas[active] < 0 and previous_state.pips[0] != previous_state.pips[1]:
            self.update_stats(self, previous_state.street, 'me', 'fold')


        raise_num = 0
        #Then, we iterate backwards to the beginning
        while previous_state.previous_state:
            all_in = False
            if previous_state.stacks == [0,0]: # If both players are all-in, don't record that they check
                previous_state = previous_state.previous_state
                continue
            if (previous_state.street != previous_state.previous_state.street) and previous_state.previous_state.pips != [0,0]: 
                # Players don't take action when the round state increases in street AND the previous street ended in a call
                previous_state = previous_state.previous_state
                continue
            if previous_state.pips == [0,0]:
                raise_num = 0
                action = 'check'
            elif previous_state.pips[0] == previous_state.pips[1]:
                raise_num = 0
                action = 'call'
                if previous_state.stacks == [0,0]:
                    all_in = True
            elif previous_state.previous_state.pips[0] == 0 and previous_state.previous_state.pips[1] == 0:
                raise_num = 0
                action = 'bet'
            else:
                if raise_num < 2:
                    action = 'raise'
                    raise_num += 1
                else:
                    previous_state = previous_state.previous_state
                    continue
            if (active + previous_state.previous_state.button) % 2 == 0:
                player = 'me'
            else:
                player = 'opp'
            #print (game_state.round_num, previous_state.street, player, action)
            self.update_stats(previous_state.street, player, action, all_in)
            previous_state = previous_state.previous_state

        if game_state.round_num % 100 == 0:
            print ('Opp preflop raise: ', self.opp_preflop_raise)
            print ('Opp flop raise: ', self.opp_flop_raise)
            print ('Opp turn raise: ', self.opp_turn_raise)
            print ('Opp river raise: ', self.opp_river_raise)
        previous_state = terminal_state.previous_state

        return

    #given the street and action, update stats
    #valid actions for this function are "check", bet", "fold", "call", "raise"
    #valid players for this function are "me" and "opp"
    #set allin to be True if calling resulted in player being all in (this is because we will not add 1 to denominator of raise fraction)
    def update_stats(self, street, player, action, allin = False):
        if street == 0:
            if player == 'me':
                if action == 'bet': 
                    self.my_preflop_bet[0] += 1
                    self.my_preflop_bet[1] += 1
                if action == 'check':
                    self.my_preflop_bet[1] += 1
                if action == 'fold':
                    self.my_preflop_call[1] += 1
                    self.my_preflop_raise[1] += 1
                if action == 'call':
                    self.my_preflop_call[0] += 1
                    self.my_preflop_call[1] += 1
                    if not allin: self.my_preflop_raise[1] += 1
                if action == 'raise':
                    self.my_preflop_raise[0] += 1
                    self.my_preflop_call[1] += 1
                    self.my_preflop_raise[1] += 1
            if player == 'opp':
                if action == 'bet': 
                    self.opp_preflop_bet[0] += 1
                    self.opp_preflop_bet[1] += 1
                if action == 'check':
                    self.opp_preflop_bet[1] += 1
                if action == 'fold':
                    self.opp_preflop_call[1] += 1
                    self.opp_preflop_raise[1] += 1
                if action == 'call':
                    self.opp_preflop_call[0] += 1
                    self.opp_preflop_call[1] += 1
                    if not allin: self.opp_preflop_raise[1] += 1
                if action == 'raise':
                    self.opp_preflop_raise[0] += 1
                    self.opp_preflop_call[1] += 1
                    self.opp_preflop_raise[1] += 1
        elif street == 3:
            if player == 'me':
                if action == 'bet': 
                    self.my_flop_bet[0] += 1
                    self.my_flop_bet[1] += 1
                if action == 'check':
                    self.my_flop_bet[1] += 1
                if action == 'fold':
                    self.my_flop_call[1] += 1
                    self.my_flop_raise[1] += 1
                if action == 'call':
                    self.my_flop_call[0] += 1
                    self.my_flop_call[1] += 1
                    if not allin: self.my_flop_raise[1] += 1
                if action == 'raise':
                    self.my_flop_raise[0] += 1
                    self.my_flop_call[1] += 1
                    self.my_flop_raise[1] += 1
            if player == 'opp':
                if action == 'bet': 
                    self.opp_flop_bet[0] += 1
                    self.opp_flop_bet[1] += 1
                if action == 'check':
                    self.opp_flop_bet[1] += 1
                if action == 'fold':
                    self.opp_flop_call[1] += 1
                    self.opp_flop_raise[1] += 1
                if action == 'call':
                    self.opp_flop_call[0] += 1
                    self.opp_flop_call[1] += 1
                    if not allin: self.opp_flop_raise[1] += 1
                if action == 'raise':
                    self.opp_flop_raise[0] += 1
                    self.opp_flop_call[1] += 1
                    self.opp_flop_raise[1] += 1
        elif street == 4:
            if player == 'me':
                if action == 'bet': 
                    self.my_turn_bet[0] += 1
                    self.my_turn_bet[1] += 1
                if action == 'check':
                    self.my_turn_bet[1] += 1
                if action == 'fold':
                    self.my_turn_call[1] += 1
                    self.my_turn_raise[1] += 1
                if action == 'call':
                    self.my_turn_call[0] += 1
                    self.my_turn_call[1] += 1
                    if not allin: self.my_turn_raise[1] += 1
                if action == 'raise':
                    self.my_turn_raise[0] += 1
                    self.my_turn_call[1] += 1
                    self.my_turn_raise[1] += 1
            if player == 'opp':
                if action == 'bet': 
                    self.opp_turn_bet[0] += 1
                    self.opp_turn_bet[1] += 1
                if action == 'check':
                    self.opp_turn_bet[1] += 1
                if action == 'fold':
                    self.opp_turn_call[1] += 1
                    self.opp_turn_raise[1] += 1
                if action == 'call':
                    self.opp_turn_call[0] += 1
                    self.opp_turn_call[1] += 1
                    if not allin: self.opp_turn_raise[1] += 1
                if action == 'raise':
                    self.opp_turn_raise[0] += 1
                    self.opp_turn_call[1] += 1
                    self.opp_turn_raise[1] += 1
        elif street == 5:
            if player == 'me':
                if action == 'bet': 
                    self.my_river_bet[0] += 1
                    self.my_river_bet[1] += 1
                if action == 'check':
                    self.my_river_bet[1] += 1
                if action == 'fold':
                    self.my_river_call[1] += 1
                    self.my_river_raise[1] += 1
                if action == 'call':
                    self.my_river_call[0] += 1
                    self.my_river_call[1] += 1
                    if not allin: self.my_river_raise[1] += 1
                if action == 'raise':
                    self.my_river_raise[0] += 1
                    self.my_river_call[1] += 1
                    self.my_river_raise[1] += 1
            if player == 'opp':
                if action == 'bet': 
                    self.opp_river_bet[0] += 1
                    self.opp_river_bet[1] += 1
                if action == 'check':
                    self.opp_river_bet[1] += 1
                if action == 'fold':
                    self.opp_river_call[1] += 1
                    self.opp_river_raise[1] += 1
                if action == 'call':
                    self.opp_river_call[0] += 1
                    self.opp_river_call[1] += 1
                    if not allin: self.opp_river_raise[1] += 1
                if action == 'raise':
                    self.opp_river_raise[0] += 1
                    self.opp_river_call[1] += 1
                    self.opp_river_raise[1] += 1

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''

        '''
        roundsleft = 1000-game_state.round_num
        
        necessarylead = 1.5*roundsleft
        if roundsleft % 2 == 1:
            if bool(active):
                necessarylead += 0.5
            else:
                necessarylead -= 0.5
        if(self.netgain > necessarylead):
            if CheckAction in round_state.legal_actions():
                return CheckAction()
            return FoldAction()
        '''
        
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        if legal_actions == {CheckAction}:
            return CheckAction()

        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, river, or turn respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        pot_after_continue = my_contribution + opp_contribution + continue_cost
        pot_odds = continue_cost / pot_after_continue

        #namedtuple('_RoundState', ['button', 'street', 'pips', 'stacks', 'hands', 'deck', 'previous_state'])
        dict_values = np.array(round_state.previous_state)
        if dict_values.any() == None:
            dict_values = [0,0,[0,0],[0,0],0,0,0]
        dict_keys = ['button', 'street', 'pips', 'stacks', 'hands', 'deck', 'previous_state']
        previous_state = {}
        for i in range(len(dict_values)):
            previous_state[dict_keys[i]] = dict_values[i]

        last_round_opp_pip = previous_state['pips'][1-active]
        last_round_pot_after_continue = (STARTING_STACK - previous_state['stacks'][active]) + \
                        (STARTING_STACK - previous_state['stacks'][1-active]) + \
                        previous_state['pips'][active] - previous_state['pips'][1-active]
        opp_reasonable_raise_amount = previous_state['pips'][active] + int(0.75 * last_round_pot_after_continue)
        if opp_pip - last_round_opp_pip >= opp_reasonable_raise_amount * 2:
            self.big_raise_times += 1

        allcard_winrate = self.compute_strength()
        #allcard_winrate = [self.wins_dict[x] / self.showdowns_dict[x] for x in self.VALUES] #[0.9,0.1,0.2,0.3]
        ind = list(np.argsort(allcard_winrate)) #[1,2,3,0]
        
        new_cards = []
        for x in my_cards+board_cards:
            original_index = self.VALUES.index(x[0])
            current_index = ind.index(original_index)
            y = self.VALUES[current_index] + x[1]
            #print(y)
            new_cards.append(y)

        my_cards = new_cards[:2]
        board_cards = new_cards[2:]

        first_card_strength = (self.VALUES.index(my_cards[0][0]) + 1) / len(self.VALUES)
        second_card_strength = (self.VALUES.index(my_cards[1][0]) + 1) / len(self.VALUES)
        card_strength = [first_card_strength, second_card_strength]
        agree_counts = [0, 0]
        for card in board_cards:
            # increase agree_counts each time values agree
            for i in range(2):
                if my_cards[i][0] == card[0]:
                    agree_counts[i] += 1

        FLUSH = False
        ABOUT_FLUSH = False
        OPP_FLUSH = False
        suit = [x[1] for x in board_cards]
        board_same_suits = max(suit.count('h'), suit.count('d'), suit.count('s'), suit.count('c'))
        suit.append(my_cards[0][1])
        suit.append(my_cards[1][1])
        hand_same_suits = max(suit.count('h'), suit.count('d'), suit.count('s'), suit.count('c'))
        if hand_same_suits >= 5 and board_same_suits <= 4:
            FLUSH == True
        if hand_same_suits >= 4 and street <=3:
            ABOUT_FLUSH == True
        if hand_same_suits == board_same_suits and board_same_suits >=3:
            OPP_FLUSH == True


        bluff_factor = 0
        if self.big_raise_times / self.games_played >= 0.3:
            bluff_factor = self.big_raise_times / self.games_played / 2


        if RaiseAction in legal_actions:
            min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
            min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
            max_cost = max_raise - my_pip  # the cost of a maximum bet/raise

            raise_amount = my_pip + continue_cost + int(0.75 * pot_after_continue)
            raise_amount = min(raise_amount, max_raise)
            raise_amount = max(raise_amount, min_raise)

            # FLUSH
            if FLUSH == True:
                return RaiseAction(raise_amount)
            # OPPO FLUSH
            if pot_odds >= 0.7 and bluff_factor < 0.05 and OPP_FLUSH == True:
                return FoldAction()
            # ABOUT FLUSH
            if ABOUT_FLUSH == True:
                if random.random() < 0.5: 
                    return RaiseAction(raise_amount)
            # THREE OF A KIND OR BETTER
            if agree_counts[0] >= 2 or agree_counts[1] >= 2:
                return RaiseAction(raise_amount)

            # TWO-PAIR
            if sum(agree_counts) >= 2:
                if first_card_strength > 0.5 or second_card_strength > 0.5:
                    return RaiseAction(raise_amount)
            if pot_odds >= 0.7 and bluff_factor < 0.05:
                return FoldAction()
            else:                
                # ONE PAIR IN FIRST CARD
                if agree_counts[0] == 1:
                    if random.random() < first_card_strength:
                        return RaiseAction(raise_amount)
                # ONE PAIR IN SECOND CARD
                if agree_counts[1] == 1:
                    if random.random() < second_card_strength:
                        return RaiseAction(raise_amount)
                # POCKET PAIR
                if my_cards[0][0] == my_cards[1][0]:
                    if random.random() < first_card_strength:
                        return RaiseAction(raise_amount)

                # PRE-FLOP HIGH CARD
                if street == 0 and (first_card_strength>0.8 or second_card_strength>0.8):
                    return RaiseAction(raise_amount)

        if CheckAction in legal_actions:  # check-call
            return CheckAction()

        if CallAction in legal_actions:
            # FLUSH
            if FLUSH == True:
                return CallAction()
            # OPPO FLUSH
            if pot_odds >= 0.7 and bluff_factor < 0.05 and OPP_FLUSH == True:
                return FoldAction()
            # ABOUT FLUSH
            if ABOUT_FLUSH == True and pot_odds < 0.4:
                return CallAction()
            # THREE OF A KIND OR BETTER
            if agree_counts[0] >= 2 or agree_counts[1] >= 2:
                return CallAction()
            # TWO-PAIR
            if sum(agree_counts) >= 2:
                return CallAction()
            if pot_odds >= 0.7 and bluff_factor < 0.05:
                return FoldAction()
            else:   
                # ONE PAIR IN FIRST CARD
                if agree_counts[0] == 1:
                    if bluff_factor < (first_card_strength * (1+bluff_factor)):
                        return CallAction()
                # ONE PAIR IN SECOND CARD
                if agree_counts[1] == 1:
                    if random.random() < (second_card_strength * (1+bluff_factor)):
                        return CallAction()
                # POCKET PAIR
                if my_cards[0][0] == my_cards[1][0]:
                    if random.random() < (first_card_strength * (1+bluff_factor)):
                        return CallAction()

                #HIGH CARD
                if street == 0 and (first_card_strength >0.9 or second_card_strength>0.9) and bluff_factor > 0.05:
                    return CallAction()
                if street == 0 and (first_card_strength >0.8 or second_card_strength>0.8) and bluff_factor > 0.15:
                    return CallAction()

                # SMALL BET
                if pot_odds < 0.2:
                    return CallAction()

        return FoldAction()


if __name__ == '__main__':
    run_bot(Player(), parse_args())
