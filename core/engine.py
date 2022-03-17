import random
import copy
import traceback

from core.common import RulesViolation, UnknownCard

import core.rules as rules
import core.cards as cards


CARD_BY_NAME = {}
for vname in dir(cards):
    c = getattr(cards, vname)
    try:
        if issubclass(c, cards.Card) and hasattr(c, 'name'):
            CARD_BY_NAME[c.name()] = c
    except TypeError:
        pass


def cardType(card):
    global CARD_BY_NAME
    if hasattr(card, 'name'):
        card = card.name()
    if hasattr(card, 'lower'):
        card = card.lower()
    if card in CARD_BY_NAME:
        return CARD_BY_NAME[card]
    raise UnknownCard(str(card))


def cardTypes(lst):
    return [
        cardTypes(card) if type(card) in (list, tuple) else cardType(card)
        for card in lst
    ]


def cardsOfType(card_type):
    ret = []
    for vname in dir(cards):
        c = getattr(cards, vname)
        try:
            if issubclass(c, card_type) and c is not card_type:
                ret.append(c)
        except TypeError as ex:
            pass
    return ret


class PiledZone(object):
    def __init__(self):
        self.piles = dict()
        self.picked = dict()
    def __str__(self):
        return "Total {} card(s):\n{}".format(self.count(),
            "\n".join(sorted([
            "({}$) {:32s} [x{:2d}]".format(card_type.cost, card_type.name(), len(pile))
            for card_type, pile in self.piles.items()
        ])))
    def count(self):
        return sum([len(pile) for pile in self.piles.values()])
    def countCards(self, card_type):
        card_type = cardType(card_type)
        return len(self.piles.get(card_type, []))
    def pickedCards(self, card_type):
        card_type = cardType(card_type)
        return self.picked.get(card_type, 0)
    def emptyPiles(self, include_curse=False):
        return len([
            card_type for card_type, pile in self.piles.items() 
            if (include_curse or not card_type.hasType(cards.Curse)) and len(pile) == 0
        ])
    def hasPile(self, card_type):
        try:
            card_type = cardType(card_type)
        except UnknownCard:
            return False
        return (card_type in self.piles)
    def pickCards(self, card_or_type, count=1, remove_empty=False):
        card_type = cardType(card_or_type)
        pile = self.piles.get(card_type, [])
        if len(pile) < count:
            raise RulesViolation("No card <{}> in zone <>".format(card_type, self))
        if card_or_type in pile and count == 1:
            ret = [card_or_type]
            pile.remove(card_or_type)
        else:
            ret = [pile.pop() for _ in range(count)]
        if remove_empty and len(pile) == 0 and card_type in self.piles:
            del self.piles[card_type]
        self.picked[card_type] = self.picked.get(card_type, 0) + count
        return ret
    def pickCard(self, card_or_type, remove_empty=False):
        return self.pickCards(card_or_type, count=1, remove_empty=remove_empty)[0]
    def putCard(self, card):
        card_type = cardType(card)
        if card_type not in self.piles:
            self.piles[card_type] = []
        self.piles[card_type].append(card)
    def putCards(self, cards):
        for card in cards:
            if card is not None:
                self.putType(card)
    def createPile(self, card_type, count=1):
        card_type = cardType(card_type)
        for _ in range(count):
            card = card_type()
            self.putCard(card)
        return self.piles.get(card_type, None)


class OrderedZone(PiledZone):
    def __init__(self):
        PiledZone.__init__(self)
        self.cards = []
    def count(self):
        return len(self.cards)
    def put(self, card):
        if type(card) in (tuple, list):
            for c in card:
                self.put(c)
            return
        card.zone = self
        self.cards.append(card)
        self.putCard(card)
    def pick(self, card_or_type=None):
        if card_or_type is None:
            if len(self.cards) == 0:
                raise RulesViolation("Trying to pick card from empty zone")
            card = self.cards[-1]
        elif card_or_type in self.cards:
            card = card_or_type
        else:
            card_type = cardType(card_or_type)
            if self.countCards(card_type) == 0:
                raise RulesViolation("Can't pick card of type <{}>: no such cards in zone".format(card_type))
            card = [c for c in self.cards if c.hasType(card_type)][0]
        self.cards.remove(card)
        picked = self.pickCard(card, remove_empty=True)
        picked.zone = None
        return picked
    def shuffle(self):
        random.shuffle(self.cards)
    def mix_to(self, other):
        if self is other:
            return
        while self.count() > 0:
            other.put(self.pick())
    def mix_from(self, other):
        if self is other:
            return
        while other.count() > 0:
            self.put(other.pick())


