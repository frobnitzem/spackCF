import re

# regexp to shorten&replace current output directory
exp = re.compile(r"/\S+/spackCF/spack")

class Line(str):
    def startswith(self, x):
        n = len(self)
        m = len(x)
        if n >= m and self[:m] == x:
            return self[m:].strip()
        return None

class Text:
    def __init__(self, s):
        self.s = s
    def __iter__(self):
        #for line in self.s.split('\n'):
        for line in self.s:
            yield Line(exp.sub('', line))
