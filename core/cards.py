from core.common import RulesViolation


class Card(object):
    setname = None
    
    cost = 0
    score = 0
    money = 0
    actions = 0
    buys = 0
    draw_cards = 0
    
    def __init__(self):
        self.zone = None
    def __str__(self):
        return "{:8s} - (${}){}{}".format(
            self.__class__.__mro__[1].__name__,
            self.cost,
            self.__class__.__name__,
            ("" if self.score == 0 else " ({:+d}VP) ".format(self.score)),)
    @classmethod
    def hasType(cls, *cls_types):
        return any([issubclass(cls, cls_type) for cls_type in cls_types])
    @classmethod
    def name(cls):
        return cls.__name__.lower()
    def play(self, game, targets=[]):
        player, phase = game.activeTurn()
        if phase == "action" and self.hasType(Action):
            if player.actions <= 0:
                raise RulesViolation("No more actions")
            player.actions += self.actions - 1
            player.money += self.money
            player.buys += self.buys
            player.draw(self.draw_cards)
            player.actions_played += 1
        elif phase == "buy" and self.hasType(Treasure):
            player.money += self.money
        else:
            raise RulesViolation("Can only play Action cards during "
                "action phase and Buy cards during buy phase")
    def bonusScores(self, game):
        return 0
    def scores(self, game):
        return self.score + self.bonusScores(game)


class Treasure(Card):
    pass

class Victory(Card):
    pass

class Action(Card):
    pass

class Attack(Action):
    def affect(self, player, other, game):
        pass
    def play(self, game, targets=[]):
        Action.play(self, game)
        active = game.activePlayer()
        for player in game.players:
            affected = True
            if player is not active:
                for card in player.hand.cards:
                    if card.hasType(Reaction):
                        if card.whenAnotherPlayerPlaysAttack(player, self):
                            affected = False
            if affected:
                self.affect(active, player, game)

class Reaction(Action):
    # returns <affection_canceled>
    def whenAnotherPlayerPlaysAttack(self, player, card):
        return


##########################
###  CORE SET OF CARDS ###
##########################

class Curse(Card):
    setname = 'Base'
    score = -1
    def play(self, game, targets=[]):
        raise RulesViolation("Can't play curse")


class Copper(Treasure):
    setname = 'Base'
    cost = 0
    money = 1
    def play(self, game, targets=[]):
        Treasure.play(self, game, targets)
        player = game.activePlayer()
        player.money += player.played.countCards(Coppersmith)
class Silver(Treasure):
    setname = 'Base'
    cost = 3
    money = 2
    def play(self, game, targets=[]):
        Treasure.play(self, game, targets)
        player = game.activePlayer()
        if player.played.countCards(Silver) == 0:  # first silver this turn
            player.money += player.played.countCards(Merchant)
class Gold(Treasure):
    setname = 'Base'
    cost = 6
    money = 3

class Estate(Victory):
    setname = 'Base'
    cost = 2
    score = 1
class Duchy(Victory):
    setname = 'Base'
    cost = 5
    score = 3
class Province(Victory):
    setname = 'Base'
    cost = 8
    score = 6

##########################
###  BASE SET OF CARDS ###
##########################

