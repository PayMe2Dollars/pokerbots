'''
Simple example pokerbot, written in Python.
'''
import random
import numpy as np
from collections import namedtuple
from operator import itemgetter


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
        #Include ranges
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        self.VALUES = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
        self.wins_dict = {v : 1 for v in self.VALUES}
        self.showdowns_dict = {v : 2 for v in self.VALUES}
        self.allcard_winrate = []
        self.big_raise_times = 0
        self.games_played = 1

        #top 60% of hands
        self.suited_top_60 = ['AK','AQ','AJ','AT','A9','A8','A7','A6','A5','A4','A3','A2',
                             'KQ','KJ','KT','K9','K8','K7','K6','K5','K4','K3','K2',
                             'QJ','QT','Q9','Q8','Q7','Q6','Q5','Q4','Q3','Q2',
                             'JT','J9','J8','J7','J6','J5','J4','J3','J2',
                             'T9','T8','T7','T6','T5','T4',
                             '98','97','96',
                             '87']
        self.unsuited_top_60 = ['AK','AQ','AJ','AT','A9','A8','A7','A6','A5','A4','A3','A2',
                             'KQ','KJ','KT','K9','K8','K7','K6','K5','K4','K3','K2',
                             'QJ','QT','Q9','Q8','Q7','Q6','Q5','Q4','Q3','Q2',
                             'JT','J9','J8','J7','J6',
                             'T9','T8','T7',
                             '98',
                             'AA','KK','QQ','JJ','TT','99','88','77','66','55','44','33','22']
        
        pass

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

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        my_cards = previous_state.hands[active]  # your cards
        opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed
        
        if opp_cards != []:
            if my_delta > 0 :
                self.wins_dict[my_cards[0][0]] += 1
                self.wins_dict[my_cards[1][0]] += 1
            self.showdowns_dict[my_cards[0][0]] += 1
            self.showdowns_dict[my_cards[1][0]] += 1
            if my_delta < 0 :
                self.wins_dict[opp_cards[0][0]] += 1
                self.wins_dict[opp_cards[1][0]] += 1
            self.showdowns_dict[opp_cards[0][0]] += 1
            self.showdowns_dict[opp_cards[1][0]] += 1 #[x][0] is value, [x][1] is suit

        pass

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

        allcard_winrate = [self.wins_dict[x] / self.showdowns_dict[x] for x in self.VALUES] #[0.9,0.1,0.2,0.3]
        ind = list(np.argsort(allcard_winrate)) #[1,2,3,0]
        
        if game_state.round_num % 100 == 0:
            print (game_state.round_num)
            print (allcard_winrate)

        new_cards = []
        for x in my_cards+board_cards:
            original_index = self.VALUES.index(x[0])
            current_index = ind.index(original_index)
            y = self.VALUES[current_index] + x[1]
            print(y)
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
            big_raise_times / self.games_played / 2


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



                card_to_winrate = []
                for i,x in enumerate(self.VALUES):
                    card_to_winrate.append([x,allcard_winrate[i]])
                card_to_winrate.sort(key = lambda x: x[1])
                permutation = {}
                for i in range(len(self.VALUES)):
                    permutation[card_to_winrate[i][0]] = self.VALUES[i]
                permuted_hand = str(permutation[my_cards[0][0]])+str(permutation[my_cards[1][0]])

                suited = False
                if my_cards[0][1] == my_cards[1][1]: suited = True


                preflop_flag = False
                if suited:
                    if permuted_hand in self.suited_top_60 or permuted_hand[::-1] in self.suited_top_60:
                        preflop_flag = True
                else:
                    if permuted_hand in self.unsuited_top_60 or permuted_hand[::-1] in self.unsuited_top_60:
                        preflop_flag = True



                # PRE-FLOP HIGH CARD
                if street == 0:
                    if preflop_flag:
                        return RaiseAction(raise_amount)
                    else:
                        if CheckAction in legal_actions:
                            return CheckAction()
                        else:
                            return FoldAction()

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
