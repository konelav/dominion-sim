from core.engine import cardType

import core.cards
from core.cards import Treasure, Victory, Action, Attack, Reaction, \
    Curse, Copper, Silver, Gold, Estate, Duchy, Province


class Basic(object):
    def __init__(self, game):
        self.game = game
        self.player = None
    def setPlayer(self, player):
        self.player = player
    
    def _rest(self, card):
        return self.game.supply.countCards(card)
    def _picked(self, card):
        return self.game.supply.pickedCards(card)
    def _restp(self, card):
        rest, picked = self._rest(card), self._picked(card)
        return float(rest) / float(max(1, rest + picked))
    def _canpay(self):
        ret = self.player.money
        for card in self.player.hand.cards:
            if card.hasType(Treasure):
                ret += card.money
        return ret
    def _canbuy(self, card):
        card = cardType(card)
        if self.game.supply.countCards(card) == 0:
            return False
        return self._canpay() >= self.game.currentCost(card)
    def _deckp(self, *cards):
        total = sum([self.player.countCards(c) for c in cards])
        return float(self.player.count()) / float(max(1, total))
    def _playAllTreasures(self):
        treasures = [c for c in self.player.hand.cards if c.hasType(Treasure)]
        for card in treasures:
            self.player.play(card)
    
    def cleanup(self):
        pass
    
    def onBuy(self, player, card_type):
        pass
    def onPlay(self, player, card, targets):
        pass
    def onNewActivePlayer(self, player):
        pass
    def onGameOver(self, table):
        pass
    
    def discardForMilitia(self, count):
        candidates = self.player.hand.cards[:]
        candidates.sort(key=lambda c: (
            c.hasType(Action), c.hasType(Treasure), c.money
        ))
        return candidates[:count]
    def discardForLibrary(self, card):
        return True
    def putForBureaucrat(self, choices):
        return list(choices)[0]
    def revealMoat(self, card):
        return True
    def shuffleForChancellor(self):
        return False
    def discardForSpy(self, other, card):
        return (other is self.player) == (not card.hasType(Treasure, Action))
    def trashForThief(self, other, candidates):
        candidates.sort(key=lambda c: c.money, reverse=True)
        return candidates[0]
    def takeForThief(self, trashed):
        return [c for c in trashed if c.money > 1]
    
    def playForVassal(self, card):
        return
    def placeForSentry(self, cards):
        to_trash, to_discard = [], []
        for card in cards:
            if card.hasType(Curse):
                to_trash.append(card)
            elif not card.hasType(Treasure, Action):
                to_discard.append(card)
        return to_trash, to_discard, None
    def putForHarbinger(self):
        candidates = self.player.discard.cards[:]
        candidates.sort(key=lambda c: (
            c.hasType(Treasure), c.money, c.hasType(Action)
        ))
        top = candidates[-1]
        if top.money > 0 or top.hasType(Action):
            return top
    def trashForBandit(self, player, candidates):
        candidates.sort(key=lambda c: c.money)
        return candidates[0]
    
    def takeForSwindler(self, other, candidates):
        if Curse in candidates:
            return Curse
        candidates.sort(key=lambda c: (
            c.score, c.actions, c.money, c.hasType(Attack)
        ))
        return candidates[0]
    def discardForTorturer(self, other):
        return
    def choicesForPawn(self):
        return ["money", "action"]
    def giveForMasquerade(self):
        candidates = self.player.hand.cards[:]
        if Curse in candidates:
            return Curse
        candidates.sort(key=lambda c: (
            c.score, c.actions, c.money, c.hasType(Attack)
        ))
        return candidates[0]
    def trashForMasquerade(self):
        if Curse in self.player.hand:
            return Curse
    def putForCourtyard(self):
        candidates = self.player.hand.cards[:]
        candidates.sort(key=lambda c: (
            c.score, c.money, c.actions
        ))
        return candidates[-1]
    def guessForWishingWell(self):
        if self.player.deck.count() > 0:
            src = self.player.deck
        else:
            src = self.player.discard
        if src.count() == 0:
            return Curse
        candidates = [(len(p), c) for (c, p) in src.piles.items()]
        candidates.sort()
        return candidates[-1][1]
    def gainForSaboteur(self, cost):
        for card in (Province, Gold, Silver, Duchy):
            if self.game.supply.countCards(card) > 0 and self.game.currentCost(card) <= cost:
                return card
    def revealSecretChamber(self, card):
        return True
    def putForSecretChamber(self):
        candidates = self.player.hand.cards[:]
        candidates.sort(key=lambda c: (
            c.score, c.money, c.actions
        ))
        return candidates[-2:]
    def orderForScout(self, to_put):
        return range(len(to_put))
    def choicesForCourtier(self, ntypes):
        return ["gold", "money", "action", "buy"]
    def chooseForLurker(self, can_trash, can_take):
        if len(can_take) > 0:
            can_take.sort(key=lambda c: (c.cost, c.money, c.score, c.actions))
            top = can_take[-1]
            if top.money > 0 or top.actions > 0 or top.score > 0 or len(can_trash) == 0:
                return None, top
        can_trash.sort(key=lambda c: self.game.supply.pickedCards(c))
        return can_trash[-1], None
    def insertForSecretPassage(self, N):
        candidates = self.player.hand.cards[:]
        candidates.sort(key=lambda c: (
            c.score, c.money, c.actions
        ))
        return candidates[-1], 0
    def revealDiplomat(self, card):
        return False
    def discardForDiplomat(self):
        candidates = self.player.hand.cards[:]
        candidates.sort(key=lambda c: (
            c.hasType(Action), c.hasType(Treasure), c.money
        ))
        return candidates[:3]
    def orderForPatrol(self, to_put):
        return range(len(to_put))


