import traceback

from core.engine import cardType, cardTypes

import core.cards
from core.cards import Treasure, Victory, Action, Attack, Reaction, \
    Curse, Copper, Silver, Gold, Estate, Duchy, Province


def nestedArgs(args):
    args, tail = [], args
    while len(tail) > 0:
        el = tail.pop(0)
        if el in ('[', '(', '{', '<'):
            subargs, tail = nestedArgs(tail)
            args.append(subargs)
        elif el in (']', ')', '}', '>'):
            break
        else:
            args.append(el)
    return args, tail


def cardNames(lst):
    return ", ".join([
        "({})".format(cardNames(card)) if type(card) in (list, tuple) else card.name()
        for card in lst
    ])


class CLI(object):
    def __init__(self, game):
        self.game = game
        self.player = None
    def setPlayer(self, player):
        self.player = player
    def _canpay(self):
        ret = self.player.money
        for card in self.player.hand.cards:
            if card.hasType(Treasure):
                ret += card.money
        return ret
    
    def _inputCommand(self, prompt):
        return input(prompt)
    
    def _selectOption(self, prompt, options, default=None):
        print(prompt)
        if len(options) == 0:
            return
        if len(options) == 1:
            return options[0]
        if default is None:
            default = options[0]
        loptions = dict([(o.lower(), o) for o in options])
        prompt = " (select option: {}; default: {}) ".format(
            " ".join(options), default)
        while True:
            resp = input(prompt).strip().lower()
            if len(resp) == 0:
                return default
            if resp in loptions:
                return loptions[resp]
    
    def _selectOrder(self, prompt, cards):
        print(prompt)
        names = [card.name() for card in cards]
        if len(set(names)) <= 1:
            return range(len(names))
        prompt = " (select order: {}) ".format(" ".join(names))
        while True:
            resp = input(prompt)
            order = []
            names_dup = names[:]
            for n in resp.split():
                if n in names_dup:
                    i = names_dup.index(n)
                    order.append(i)
                    names_dup[i] = None
            if len(order) == len(names):
                return order
            print("you must select all items: {}".format(" ".join([
                n for n in names_dup if n is not None])))
    
    def _selectCards(self, prompt, candidates, min_count=0, max_count=None):
        print(prompt)
        if len(candidates) < min_count:
            min_count = len(candidates)
        all_cards = {}
        for card in candidates:
            if hasattr(card, 'name'):
                name = card.name().lower()
            else:
                name = card
            if name not in all_cards:
                all_cards[name] = []
            all_cards[name].append(card)
        names = ["{}{}".format(name, 
            "" if len(l) == 1 else "(x{})".format(len(l)))
            for name, l in all_cards.items()]
        if len(names) == min_count and len(names) == max_count:
            return candidates[:min_count], candidates[-min_count:]
        names.sort()
        prompt = " (select {} card(s): {}) ".format(
            ("any number" if (min_count == 0 and max_count is None) else
             "{}".format(min_count) if min_count == max_count else
             "at least {}".format(min_count) if max_count is None else
             "up to {}".format(max_count) if min_count == 0 else
             "{} to {}".format(min_count, max_count)),
            " ".join(names))
        selected = []
        while True:
            for name in input(prompt).split():
                l = all_cards.get(name.lower(), [])
                if len(l) > 0:
                    selected.append(l.pop())
            if len(selected) >= min_count:
                break
        if max_count is not None:
            selected = selected[:max_count]
        unselected = [card for card in candidates if card not in selected]
        return selected, unselected
    
    def doPhase(self, phase):
        if phase == "action":
            print("HAND:")
            print(self.player.hand)
        elif phase == "buy":
            print("SUPPLY: ")
            print(self.game.supply)
        
        if phase == "buy":
            treasures = [c for c in self.player.hand.cards if c.hasType(Treasure)]
            for card in treasures:
                self.player.play(card)
        
        while True:
            if phase == "action":
                actions_in_hand = [c for c in self.player.hand.cards if c.hasType(Action)]
                if self.player.actions == 0 or len(actions_in_hand) == 0:
                    print("(no actions remain, end action phase automatically)")
                    break
            elif phase == "buy":
                if self.player.buys == 0:
                    print("(no buys, end turn automatically)")
                    break
            
            try:
                command = self._inputCommand("[ #{} - {}, {} action(s), {} buy(s)    ${} ] >> ".format(
                    self.player.turns_taken+1, phase, self.player.actions,
                    self.player.buys, self._canpay()))
                if command == ".help" or command == "" or "?" in command:
                    print("  Available commands are:")
                    print("    .help                - print this message")
                    print("    .supply              - print supply state")
                    print("    .trash               - print trash state")
                    print("    .hand                - print hand state")
                    print("    .discard             - print discard state")
                    print("    .played              - print played state")
                    print("    .deck                - print your deck state")
                    print("    .end                 - end current phase ({})".format(phase))
                    print("    .                    - same as end")
                    print("    .exit                - terminate the game")
                    if phase == "action":
                        print("    <card_name>[ <target1>[ <target2> ...]] - play a card from hand with optional list of targets")
                    elif phase == "buy":
                        print("    <card_name>[ <card2>[ ...]]          - buy card(s) from supply")
                else:
                    tokens = command.split()
                    cmd, (args, _) = tokens[0], nestedArgs(tokens[1:])
                    if cmd == ".end" or cmd == ".":
                        break
                    elif cmd == ".exit":
                        print("Good bye!")
                        exit(0)
                    elif cmd in (".supply",):
                        print(self.game.supply)
                    elif cmd in (".trash",):
                        print(self.game.trash)
                    elif cmd in (".hand",):
                        print(self.player.hand)
                    elif cmd in (".discard",):
                        print(self.player.discard)
                    elif cmd in (".played",):
                        print(self.player.played)
                    elif cmd in (".deck",):
                        print(self.player.deck)
                    elif phase == "action" and not cmd.startswith("."):
                        self.player.play(cmd, args)
                    elif phase == "buy" and not cmd.startswith("."):
                        for card_name in [cmd] + args:
                            self.player.buy(card_name)
                    else:
                        print("Unknown command <{}>, type <help> to list available commands".format(cmd))
            except Exception:
                traceback.print_exc()
                continue
        
    def action(self):
        self.doPhase("action")
    
    def buy(self):
        self.doPhase("buy")
    
    def cleanup(self):
        pass
    
    def onBuy(self, player, card):
        print("Player <{}> buys card <{}>".format(player.name, card.name()))
    
    def onPlay(self, player, card, targets):
        print("Player <{}> plays card <{}>({})".format(
            player.name, card.name(), cardNames(targets)))
    
    def onNewActivePlayer(self, player):
        print("TURN #{} OF PLAYER <{}>".format(player.turns_taken + 1,
            player.name))
    
    def onGameOver(self, table):
        print("GAME OVER")
        for player in self.game.players:
            print("Player <{}>'s deck:".format(player.name))
            print(player.deck)
        print("Score table:")
        print("N[WIN]\tPLAYER          \tCARDS\tSCORES\tTURNS")
        lines = []
        for nplayer, (scores, turns, cards, rank, winner, name) in table.items():
            lines.append("{}[{}]\t{:16s}\t{}\t{}\t{}".format(rank,
                ("+" if winner else " "),
                name, cards, scores, turns))
        lines.sort()
        for line in lines:
            print(line)
    
    def discardForMilitia(self, count):
        return self._selectCards(
            "Discard card(s) for Militia:",
            self.player.hand.cards, count, count)[0]
    
    def discardForLibrary(self, card):
        return self._selectOption(
            "Discard for Library <{}>?".format(card),
            ["no", "yes"]) == "yes"
    
    def putForBureaucrat(self, choices):
        return self._selectCards(
            "Which victory card put for Bureaucrat?",
            choices, 1, 1)[0][0]
    
    def revealMoat(self, card):
        return self._selectOption(
            "Attack played: {}; reveal Moat?".format(card),
            ["yes", "no"]) == "yes"
    
    def discardForSpy(self, other, card):
        if other is self.player:
            name = "YOUR"
        else:
            name = other.name
        return self._selectOption(
            "{}'s top library card is <{}>. Discard it for Spy?".format(name, card),
            ["no", "yes"]) == "yes"
    
    def trashForThief(self, other, candidates):
        candidates.sort(key=lambda c: c.money, reverse=True)
        return self._selectCards(
            "Select {}'s treasure to be trashed:".format(other.name),
            candidates, 1, 1)[0][0]
    
    def takeForThief(self, trashed):
        return self._selectCards(
            "Select theft treasures to be taken:",
            trashed)[0]
    
    def playForVassal(self, card):
        resp = self._inputCommand("Select targets for Vassal's card <{}> ('end' for not playing):".format(card.name()))
        if resp == 'end':
            return
        return resp.split()
    
    def placeForSentry(self, cards):
        to_trash, cards = self._selectCards("Select cards to trash for Sentry:", cards)
        to_discard, cards = self._selectCards("Select cards to discard for Sentry:", cards)
        order = self._selectOrder("Select order of cards for Sentry:", cards)
        return to_trash, to_discard, order
    
    def putForHarbinger(self):
        ret = self._selectCards(
            "Select card to put on deck for Harbinger:",
            self.player.discard.cards, 0, 1)[0]
        if len(ret) > 0:
            return ret[0]
    
    def trashForBandit(self, player, candidates):
        return self._selectCards(
            "Select card to trash for Bandit:",
            candidates, 1, 1)[0][0]
    
    def takeForSwindler(self, other, candidates):
        return self._selectCards(
            "Select card to take for Swindler by {}:".format(other.name),
            candidates, 1, 1)[0][0]
    def discardForTorturer(self, other):
        ret = self._selectCards(
            "Select cards to discard for Torturer:",
            self.player.hand.cards, 0, 2)
        if len(ret) >= len(self.player.hand.cards):
            return ret
    def choicesForPawn(self):
        opts = ["card", "action", "buy", "money"]
        ret = []
        while len(ret) < 2 and len(opts) > 0:
            resp = self._selectOption("Select {}/{} option for Pawn:".format(len(ret) + 1, 2), opts)
            ret.append(resp)
            opts.remove(resp)
        return ret
    def giveForMasquerade(self):
        return self._selectCards(
            "Select card to give for Masquerade:",
            self.player.hand.cards, 1, 1)[0][0]
    def trashForMasquerade(self):
        ret = self._selectCards(
            "Select card to trash for Masquerade:",
            self.player.hand.cards, 0, 1)[0]
        if len(ret) > 0:
            return ret[0]
    def putForCourtyard(self):
        return self._selectCards(
            "Select card to put on top of your deck for Courtyard:",
            self.player.hand.cards, 1, 1)[0][0]
    def guessForWishingWell(self):
        if self.player.deck.count() > 0:
            src = self.player.deck
        else:
            src = self.player.discard
        return self._selectCards(
            "Select card to guess for WishingWell:",
            src.cards, 1, 1)[0][0]
    def gainForSaboteur(self, cost):
        candidates = [c for (c, l) in self.game.supply.piles.items()
            if len(l) > 0 and self.game.currentCost(c) <= cost]
        ret = self._selectCards(
            "Select card to gain for Saboteur:",
            candidates, 0, 1)[0]
        if len(ret) > 0:
            return ret[0]
    def revealSecretChamber(self, card):
        return self._selectOption(
            "Attack played: {}; reveal SecretChamber?".format(card),
            ["yes", "no"]) == "yes"
    def putForSecretChamber(self):
        return self._selectCards(
            "Select cards to put for SecretChamber:",
            self.player.hand.cards, 2, 2)[0]
    def orderForScout(self, to_put):
        return self._selectOrder("Select order of cards for Scout:", to_put)
    def choicesForCourtier(self, ntypes):
        opts = ["gold", "money", "action", "buy"]
        ret = []
        while len(ret) < ntypes and len(opts) > 0:
            resp = self._selectOption("Select {}/{} option for Courtier:".format(len(ret) + 1, ntypes), opts)
            ret.append(resp)
            opts.remove(resp)
        return ret
    def chooseForLurker(self, can_trash, can_take):
        ret = self._selectCards("Select card to gain for Lurker:", can_take, 0, 1)[0]
        if len(ret) > 0:
            return None, ret[0]
        return self._selectCards("Select card to trash for Lurker:", can_trash, 1, 1)[0][0]
    def insertForSecretPassage(self, N):
        card = self._selectCards(
            "Select card to insert for SecretPassage:",
            self.player.hand.cards, 1, 1)[0][0]
        index = self._selectOption(
            "Select index of card to be inserted at:",
            [str(i) for i in range(N + 1)])
        return card, int(index)
    def revealDiplomat(self, card):
        return self._selectOption(
            "Attack played: {}; reveal Diplomat?".format(card),
            ["yes", "no"]) == "yes"
    def discardForDiplomat(self):
        return self._selectCards(
            "Select cards to be discarded for Diplomat:",
            self.player.hand.cards, 3, 3)[0][0]
    def orderForPatrol(self, to_put):
        return self._selectOrder("Select order of cards for Patrol:", to_put)


