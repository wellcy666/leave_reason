class Literal:
    def __init__(self, name): self.name = name; self.children = {}; self.func = None
    def runs(self, func): self.func = func; return self
    def then(self, node): self.children[node.name] = node; return self

class Info:
    def __init__(self, raw): self.raw_content = raw; self.content = raw

class CommandSource:
    def __init__(self, level=4): self.level = level; self.msgs = []
    def has_permission(self, lvl): return self.level >= lvl
    def reply(self, msg): self.msgs.append(str(msg))

class PluginServerInterface: pass