class BigMoney(Basic):
    max_provinces_for_duchy = 8.0 / 12.0
    max_provinces_for_estate = 2.0 / 12.0
    def action(self):
        pass
    def buy(self):
        self._playAllTreasures()
        if self._canbuy("province"):
            self.player.buy("province")
        elif self._canbuy("duchy") and self._restp("province") <= self.max_provinces_for_duchy:
            self.player.buy("duchy")
        elif self._canbuy("estate") and self._restp("province") <= self.max_provinces_for_estate:
            self.player.buy("estate")
        elif self._canbuy("gold"):
            self.player.buy("gold")
        elif self._canbuy("silver"):
            self.player.buy("silver")


class Discarder(BigMoney):
    max_provinces_for_duchy = 5.0 / 12.0
    max_provinces_for_estate = 0.0 / 12.0
    def action(self):
        if self.player.hand.countCards("chapel") > 0 and not self._canbuy("province"):
            need_silver = (self._deckp("gold") > 1.8)
            total_money = 0
            for z in self.player.zones:
                for c, p in z.piles.items():
                    if c.hasType(Treasure):
                        total_money += c.money*len(p)
            max_copper_to_trash = max(0, total_money - 3)
            max_silver_to_trash = max(0, total_money - 6) // 2
            targets = []
            targets += ["curse"] * self.player.hand.countCards("curse")
            targets += ["copper"] * min(max_copper_to_trash, self.player.hand.countCards("copper"))
            if self._restp("province") > self.max_provinces_for_estate:
                targets += ["estate"] * self.player.hand.countCards("estate")
            if not need_silver:
                targets += ["silver"] * min(max_silver_to_trash, self.player.hand.countCards("silver"))
            self.player.play("chapel", targets)
    def buy(self):
        self._playAllTreasures()
        need_silver = (self._deckp("gold") > 1.8)
        need_chapel = (
            (self.player.countCards("chapel") < 1) or
            (self.player.countCards("curse") > 2 and (self._deckp("chapel") > 8))
        )
        if self._canbuy("province"):
            self.player.buy("province")
        elif self._canbuy("duchy") and self._restp("province") <= self.max_provinces_for_duchy:
            self.player.buy("duchy")
        elif self._canbuy("estate") and self._restp("province") <= self.max_provinces_for_estate:
            self.player.buy("estate")
        elif self._canbuy("chapel") and need_chapel and self.player.money <= 3:
            self.player.buy("chapel")
        elif self._canbuy("gold"):
            self.player.buy("gold")
        elif self._canbuy("silver") and need_silver:
            self.player.buy("silver")


class Attacker(BigMoney):
    use_attacks = ["witch", "militia", "bandit", "thief", "spy"]
    def action(self):
        gold_num = self.game.supply.pickedCards("gold") - self.player.countCards("gold")
        silver_num = self.game.supply.pickedCards("silver") - self.player.countCards("silver")
        theft_needed = ((gold_num * 3 + silver_num) > 6)
        curse_needed = (self.game.supply.countCards("curse") > 0)
        while self.player.hand.countCards("spy") > 0:
            self.player.play("spy")
        if self.player.hand.countCards("witch") > 0 and curse_needed:
            self.player.play("witch")
        elif self.player.hand.countCards("militia") > 0:
            self.player.play("militia")
        elif theft_needed and self.player.hand.countCards("thief") > 0:
            self.player.play("thief")
        else:
            for c in self.player.hand.cards:
                if c.hasType(Action):
                    self.player.play(c)
                    break
    def buy(self):
        self._playAllTreasures()
        
        gold_num = self.game.supply.pickedCards("gold") - self.player.countCards("gold")
        silver_num = self.game.supply.pickedCards("silver") - self.player.countCards("silver")
        theft_needed = ((gold_num * 3 + silver_num) > 6)
        curse_needed = (self.game.supply.countCards("curse") > 0)
        
        can_buy_action = self._deckp(*self.use_attacks) > 8
        
        if self._canbuy("province"):
            self.player.buy("province")
        elif self._canbuy("duchy") and self._restp("province") <= self.max_provinces_for_duchy:
            self.player.buy("duchy")
        elif self._canbuy("estate") and self._restp("province") <= self.max_provinces_for_estate:
            self.player.buy("estate")
        elif self._canbuy("witch") and "witch" in self.use_attacks and curse_needed and can_buy_action:
            self.player.buy("witch")
        elif self._canbuy("bandit") and "bandit" in self.use_attacks and theft_needed and can_buy_action:
            self.player.buy("bandit")
        elif self._canbuy("thief") and "thief" in self.use_attacks and theft_needed and can_buy_action:
            self.player.buy("thief")
        elif self._canbuy("militia") and "militia" in self.use_attacks and can_buy_action:
            self.player.buy("militia")
        elif self._canbuy("spy") and "spy" in self.use_attacks and can_buy_action:
            self.player.buy("spy")
        elif self._canbuy("gold"):
            self.player.buy("gold")
        elif self._canbuy("silver"):
            self.player.buy("silver")