class Player(object):
    def __init__(self, strategy, name=""):
        self.strategy = strategy
        self.strategy_name = self.strategy.__class__.__name__
        self.game = strategy.game
        self.name = name
        self.deck = OrderedZone()
        self.hand = OrderedZone()
        self.played = OrderedZone()
        self.discard = OrderedZone()
        self.zones = (self.deck, self.hand, self.played, self.discard)
    def init(self, nplayer):
        self.nplayer = nplayer
        self.deck.put(self.game.supply.pickCards(cards.Copper, rules.INITIAL_COPPER))
        self.deck.put(self.game.supply.pickCards(cards.Estate, rules.INITIAL_ESTATES))
        self.deck.shuffle()
        self.draw(rules.CARDS_PER_HAND)
        self.turns_taken = 0
        self.money = self.actions = self.buys = self.actions_played = 0
        self.strategy.setPlayer(self)
    def count(self):
        return sum([zone.count() for zone in self.zones])
    def countCards(self, card_type):
        return sum([zone.countCards(card_type) for zone in self.zones])
    def draw(self, count=1):
        drawn = []
        for _ in range(count):
            if self.deck.count() == 0:
                if self.discard.count() == 0:
                    return drawn
                self.discard.shuffle()
                self.deck, self.discard = self.discard, self.deck
            card = self.deck.pick()
            self.hand.put(card)
            drawn.append(card)
        return drawn
    def drop(self, card_or_type, to_zone=None):
        if to_zone is None:
            to_zone = self.discard
        to_zone.put(self.hand.pick(card_or_type))
    def countScores(self):
        for z in self.zones:
            z.mix_to(self.deck)
        total = sum([card.scores(self.game) for card in self.deck.cards])
        return (total, -self.turns_taken)
    def buy(self, card_or_type):
        card_type = cardType(card_or_type)
        if self.buys < 1:
            raise RulesViolation("Can't buy: no more buys")
        cost = self.game.currentCost(card_type)
        if self.money < cost:
            raise RulesViolation("Can't buy: not enough money")
        if self.game.supply.countCards(card_type) < 1:
            raise RulesViolation("Can't buy: no such card in supply")
        self.buys -= 1
        self.money -= cost
        card = self.game.supply.pickCard(card_type)
        self.discard.put(card)
        for player in self.game.players:
            player.strategy.onBuy(self, card_type)
    def play(self, card_or_type, targets=[]):
        targets = cardTypes(targets)
        card = self.hand.pick(card_or_type)
        self.played.put(card)
        card.play(self.game, targets)
        for player in self.game.players:
            player.strategy.onPlay(self, card, targets)
    def doTurn(self):
        self.actions = 1
        self.buys = 1
        self.money = 0
        self.actions_played = 0
        
        for phase in rules.TURN_PHASES:
            self.game.setPhase(phase)
            getattr(self.strategy, phase)()
        
        self.hand.mix_to(self.discard)
        self.played.mix_to(self.discard)
        
        self.actions = 0
        self.buys = 0
        self.money = 0
        self.actions_played = 0
        self.draw(rules.CARDS_PER_HAND)
        self.turns_taken += 1


