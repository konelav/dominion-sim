Dominion board game simulator
=============================


The main purpose of this project is to create framework for developing
and testing different strategies for Dominion board game.

Main parts of framework are:

  - game engine (`core.rules`, `core.engine`) for maintaining game state,
    turns, phases of turn, card piles and so on;
  - cards and their properties and behaviour (`core.cards`);
  - sample strategies (`strategy.demo` - several simple strategies for
    Base card set, `strategy.human` - CLI and GUI (tk-based) for
    playing game by hand against other strategies);
  - scripts for running single game (`dominion-play`) or series of
    matches (`dominion-tournament`).


Implementing custom strategy
----------------------------

1. Create module for your custom strategy or set of strategies, e.g.
  `strategy/custom.py`. You can use `strategy/demo.py` as a template
  with useful stubs.

2. Each class in this module is considered to be *strategy* if it
  implements methods for all turn phases: `action()`, `buy()`, `cleanup()`.

3. Each strategy must has contructor with single parameter in which
  game engine will be passed: `def __iniy__(self, game):`.

4. Each strategy must has method `setPlayer` which will be called
  by engine passing in argument a `player` that uses this strategy:
  `def setPlayer(self, player):`.

5. Each strategy must has set of callbacks that will be called in
  certaing moments of game flow:

```
    def onBuy(self, player, card_type):
        pass
    def onPlay(self, player, card, targets):
        pass
    def onNewActivePlayer(self, player):
        pass
    def onGameOver(self, score_table):
        pass
```

There is theretically unlimited number of callbacks that will be
called by specific card mechanics. You should implement all callbacks
that are used by all cards involved in games you are planning
to simulate. E.g. if you will use **Militia**, then you should implement
`discardForMilitia(self, count)` callback that will return `count`
cards from hand of strategy's player that will be discarded.
You can see what callbacks needed by different cards simply by looking
in that card's source code in `core.cards`, it should be pretty
self-discribing. Stubs for all callbacks for currently implemented card
sets can be found in `strategy/demo.py`, class `Basic`. When in doubt
what is exact meaning of callback arguments and return value, again,
see it's usage in `core.cards`.


Card sets currently implemented
-------------------------------

  - Base (1st and 2nd edition);
  - Intrigue (1st and 2nd edition).


Strategies included
-------------------

Simple demonstations:

  - `demo.BigMoney`: simply buy silver, gold, provinces, and (at low
    provinces) duchies/estates;
  - `demo.Discarder`: additionally try to discard copper/curse with
    chapel;
  - `demo.Attacker`: extensive use of Attacks if available;
  - `demo.Gardener`: if gardens are available, tries to buy as much
    cards and gardens as possible using workshops, wooductters,
    markets, and villages.

Simple human interfaces:

  - `human.CLI`: playing in console, type `.help` or `?` to see available
    commands;
  - `human.GUI`: playing simple Tk-based GUI; it needs images of cards
    to be placed in `img` folder, this can be done by script
    `dominion-load-imgs`.


Setting up Kingdom
------------------

Both scripts accepts argument `-k`, `--kingdom` in which you can
specify kingdom cards in supply. If there are more cards specified
than `core.rules.SUPPLY_PILES` then engine will randomly select
needed amount of cards at start of each game. Otherwise,
all specified cards will be selected plus random cards from given
set(s) by argument `--set`.


Example output
--------------

```
$ ./dominion-tournament -s demo.BigMoney demo.Attacker demo.Gardener demo.Discarder --set base1e -k witch gardens chapel
Playing game 1 / 1000...
Playing game 101 / 1000...
Playing game 201 / 1000...
Playing game 301 / 1000...
Playing game 401 / 1000...
Playing game 501 / 1000...
Playing game 601 / 1000...
Playing game 701 / 1000...
Playing game 801 / 1000...
Playing game 901 / 1000...
RANK	STRATEGY        	WINS	SCORES	CARDS	RANK
1	demo.Gardener #1	616	40.93	47.463	1.637
2	demo.Attacker #1	341	37.635	31.407	1.892
3	demo.Discarder #1	43	28.319	22.696	3.19
4	demo.BigMoney #1	33	27.453	36.896	3.281
```
