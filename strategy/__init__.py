import pkgutil
import inspect

import random

import core.rules


class RandomStrategy(object):
    def __init__(self, modname, candidates):
        self.candidates = candidates
        setattr(self, '__name__', '{}.Random'.format(modname))
    def __call__(self, *args, **kwargs):
        i = random.randrange(0, len(self.candidates))
        name, cls = self.candidates[i]
        return cls(*args, **kwargs)


strategies = {}

for importer, name, ispkg in pkgutil.iter_modules(__path__):
    loader = importer.find_module(name)
    module = loader.load_module(name)
    mod_strategies = []
    for varname in dir(module):
        cls = getattr(module, varname)
        
        if inspect.isclass(cls):
            strategy_name = "{}.{}".format(name, varname)
            cls = getattr(module, varname)
            if all([hasattr(cls, phase) for phase in core.rules.TURN_PHASES]):
                strategies[strategy_name] = cls
                mod_strategies.append((strategy_name, cls))
    
    if len(mod_strategies) > 0:
        strategy_name = "{}.{}".format(name, "Random")
        strategies[strategy_name] = RandomStrategy(name, mod_strategies)