class Game(object):
    def __init__(self, strategies, card_types=[], set_names=['Base1E'],
                 first_player=None, seed=None):
        random.seed(seed)
        
        self.nplayers = nplayers = len(strategies)
        
        card_types = cardTypes(card_types)
        if len(card_types) > rules.SUPPLY_PILES:
            candidates = card_types
            card_types = []
        else:
            candidates = [c for c in CARD_BY_NAME.values()
                if c not in 
                    [cards.Curse, cards.Copper, cards.Silver, cards.Gold,
                    cards.Estate, cards.Duchy, cards.Province]
                    and any([c.setname is not None and
                             set_name.lower().startswith(c.setname.lower())
                        for set_name in set_names])
            ]
        while len(card_types) < rules.SUPPLY_PILES:
            card = candidates[random.randrange(0, len(candidates))]
            if card not in card_types:
                card_types.append(card)
        
        victory_cnt = (rules.VICTORY_CARDS_2_PLAYERS if nplayers == 2 else
                       rules.VICTORY_CARDS_3_PLAYERS if nplayers == 3 else
                       rules.VICTORY_CARDS_4_PLAYERS)
        
        self.supply = PiledZone()
        for card_type in card_types:
            if card_type in (cards.Estate, cards.Duchy, cards.Province):
                count = victory_cnt
            else:
                count = rules.ACTION_CARDS
            self.supply.createPile(card_type, count)
        
        self.supply.createPile(cards.Curse,
            rules.TOTAL_CURSE_CARDS_PER_PLAYER * (nplayers - 1))
        
        self.supply.createPile(cards.Copper, rules.TOTAL_COPPER_CARDS +
            rules.INITIAL_COPPER * nplayers)
        self.supply.createPile(cards.Silver, rules.TOTAL_SILVER_CARDS)
        self.supply.createPile(cards.Gold, rules.TOTAL_GOLD_CARDS)
        
        self.supply.createPile(cards.Estate, victory_cnt +
            rules.INITIAL_ESTATES * nplayers)
        self.supply.createPile(cards.Duchy, victory_cnt)
        self.supply.createPile(cards.Province, victory_cnt)
        
        self.trash = OrderedZone()
        
        self.players = []
        for nplayer, strategy_cls in enumerate(strategies, 1):
            name = "#{} ({})".format(nplayer, strategy_cls.__name__)
            strategy = strategy_cls(self)
            self.players.append(Player(strategy, name))
        
        if first_player is None:
            first_player = random.randrange(0, nplayers)
        
        self.active_player = first_player
        
        for nplayer, player in enumerate(self.players, 1):
            player.init(nplayer)
        
        self.phase = None
    
    def setPhase(self, phase):
        self.phase = phase
    
    def activePlayer(self):
        return self.players[self.active_player]
    
    def activeTurn(self):
        return self.players[self.active_player], self.phase
    
    def nonActivePlayers(self):
        ret = []
        for n in range(len(self.players)-1):
            index = (self.active_player + 1 + n) % len(self.players)
            ret.append(self.players[index])
        return ret
    
    def modifyCost(self, delta):
        self.cost_modifier += delta
    
    def currentCost(self, card_or_type):
        card_type = cardType(card_or_type)
        return card_type.cost + self.cost_modifier
    
    def gameOver(self):
        if self.supply.emptyPiles() >= rules.MAX_EMPTY_PILES:
            return True
        if self.supply.countCards(cards.Province) == 0:
            return True
        return False
    
    def turn(self):
        self.cost_modifier = 0
        player = self.activePlayer()
        for p in self.players:
            p.strategy.onNewActivePlayer(player)
        player.doTurn()
        if self.gameOver():
            return True
        self.active_player = (self.active_player + 1) % len(self.players)
        return False
    
    def scoreTable(self):
        table = [(player.countScores(), player.count(), i, player.name) 
                 for i, player in enumerate(self.players, 1)
        ]
        table.sort(reverse=True)
        top_score = table[0][0]
        ret = {}
        for rank, ((scores, turns), cards, nplayer, name) in enumerate(table, 1):
            winner = (top_score == (scores, turns))
            ret[nplayer] = (scores, -turns, cards, rank, winner, name)
        return ret
    
    def run(self):
        while not self.turn():
            pass
        table = self.scoreTable()
        for player in self.players:
            player.strategy.onGameOver(table)
        return table