import tkinter as tk
from tkinter.simpledialog import SimpleDialog
import threading
import queue
import os
import os.path
import time


class GUI(CLI):
    IMG_DIR = 'img'
    
    
    class Zone(object):
        def __init__(self, name, root, imgs, closed, opened, cardClicked=None):
            self.name = name
            self.root = root
            self.imgs = imgs
            
            self.closed = closed
            self.opened = opened
            self.cardClicked=cardClicked
            
            self.frame = frame = tk.LabelFrame(root, text=name)
            self.grid = {}
        
        def _events(self, lbl, name, cardClicked):
            setattr(lbl, 'imgs', self.imgs)
            setattr(lbl, 'card_name', name)
            setattr(lbl, 'bigtip', None)
            def enter(event):
                if lbl.card_name.startswith('_'):
                    return
                #lbl.config(image=lbl.imgs[lbl.card_name][0])
                #return
                if lbl.bigtip is not None:
                    return
                x, y, cx, cy = lbl.bbox("insert")
                x = x + lbl.winfo_rootx() + 57
                y = y + cy + lbl.winfo_rooty() +27
                lbl.bigtip = tk.Toplevel(lbl)
                lbl.bigtip.wm_overrideredirect(1)
                lbl.bigtip.wm_geometry("+%d+%d" % (x, y))
                biglbl = tk.Label(lbl.bigtip, image=lbl.imgs[lbl.card_name][0])
                biglbl.pack(ipadx=1)
            def leave(event):
                if lbl.card_name.startswith('_'):
                    return
                #lbl.config(image=lbl.imgs[lbl.card_name][1])
                #return
                if lbl.bigtip is None:
                    return
                lbl.bigtip.destroy()
                lbl.bigtip = None
            if cardClicked is None:
                click = None
            else:
                def click(event):
                    cardClicked(lbl.card_name)
            return enter, leave, click
        
        def cardLabel(self, col, row, name, tiny):
            if (row, col) not in self.grid:
                lbl = tk.Label(self.frame, image=self.imgs[name][int(tiny)])
                lbl.grid(column=col, row=row*2 + 1)
                if tiny or True:
                    enter, leave, click = self._events(lbl, name, self.cardClicked)
                    lbl.bind("<Enter>", enter)
                    lbl.bind("<Leave>", leave)
                if click is not None:
                    lbl.bind("<Button-1>", click)
                lbl_cnt = tk.Label(self.frame, text="")
                lbl_cnt.grid(column=col, row=row*2 + 0)
                self.grid[(row, col)] = (lbl, lbl_cnt)
            lbl, lbl_cnt = self.grid[(row, col)]
            if name != lbl.card_name:
                lbl.card_name = name
                lbl.config(image=self.imgs[name][int(tiny)])
            return (lbl, lbl_cnt)
        
        def setLabelCounts(self, cols, rows):
            to_remove = []
            for (col, row) in self.grid.keys():
                if col >= cols or row >= rows:
                    to_remove.append((col, row))
            for col, row in to_remove:
                lbl, lbl_cnt = self.grid[(col, row)]
                lbl.destroy()
                lbl_cnt.destroy()
                del self.grid[(col, row)]
        
        def updatePiles(self, piles, columns, tiny):
            for i, (card_type, lst) in enumerate(sorted(piles.items(),
                    key=lambda x: str(x[0]()))):
                col = i % columns
                row = i // columns
                lbl, lbl_cnt = self.cardLabel(col, row, card_type.name(), tiny)
                lbl_cnt.config(text="x {}".format(len(lst)))
        
        def updateCards(self, cards, tiny):
            if self.closed:
                col, row = 0, 0
                lbl, lbl_cnt = self.cardLabel(col, row, "_back", tiny)
                lbl_cnt.config(text="x {}".format(len(cards)))
            elif not self.opened:
                col, row = 0, 0
                if len(cards) == 0:
                    name = "_back_mono"
                else:
                    name = cards[-1].name()
                lbl, lbl_cnt = self.cardLabel(col, row, name, tiny)
                lbl_cnt.config(text="x {}".format(len(cards)))
            else:
                self.setLabelCounts(len(cards), 1)
                for col, card in enumerate(cards):
                    lbl, lbl_cnt = self.cardLabel(col, 0, card.name(), tiny)
        
        def update(self, zone, columns=20, tiny=True, force_piles=False):
            if (hasattr(zone, 'cards') or self.closed) and not force_piles:
                self.updateCards(zone.cards, tiny=tiny)
            else:
                self.updatePiles(zone.piles, columns=columns, tiny=tiny)
    
    
    class PlayerArea(object):
        def __init__(self, number, name, root, imgs, is_human, cardClicked=None):
            name = "PLAYER #{} {}".format(number, name)
            if is_human:
                name = "{} (YOU)".format(name)
            
            self.frame = frame = tk.LabelFrame(root, text=name)
            
            self.deck = GUI.Zone("deck", frame, imgs, True, False)
            self.hand = GUI.Zone("hand", frame, imgs, not is_human, is_human,
                (cardClicked if is_human else None))
            self.discard = GUI.Zone("discard", frame, imgs, False, False)
            
            self.deck.frame.pack(expand=1, side=tk.LEFT, fill=tk.BOTH)
            self.hand.frame.pack(expand=1, side=tk.LEFT, fill=tk.BOTH)
            self.discard.frame.pack(expand=1, side=tk.LEFT, fill=tk.BOTH)
        
        def update(self, player, is_active, tiny=True):
            self.deck.update(player.deck, tiny=tiny)
            self.hand.update(player.hand, tiny=tiny)
            self.discard.update(player.discard, tiny=tiny)
            self.frame.config(bg=
                ("green" if is_active else "gray"))
    
    
    class ChoiceDialog(object):
        def __init__(self, root, text, options, cards, piles, imgs, min_count, max_count, choice_q):
            self.min_count = min_count
            self.max_count = max_count
            self.choice_q = choice_q
            
            self.results = []
            self.selected = []
            self.options = options
            self.cards = cards
            self.piles = piles
            
            x, y, cx, cy = root.bbox("insert")
            x = x + root.winfo_rootx()
            y = y + root.winfo_rooty()
            wnd = tk.Toplevel(root)
            #wnd.wm_overrideredirect(1)
            wnd.wm_geometry("+%d+%d" % (x, y))
            
            tk.Label(wnd, text=text).pack(expand=1, fill=tk.BOTH)
            
            if min_count != max_count:
                tk.Button(wnd, text="DONE", command=self.onClick(".")).pack(expand=1, fill=tk.BOTH)
            
            if options is not None and len(options) > 0:
                nopts = len(options)
                btns_frm = tk.LabelFrame(wnd, text="options")
                btns_frm.pack(expand=1, fill=tk.BOTH)
                for i, option in enumerate(options):
                    tk.Button(btns_frm, text=option, command=self.onClick(option)).grid(
                        row=0, column=i)
            
            elif False: #piles is not None and len(piles) > 0:
                piles_frm = tk.LabelFrame(wnd, text="piles")
                piles_frm.pack(expand=1, fill=tk.BOTH)
                for i, (name, cnt) in enumerate(piles.items()):
                    lbl = tk.Label(piles_frm, image=imgs[name][0])
                    lbl.grid(row=0, column=i)
                    lbl.bind("<Button-1>", self.onClick(name))
            
            elif cards is not None and len(cards) > 0:
                cards_frm = tk.LabelFrame(wnd, text="cards")
                cards_frm.pack(expand=1, fill=tk.BOTH)
                for i, card in enumerate(cards):
                    name = card.name()
                    lbl = tk.Label(cards_frm, image=imgs[name][0])
                    lbl.grid(row=0, column=i)
                    lbl.bind("<Button-1>", self.onClick(name, lbl))
            
            self.wnd = wnd
        
        def onClick(self, choice, label=None):
            def ret(*args):
                if label is not None:
                    if label in self.selected:
                        label.config(bg="gray")
                        self.results.remove(choice)
                        self.selected.remove(label)
                        return
                    label.config(bg="green")
                    self.selected.append(label)
                finished = False
                if choice in (".", ".end"):
                    if len(self.results) < self.min_count:
                        return
                    finished = True
                elif self.max_count is None or len(self.results) < self.max_count:
                    self.results.append(choice)
                    finished = (self.min_count == self.max_count and self.min_count == len(self.results))
                if finished:
                    self.choice_q.put(self.results)
                    self.wnd.destroy()
                    self.wnd = None
            return ret
    
    class GameOverDialog(object):
        def __init__(self, root, table, players, imgs, tiny, cmd_q):
            self.cmd_q = cmd_q
            
            x, y, cx, cy = root.bbox("insert")
            x = x + root.winfo_rootx()
            y = y + root.winfo_rooty()
            wnd = tk.Toplevel(root)
            #wnd.wm_overrideredirect(1)
            wnd.wm_geometry("+%d+%d" % (x, y))
            
            tk.Label(wnd, text="Game over! Ranking and deck contents:").pack(expand=1, fill=tk.BOTH)
            tk.Button(wnd, text="DONE", command=self.onDone).pack(expand=1, fill=tk.BOTH)
            
            for nplayer, (scores, turns, cards, rank, winner, name) in sorted(table.items(), key=lambda x: x[1][3]):
                deck = GUI.Zone("{} {} - {} CARD(S), {} SCORE(s), {} TURN(s)".format(
                    rank, name, cards, scores, turns), wnd, imgs, False, False)
                if winner:
                    deck.frame.config(bg="green")
                deck.update(players[nplayer-1].deck, tiny=tiny, force_piles=True)
                deck.frame.pack(expand=1, fill=tk.BOTH)
            
            self.wnd = wnd
        
        def onDone(self, *args):
            self.cmd_q.put("done")
            self.wnd.destroy()
            self.wnd = None
    
    def __init__(self, game, tiny=True, tiny_scale=2):
        CLI.__init__(self, game)
        
        self.tiny = tiny
        self.tiny_scale = tiny_scale
        
        self.commands_q = queue.Queue()
        self.data_q = queue.Queue()
        
        self.gui_thread = threading.Thread(target=self.run)
        self.gui_thread.setDaemon(True)
    
    def setPlayer(self, player):
        CLI.setPlayer(self, player)
        
        self.gui_thread.start()
        if self.commands_q.get() != "ready":
            raise
    
    def run(self):
        self.root = root = tk.Tk()
        
        game = self.game
        player = self.player
        
        nplayers = game.nplayers
        
        self.imgs = {}
        try:
            for fname in os.listdir(self.IMG_DIR):
                path = os.path.join(self.IMG_DIR, fname)
                name, ext = os.path.splitext(fname)
                if ext != ".png" or (game.supply.hasPile(name) == 0 and not fname.startswith('_')):
                    continue
                full = tk.PhotoImage(file=path)
                if int(self.tiny_scale) != self.tiny_scale:
                    tmp = full.zoom(5)
                    tiny = tmp.subsample(int(self.tiny_scale * 5.0))
                else:
                    tiny = full.subsample(self.tiny_scale)
                self.imgs[name] = (full, tiny)
        except Exception:
            traceback.print_exc()
        print("Total card images loaded: {}".format(len(self.imgs)))
        
        root.title("Dominion - GUI")
        root.geometry('960x700')
        
        self.supply = self.Zone("SUPPLY", root, self.imgs, False, False,
            self.supplyCardClicked)
        self.supply.frame.pack(expand=1, fill=tk.BOTH)
        
        zones = tk.LabelFrame(root, text="BOARD")
        zones.pack(expand=1, fill=tk.BOTH)
        
        self.played = self.Zone("PLAYED", zones, self.imgs, False, True)
        self.played.frame.pack(expand=1, side=tk.TOP, fill=tk.BOTH)
        
        self.player_areas = []
        ncol = 0
        for i in range(1, game.nplayers+1):
            is_human = (game.players[i-1] is player)
            if is_human:
                area = self.PlayerArea(i, game.players[i-1].name, root,
                    self.imgs, is_human, self.handCardClicked)
                area.frame.pack(expand=1, fill=tk.BOTH)
            else:
                area = self.PlayerArea(i, game.players[i-1].name, zones,
                    self.imgs, is_human, self.handCardClicked)
                area.frame.pack(expand=1, side=tk.LEFT, fill=tk.BOTH)
                ncol += 1
            self.player_areas.append(area)
        
        self.trash = self.Zone("TRASH", zones, self.imgs, False, False)
        self.trash.frame.pack(expand=1, side=tk.LEFT, fill=tk.BOTH)
        
        control = tk.LabelFrame(root, text="CONTROL")
        control.pack(expand=1, fill=tk.BOTH)
        
        self.info = tk.Label(control, text="")
        self.info.pack(expand=1, fill=tk.BOTH)
        
        done_button = tk.Button(control, text="DONE", command=self.cmdDone)
        done_button.pack(expand=1, fill=tk.BOTH)
        
        root.bind("<KeyPress>", self.keyPressHandler)
        root.bind("<KeyRelease>", self.keyReleaseHandler)
        
        root.bind("<<update_state>>", self.updateState)
        
        root.bind("<<select_option>>", self.onSelectOption)
        root.bind("<<select_order>>", self.onSelectOrder)
        root.bind("<<select_cards>>", self.onSelectCards)
        root.bind("<<game_over>>", self.showGameOverDialog)
        
        self.targets = []
        self.ctrl_pressed = False
        
        self.commands_q.put("ready")
        root.mainloop()
    
    def updateState(self, evt):
        active_player, phase = self.game.activeTurn()
        self.supply.update(self.game.supply, tiny=self.tiny)
        self.played.update(active_player.played, tiny=self.tiny)
        self.trash.update(self.game.trash, tiny=self.tiny)
        for i, player in enumerate(self.game.players):
            self.player_areas[i].update(player, player is active_player, tiny=self.tiny)
        self.info.config(text="({}) ${}; buys: {}; actions: {}".format(
            phase, self.player.money, self.player.buys, self.player.actions))
    
    def keyPressHandler(self, evt):
        ch, sym, code = evt.char, evt.keysym, evt.keycode
        if sym.startswith('Control') and not self.ctrl_pressed:
            self.targets = []
            self.ctrl_pressed = True
        if ch == ' ':
            self.commands_q.put(" ")
    
    def keyReleaseHandler(self, evt):
        ch, sym, code = evt.char, evt.keysym, evt.keycode
        if sym.startswith('Control') and self.ctrl_pressed:
            if len(self.targets) > 0:
                self.commands_q.put(" ".join(self.targets))
                self.targets = []
            self.ctrl_pressed = False
    
    def cmdDone(self):
        self.commands_q.put(".end")
    
    def handCardClicked(self, card):
        if self.game.activePlayer() is not self.player:
            return
        if self.ctrl_pressed:
            self.targets.append(card)
        else:
            self.commands_q.put(card)
    
    def supplyCardClicked(self, card):
        if self.game.activePlayer() is not self.player:
            return
        if self.ctrl_pressed:
            self.targets.append(card)
        else:
            self.commands_q.put(card)
    
    def _inputCommand(self, prompt):
        cmd = self.commands_q.get()
        print(cmd)
        return cmd
    
    def _selectOption(self, prompt, options, default=None):
        print(prompt)
        if len(options) == 0:
            return
        if len(options) == 1:
            return options[0]
        if default is None:
            default = options[0]
        loptions = dict([(o.lower(), o) for o in options])
        self.data_q.put((prompt, options, default))
        self.root.event_generate("<<select_option>>")
        return loptions[self.commands_q.get()[0].lower()]
    
    def _selectOrder(self, prompt, cards):
        print(prompt)
        names = [card.name() for card in cards]
        if len(set(names)) <= 1:
            return range(len(names))
        self.data_q.put((prompt, cards))
        self.root.event_generate("<<select_order>>")
        ordered = self.commands_q.get()
        order = []
        names_dup = names[:]
        for n in ordered:
            if n in names_dup:
                i = names_dup.index(n)
                order.append(i)
                names_dup[i] = None
        return order
    
    def _selectCards(self, prompt, candidates, min_count=0, max_count=None):
        print(prompt)
        if len(candidates) < min_count:
            min_count = len(candidates)
        all_cards = {}
        for card in candidates:
            if hasattr(card, 'name'):
                name = card.name().lower()
            else:
                name = card
            if name not in all_cards:
                all_cards[name] = []
            all_cards[name].append(card)
        names = ["{}{}".format(name, 
            "" if len(l) == 1 else "(x{})".format(len(l)))
            for name, l in all_cards.items()]
        if len(names) == min_count and len(names) == max_count:
            return candidates[:min_count], candidates[-min_count:]
        self.data_q.put((prompt, candidates, all_cards, min_count, max_count))
        self.root.event_generate("<<select_cards>>")
        results = self.commands_q.get()
        selected = []
        for name in results:
            l = all_cards.get(name.lower(), [])
            if len(l) > 0:
                selected.append(l.pop())
        if max_count is not None:
            selected = selected[:max_count]
        unselected = [card for card in candidates if card not in selected]
        return selected, unselected
    
    def onSelectOption(self, evt):
        prompt, options, default = self.data_q.get()
        dlg = self.ChoiceDialog(self.root, prompt, options, [], [], self.imgs, 1, 1, self.commands_q)
    
    def onSelectOrder(self, evt):
        prompt, cards = self.data_q.get()
        N = len(cards)
        dlg = self.ChoiceDialog(self.root, prompt, [], cards, [], self.imgs, N, N, self.commands_q)
    
    def onSelectCards(self, evt):
        prompt, cards, piles, min_count, max_count = self.data_q.get()
        if len(cards) < 10:
            dlg = self.ChoiceDialog(self.root, prompt, [], cards, [], self.imgs, min_count, max_count, self.commands_q)
        else:
            dlg = self.ChoiceDialog(self.root, prompt, [], cards, piles, self.imgs, min_count, max_count, self.commands_q)
    
    def showGameOverDialog(self, evt):
        table, players = self.data_q.get()
        dlg = self.GameOverDialog(self.root, table, players, self.imgs, self.tiny, self.commands_q)
    
    def doPhase(self, phase):
        self.root.event_generate("<<update_state>>")
        CLI.doPhase(self, phase)
        self.root.event_generate("<<update_state>>")
    
    def onBuy(self, player, card):
        CLI.onBuy(self, player, card)
        self.root.event_generate("<<update_state>>")
    
    def onPlay(self, player, card, targets):
        CLI.onPlay(self, player, card, targets)
        self.root.event_generate("<<update_state>>")
        
    def onNewActivePlayer(self, player):
        CLI.onNewActivePlayer(self, player)
        self.root.event_generate("<<update_state>>")
    
    def onGameOver(self, table):
        CLI.onGameOver(self, table)
        self.root.event_generate("<<update_state>>")
        self.data_q.put((table, self.game.players))
        self.root.event_generate("<<game_over>>")
        self.commands_q.get()
