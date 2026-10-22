class RColor:
    def __init__(self, v): self.v = v
    @staticmethod
    def from_mc_value(v): return v

class RStyle:
    bold = 'bold'; italic = 'italic'; underlined = 'underlined'
    strikethrough = 'strikethrough'; obfuscated = 'obfuscated'

class RText:
    def __init__(self, text='', color=None, styles=None):
        self.text = text; self.color = color; self.styles = styles or []
    def __str__(self): return self.text

class RTextList(list):
    def append(self, x):
        super().append(x); return self
    def __str__(self): return ''.join(str(x) for x in self)