class Gardens(Victory):
    setname = 'Base'
    cost = 4
    def bonusScores(self, game):
        return (self.zone.count() // 10) * 1


class Village(Action):
    setname = 'Base'
    cost = 3
    actions = 2
    draw_cards = 1
class Smithy(Action):
    setname = 'Base'
    cost = 4
    draw_cards = 3
class Market(Action):
    setname = 'Base'
    cost = 5
    money = 1
    actions = 1
    buys = 1
    draw_cards = 1
class Festival(Action):
    setname = 'Base'
    cost = 5
    money = 2
    actions = 2
    buys = 1
class Witch(Attack):
    setname = 'Base'
    cost = 5
    draw_cards = 2
    def affect(self, player, other, game):
        if other is not player:
            if game.supply.countCards(Curse) > 0:
                other.discard.put(game.supply.pickCard(Curse))
class Moneylender(Action):
    setname = 'Base'
    cost = 4
    def play(self, game, targets=[]):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if player.hand.countCards(Copper) > 0 and Copper in targets:
            player.drop(Copper, game.trash)
            player.money += 3
class Militia(Attack):
    setname = 'Base'
    cost = 4
    money = 2
    def affect(self, player, other, game):
        if other is not player:
            while other.hand.count() > 3:
                to_discard = other.strategy.discardForMilitia(other.hand.count() - 3)
                for card in to_discard:
                    other.drop(card)            
class CouncilRoom(Action):
    setname = 'Base'
    cost = 5
    buys = 1
    draw_cards = 4
    def play(self, game, targets):
        Action.play(self, game, targets)
        for player in game.nonActivePlayers():
            player.draw()
class Laboratory(Action):
    setname = 'Base'
    cost = 5
    actions = 1
    draw_cards = 2
class Library(Action):
    setname = 'Base'
    cost = 5
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        total_picked, max_picked = 0, player.count()
        while player.hand.count() < 7 and total_picked < max_picked:
            total_picked += 1
            for card in player.draw():
                if card.hasType(Action):
                    do_discard = player.strategy.discardForLibrary(card)
                    if do_discard:
                        player.drop(card)
class Mine(Action):
    setname = 'Base'
    cost = 5
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if len(targets) == 0:
            coins = [c for c in player.hand.cards if c.hasType(Treasure)]
            coins.sort(key=lambda c: c.cost)
            targets.append(coins[0])
        if len(targets) == 1:
            max_cost = game.currentCost(targets[0]) + 3
            coins = [c for c, l in game.supply.piles.items()
                     if c.hasType(Treasure) and len(l) > 0 and game.currentCost(c) <= max_cost]
            coins.sort(key=lambda c: c.money, reverse=True)
            targets.append(coins[0])
        to_trash, to_mine = targets[:2]
        if not (to_trash.hasType(Treasure) and to_mine.hasType(Treasure)):
            raise RulesViolation("Can't mine <{}> to <{}>: both must be treasure".format(to_trash, to_mine))
        if to_mine.cost > to_trash.cost + 3:
            raise RulesViolation("Can't mine <{}> to <{}>: maximum +3 cost".format(to_trash, to_mine))
        if game.supply.countCards(to_mine) <= 0:
            raise RulesViolation("Can't mine <{}>: not present in supply".format(to_mine))
        player.drop(to_trash, game.trash)
        player.hand.put(game.supply.pickCard(to_mine))
class Chapel(Action):
    setname = 'Base'
    cost = 2
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        for card in targets[:4]:
            player.drop(card, game.trash)
class Cellar(Action):
    setname = 'Base'
    cost = 2
    actions = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        for card in targets:
            player.drop(card)
        player.draw(len(targets))
class Bureaucrat(Attack):
    setname = 'Base'
    cost = 4
    def affect(self, player, other, game):
        if player is other:
            return
        choices = set([c.name() for c in player.hand.cards if c.hasType(Victory)])
        if len(choices) == 1:
            player.drop(list(choices)[0], player.deck)
        elif len(choices) > 1:
            while True:
                to_put = player.strategy.putForBureaucrat(choices)
                if to_put in choices:
                    break
            player.drop(to_put, player.deck)
    def play(self, game, targets):
        Attack.play(self, game, targets)
        if game.supply.countCards(Silver) > 0:
            game.activePlayer().deck.put(game.supply.pickCard(Silver))
class Workshop(Action):
    setname = 'Base'
    cost = 3
    def play(self, game, targets):
        Action.play(self, game, targets)
        game.activePlayer().discard.put(game.supply.pickCard(targets[0]))
class Moat(Reaction):
    setname = 'Base'
    cost = 2
    draw_cards = 2
    def whenAnotherPlayerPlaysAttack(self, player, card):
        if player.strategy.revealMoat(card):
            return True
class Remodel(Action):
    setname = 'Base'
    cost = 4
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        to_trash, to_model = targets[:2]
        if game.supply.countCards(to_model) <= 0:
            raise RulesViolation("Can't remodel <{}>: not present on supply".format(to_model))
        if game.currentCost(to_trash) + 2 > game.currentCost(to_model):
            raise RulesViolation("Can't remodel <{}> => <{}>: cost violation".format(to_trash, to_model))
        player.drop(to_trash, game.trash)
        player.discard.put(game.supply.pickCard(to_model))
class ThroneRoom(Action):
    setname = 'Base'
    cost = 4
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        while len(targets) < 3:
            targets.append([])
        to_dup, targets1, targets2 = targets[:3]
        if type(targets1) not in (tuple, list):
            targets1 = [targets1]
        if type(targets2) not in (tuple, list):
            targets2 = [targets2]
        if not to_dup.hasType(Action):
            raise RulesViolation("Can't dup non-action card with throne room")
        card = player.hand.pick(to_dup)
        player.actions += 2
        try:
            card.play(game, targets1)
            card.play(game, targets2)
        except Exception:
            player.hand.put(card)
            raise
        player.played.put(card)

########################################
###  BASE - 1st EDITION SET OF CARDS ###
########################################

class Woodcutter(Action):
    setname = 'Base1E'
    cost = 3
    money = 2
    buys = 1
class Feast(Action):
    setname = 'Base1E'
    cost = 4
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        card = targets[0]
        if game.currentCost(card) > 5:
            raise RulesViolation("Cost of card must be not greater that 5")
        game.trash.put(player.played.pick(self))
        player.discard.put(game.supply.pickCard(card))
class Chancellor(Action):
    setname = 'Base1E'
    cost = 3
    money = 2
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if player.deck.count() > 0:
            if player.strategy.shuffleForChancellor():
                while player.deck.count() > 0:
                    player.discard.put(player.deck.pick())
class Adventurer(Action):
    setname = 'Base1E'
    cost = 6
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        picked_treasures = 0
        total_picks, max_picks = 0, player.deck.count() + player.discard.count()
        while picked_treasures < 2 and total_picks < max_picks:
            cards = player.draw()
            total_picks += 1
            if len(cards) == 0:
                break
            if cards[0].hasType(Treasure):
                picked_treasures += 1
            else:
                player.drop(cards[0])
class Spy(Attack):
    setname = 'Base1E'
    cost = 4
    actions = 1
    draw_cards = 1
    def affect(self, player, other, game):
        for card in other.draw():
            discard = player.strategy.discardForSpy(other, card)
            other.drop(card, other.discard if discard else other.deck)
class Thief(Attack):
    setname = 'Base1E'
    cost = 4
    def affect(self, player, other, game):
        if player is other:
            return
        candidates = []
        for card in other.draw(2):
            if card.hasType(Treasure):
                candidates.append(card)
            else:
                other.drop(card)
        if len(candidates) == 0:
            return
        to_trash = player.strategy.trashForThief(other, candidates)
        other.drop(to_trash, game.trash)
        self.trashed.append(to_trash)
        for card in candidates:
            if card is not to_trash:
                other.drop(card)
    def play(self, game, targets):
        self.trashed = []
        Attack.play(self, game, targets)
        player = game.activePlayer()
        if len(self.trashed) > 0:
            for card in player.strategy.takeForThief(self.trashed):
                player.discard.put(game.trash.pick(card))
        self.trashed = []

########################################
###  BASE - 2nd EDITION SET OF CARDS ###
########################################

class Vassal(Action):
    setname = 'Base2E'
    cost = 3
    money = 2
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        for card in player.draw():
            if card.hasType(Action):
                targets = player.strategy.playForVassal(card)
                if targets is not None and targets is not False:
                    player.actions += 1
                    player.play(card, targets)
class Merchant(Action):
    setname = 'Base2E'
    cost = 3
    actions = 1
    draw_cards = 1
class Sentry(Action):
    setname = 'Base2E'
    cost = 5
    actions = 1
    draw_cards = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        cards = player.draw(2)
        to_trash, to_discard, order = player.strategy.placeForSentry(cards)
        for card in to_trash:
            player.drop(card, game.trash)
        for card in to_discard:
            player.drop(card, player.discard)
        to_deck = [c for c in cards if c not in to_trash and c not in to_discard]
        if len(to_deck) <= 1 or order is None or len(order) != len(to_deck):
            order = range(len(to_deck))
        for i in order:
            player.drop(to_deck[i], player.deck)
class Poacher(Action):
    setname = 'Base2E'
    cost = 4
    actions = 1
    money = 1
    draw_cards = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        cnt = game.supply.emptyTypes()
        if cnt >= player.hand.count():
            to_discard = player.hand.cards
        else:
            if len(targets) < cnt:
                raise RulesViolation("Not enough targets for discarding for Poacher")
            to_discard = targets[:cnt]
        for card in to_discard:
            player.drop(card)
class Harbinger(Action):
    setname = 'Base2E'
    cost = 3
    actions = 1
    draw_cards = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if player.discard.count() > 0:
            card = player.strategy.putForHarbinger()
            if card is not None and card in player.discard.cards:
                player.deck.put(player.discard.pick(card))
class Bandit(Attack):
    setname = 'Base2E'
    cost = 5
    def affect(self, player, other, game):
        if player is other:
            return
        candidates = [c for c in other.draw(2)
                      if c.hasType(Treasure) and not c.hasType(Copper)]
        to_trash = None
        if len(set([c.name() for c in candidates])) == 1:
            to_trash = candidates[0]
        elif len(candidates) > 1:
            to_trash = other.strategy.trashForBandit(player, candidates)
        for card in candidates:
            other.drop(card, game.trash if card is to_trash else other.discard)
    def play(self, game, targets):
        Attack.play(self, game, targets)
        player = game.activePlayer()
        if game.supply.countCards(Gold) > 0:
            player.discard.put(game.supply.pickCard(Gold))
class Artisan(Action):
    setname = 'Base2E'
    cost = 6
    def play(self, game, targets):
        Attack.play(self, game, targets)
        player = game.activePlayer()
        to_gain, to_put = targets[:2]
        if game.currentCost(to_gain) > 5:
            raise RulesViolation("Can't gain <{}>: too big cost".format(to_gain))
        player.hand.put(game.supply.pickCard(to_gain))
        player.drop(to_put, player.deck)

##############################
###  INTRIGUE SET OF CARDS ###
##############################

class Steward(Action):
    setname = 'Intrigue'
    cost = 3
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if len(targets) == 0:
            player.money += 2
        elif len(targets) >= 2:
            for card in targets[:2]:
                player.drop(card, game.trash)
        else:
            player.draw(2)
class Swindler(Attack):
    setname = 'Intrigue'
    cost = 3
    money = 2
    def affect(self, player, other, game):
        if player is not other:
            for card in other.draw():
                game.trash.put(card)
                candidates = [c for c, l in game.supply.piles.items()
                    if len(l) > 0 and game.currentCost(c) == game.currentCost(card)]
                if len(candidates) == 0:
                    continue
                elif len(candidates) == 1:
                    choice = candidates[0]
                else:
                    choice = player.strategy.takeForSwindler(other, candidates)
                other.discard.put(game.supply.pickCard(choice))
class Torturer(Attack):
    setname = 'Intrigue'
    cost = 5
    draw_cards = 3
    def affect(self, player, other, game):
        if player is not other:
            discard = other.strategy.discardForTorturer(other)
            if discard is None:
                if game.supply.countCards(Curse) > 0:
                    other.discard.put(game.supply.pickCard(Curse))
                return
            if len(discard) < 2:
                if len(player.hand.cards) >= 2:
                    raise RulesViolation("You must discard 2 cards for Torturer")
                discard = player.hand.cards
            for card in discard[:2]:
                player.drop(card)
class TradingPost(Action):
    setname = 'Intrigue'
    cost = 5
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if len(targets) >= 2:
            for card in targets[:2]:
                player.drop(card, game.trash)
            if game.supply.countCards(Silver) > 0:
                player.hand.put(game.supply.pickCard(Silver))
class Pawn(Action):
    setname = 'Intrigue'
    cost = 2
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        choices = set(player.strategy.choicesForPawn())
        for choice in list(choices)[:2]:
            if choice == "card":
                player.draw()
            elif choice == "action":
                player.actions += 1
            elif choice == "buy":
                player.buys += 1
            elif choice == "money":
                player.money += 1
class Nobles(Action, Victory):
    setname = 'Intrigue'
    cost = 6
    score = 2
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if len(targets) > 0:
            player.draw(3)
        else:
            player.actions += 2
class Minion(Attack):
    setname = 'Intrigue'
    cost = 5
    actions = 1
    def affect(self, player, other, game):
        if other is player or other.hand.count() >= 5:
            other.discard.mix(other.hand)
            other.draw(4)
    def play(self, game, targets):
        player = game.activePlayer()
        if len(targets) > 0:
            Attack.play(self, game, targets)
        else:
            Action.play(self, game, targets)
            player.money += 2

class MiningVillage(Action):
    setname = 'Intrigue'
    cost = 4
    draw_cards = 1
    actions = 2
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if len(targets) > 0:
            game.trash.put(player.played.pick(self))
            player.money += 2
class Masquerade(Action):
    setname = 'Intrigue'
    cost = 3
    draw_cards = 2
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        choices = []
        for p in game.players:
            if p.hand.count() == 0:
                choices.append(None)
            else:
                choices.append(p.strategy.giveForMasquerade())
        for i, p1 in enumerate(game.players):
            if choices[i] is None:
                continue
            p2 = game.players[(i + 1) % len(game.players)]
            p2.hand.put(p1.hand.pick(choices[i]))
        card = player.strategy.trashForMasquerade()
        if card is not None:
            player.drop(card, game.trash)
class ShantyTown(Action):
    setname = 'Intrigue'
    cost = 3
    actions = 2
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        nactions = len([c for c in player.hand if c.hasType(Action)])
        if nactions == 0:
            player.draw(2)
class Conspirator(Action):
    setname = 'Intrigue'
    cost = 4
    money = 2
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if player.actions_played >= 3:
            player.draw()
            player.actions += 1
class Courtyard(Action):
    setname = 'Intrigue'
    cost = 2
    draw_cards = 3
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if len(targets) == 0:
            targets = [player.strategy.putForCourtyard()]
        player.deck.put(player.hand.pick(targets[0]))
class Baron(Action):
    setname = 'Intrigue'
    cost = 4
    buys = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        estates = [c for c in targets if c.hasType(Estate)]
        if len(estates) > 0:
            player.drop(Estate)
            player.money += 4
        elif game.supply.countCards(Estate) > 0:
            player.discard.put(game.supply.pickCard(Estate))
class Bridge(Action):
    setname = 'Intrigue'
    cost = 4
    buys = 1
    money = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        game.modifyCost(-1)
class Duke(Victory):
    setname = 'Intrigue'
    cost = 5
    def bonusScores(self, game):
        return self.zone.countCards(Duchy)
class Harem(Treasure, Victory):
    setname = 'Intrigue'
    cost = 6
    money = 2
    score = 2
class IronWorks(Action):
    setname = 'Intrigue'
    cost = 4
    def play(self, game, targets):
        Action.play(self, game, targets)
        card = targets[0]
        game.activePlayer().discard.put(game.supply.pickCard(card))
        if card.hasType(Acton):
            player.actions += 1
        if card.hasType(Treasure):
            player.money += 1
        if card.hasType(Victory):
            player.draw()
class WishingWell(Action):
    setname = 'Intrigue'
    cost = 3
    draw_cards = 1
    actions = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if len(targets) == 0:
            targets = [player.strategy.guessForWishingWell()]
        for card in player.draw():
            if card.name() != targets[0].name():
                player.drop(card, player.deck)
class Upgrade(Action):
    setname = 'Intrigue'
    cost = 5
    draw_cards = 1
    actions = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        to_trash, to_upgrade = targets[:2]
        if game.supply.countCards(to_upgrade) <= 0:
            raise RulesViolation("Can't upgrade <{}>: not present on supply".format(to_upgrade))
        if game.currentCost(to_trash) + 1 != game.currentCost(to_upgrade):
            raise RulesViolation("Can't upgrade <{}> => <{}>: cost violation".format(to_trash, to_upgrade))
        player.drop(to_trash, game.trash)
        player.discard.put(game.supply.pickCard(to_upgrade))

############################################
###  INTRIGUE - 1st EDITION SET OF CARDS ###
############################################

class Saboteur(Attack):
    setname = 'Intrigue1E'
    cost = 5
    def affect(self, player, other, game):
        if other is player:
            return
        max_n = other.deck.count() + other.discard.count()
        for _ in range(max_n):
            for card in other.draw():
                cost = game.currentCost(card)
                if cost >= 3:
                    other.drop(card, game.trash)
                    new_card = other.strategy.gainForSaboteur(cost - 2)
                    if new_card is not None and game.currentCost(new_card) <= cost - 2:
                        other.discard.put(game.supply.pickCard(new_card))
                    return
                other.drop(card)
class Tribute(Action):
    setname = 'Intrigue1E'
    cost = 5
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        ileft = (game.active_player + 1) % len(game.players)
        left = game.players[ileft]
        seen = set()
        for card in left.draw(2):
            if card.name() not in seen:
                seen.add(card.name())
                if card.hasType(Action):
                    player.actions += 2
                if card.hasType(Treasure):
                    player.money += 2
                if card.hasType(Victory):
                    player.draw(2)
            left.drop(card)
class GreatHall(Action, Victory):
    setname = 'Intrigue1E'
    cost = 3
    score = 1
    draw_cards = 1
    actions = 1
class Coppersmith(Action):
    setname = 'Intrigue1E'
    cost = 4
class SecretChamber(Reaction):
    setname = 'Intrigue1E'
    cost = 2
    def whenAnotherPlayerPlaysAttack(self, player, card):
        if player.strategy.revealSecretChamber(card):
            player.draw(2)
            targets = player.strategy.putForSecretChamber()
            if len(targets) < 2 and len(targets) < len(player.hand.cards):
                raise RulesViolation("You must put 2 cards for Secret Chamber")
            for card in targets[:2]:
                player.drop(card, player.deck)
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        for card in targets:
            player.drop(card)
            player.money += 1
class Scout(Action):
    setname = 'Intrigue1E'
    cost = 4
    actions = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        to_put = []
        for card in player.draw(4):
            if not card.hasType(Victory):
                to_put.append(card)
        if len(to_put) <= 1:
            order = range(len(to_put))
        else:
            order = player.strategy.orderForScout(to_put)
        for i in order:
            player.drop(to_put[i], player.deck)

############################################
###  INTRIGUE - 2nd EDITION SET OF CARDS ###
############################################

class Courtier(Action):
    setname = 'Intrigue2E'
    cost = 5
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        ntypes = sum([int(targets[0].hasType(T)) for T in
            [Curse, Treasure, Victory, Action, Attack, Reaction]])
        choices = set(player.strategy.choicesForCourtier(ntypes))
        for choice in list(choices)[:ntypes]:
            if choice == "action":
                player.actions += 1
            elif choice == "buy":
                player.buys += 1
            elif choice == "money":
                player.money += 3
            elif choice == "gold" and game.supply.countCards(Gold) > 0:
                player.discard.put(game.supply.pickCard(Gold))
class Lurker(Action):
    setname = 'Intrigue2E'
    cost = 2
    actions = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        can_trash = [c for c, l in game.supply.piles.items()
                     if len(l) > 0 and c.hasType(Action)]
        can_take, seen = [], set()
        for c in game.trash.cards:
            if c.hasType(Action) and c.name() not in seen:
                can_take.append(c)
                seen.add(c.name())
        if len(can_trash) > 0 or len(can_take) > 0:
            to_trash, to_take = player.strategy.chooseForLurker(can_trash, can_take)
            if to_trash is not None:
                game.trash.put(game.supply.pickCard(to_trash))
            else:
                player.discard.put(game.trash.pick(to_take))
class Mill(Action, Victory):
    setname = 'Intrigue2E'
    cost = 4
    score = 1
    draw_cards = 1
    actions = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if len(targets) >= 2:
            for card in targets[:2]:
                player.drop(card)
            player.money += 2
class Replace(Attack):
    setname = 'Intrigue2E'
    cost = 5
    def affect(self, player, other, game):
        if self.affect_curse:
            if other is not player:
                if game.supply.countCards(Curse) > 0:
                    other.discard.put(game.supply.pickCard(Curse))
    def play(self, game, targets):
        player = game.activePlayer()
        to_trash, to_replace = targets[:2]
        if game.supply.countCards(to_replacel) <= 0:
            raise RulesViolation("Can't replace <{}>: not present on supply".format(to_replace))
        if game.currentCost(to_trash) + 2 > game.currentCost(to_replace):
            raise RulesViolation("Can't replace <{}> => <{}>: cost violation".format(to_trash, to_replace))
        player.drop(to_trash, game.trash)
        card = game.supply.pickCard(to_replace)
        if card.hasType(Action) or card.hasType(Treasure):
            player.deck.put(card)
        else:
            player.discard.put(card)
        self.affect_curse = card.hasType(Victory)
        Attack.play(self, game, targets)
class SecretPassage(Action):
    setname = 'Intrigue2E'
    cost = 4
    draw_cards = 2
    actions = 1
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        N = player.hand.count()
        card, place = player.strategy.insertForSecretPassage(N)
        player.deck.cards.insert(place, player.hand.pick(card))
class Diplomat(Reaction):
    setname = 'Intrigue2E'
    cost = 4
    draw_cards = 2
    def whenAnotherPlayerPlaysAttack(self, player, card):
        if player.hand.count() < 5:
            return
        if player.strategy.revealDiplomat(card):
            player.draw(2)
            to_discard = player.strategy.discardForDiplomat()
            if len(to_discard) < 3:
                raise RulesViolation("You must choose 3 cards to discard")
            for card in to_discard[:3]:
                player.drop(card)
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        if player.hand.count() <= 5:
            player.actions += 2
class Patrol(Action):
    setname = 'Intrigue2E'
    cost = 5
    draw_cards = 3
    def play(self, game, targets):
        Action.play(self, game, targets)
        player = game.activePlayer()
        to_put = []
        for card in player.draw(4):
            if not (card.hasType(Victory) or card.hasType(Curse)):
                to_put.append(card)
        if len(to_put) <= 1:
            order = range(len(to_put))
        else:
            order = player.strategy.orderForPatrol(to_put)
        for i in order:
            player.drop(to_put[i], player.deck)