class Gardener(Basic):
    max_provinces_for_workshop_estate = 6.0 / 12.0
    max_provinces_for_gardens = 10.0 / 12.0
    max_provinces_for_duchy = 8.0 / 12.0
    max_provinces_for_estate = 2.0 / 12.0
    def __init__(self, game):
        Basic.__init__(self, game)
        self.gardens_present = game.supply.hasPile("gardens")
    def action(self):
        while True:
            candidates = [card for card in self.player.hand.cards if card.actions > 0]
            if len(candidates) == 0:
                break
            self.player.play(candidates[0])
        
        while self.player.actions > 0:
            if self.player.hand.countCards("workshop") > 0:
                if self.game.supply.countCards("gardens") > 0:
                    self.player.play("workshop", ["gardens"])
                elif self.game.supply.countCards("workshop") > 0 and self._deckp("workshop") > 8:
                    self.player.play("workshop", ["workshop"])
                elif self.gardens_present and self.game.supply.countCards("woodcutter") > 0 and self._deckp("woodcutter") > 8:
                    self.player.play("workshop", ["woodcutter"])
                elif self.gardens_present and self.game.supply.countCards("village") > 0 and self._deckp("village") > 10:
                    self.player.play("workshop", ["village"])
                elif self._restp("province") <= self.max_provinces_for_workshop_estate and self.game.supply.countCards("estate") > 0:
                    self.player.play("workshop", ["estate"])
                elif self.game.supply.countCards("silver") > 0:
                    self.player.play("workshop", ["silver"])
                else:
                    self.player.drop("workshop")
            else:
                candidates = [((card.buys, card.draw_cards, card.money), card)
                              for card in self.player.hand.cards if
                              card.hasType(Action)
                ]
                if len(candidates) == 0:
                    break
                candidates.sort(key=lambda x: x[0], reverse=True)
                _, card = candidates[0]
                self.player.play(card)
        
    def buy(self):
        self._playAllTreasures()
        while self.player.buys > 0:
            if self._canbuy("province"):
                self.player.buy("province")
            elif self._canbuy("gardens") and self._restp("province") <= self.max_provinces_for_gardens:
                self.player.buy("gardens")
            elif self._canbuy("duchy") and self._restp("province") <= self.max_provinces_for_duchy:
                self.player.buy("duchy")
            elif self._canbuy("estate") and self._restp("province") <= self.max_provinces_for_estate:
                self.player.buy("estate")
            elif self._canbuy("market"):
                self.player.buy("market")
            elif self._canbuy("workshop") and self.gardens_present and self._deckp("workshop") > 7:
                self.player.buy("workshop")
            elif self._canbuy("woodcutter") and self.gardens_present and self._deckp("woodcutter") > 7:
                self.player.buy("woodcutter")
            elif self._canbuy("village") and self.gardens_present and self._deckp("village") > 10:
                self.player.buy("village")
            elif self._canbuy("gold"):
                self.player.buy("gold")
            elif self._canbuy("silver"):
                self.player.buy("silver")
            elif self.gardens_present and self._canbuy("copper"):
                self.player.buy("copper")
            else:
                break
    
    def discardForMilitia(self, count):
        candidates = self.player.hand.cards[:]
        candidates.sort(key=lambda c: (
            c.hasType(Action), c.buys, c.hasType(Treasure), c.money
        ))
        return candidates[:count]
    def takeForThief(self, trashed):
        return trashed
    
    def trashForThief(self, other, candidates):
        candidates.sort(key=lambda c: c.money, reverse=True)
        return (candidates[0].money > 1)
    def takeForThief(self, trashed):
        return [c for c in trashed if c.money > 1]
    
    def choicesForPawn(self):
        return ["buy", "action"]
    def giveForMasquerade(self):
        candidates = self.player.hand.cards[:]
        if Curse in candidates:
            return Curse
        candidates.sort(key=lambda c: (
            c.score, c.buys, c.actions, c.money, c.hasType(Attack)
        ))
        return candidates[0]
    def gainForSaboteur(self, cost):
        for card in (Province, core.cards.Gardens, Gold, Silver, Duchy):
            if self.game.supply.countCards(card) > 0 and self.game.currentCost(card) <= cost:
                return card
