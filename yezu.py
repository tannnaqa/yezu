import enum
import sys

def readfile(path):
    try:
        with open(path, "r", encoding="utf8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"ERROR: file {path!r} not found", file=sys.stderr)
        exit()

class Position:
    __slots__ = "path", "line", "row"
    
    def __init__(self, path, line, row):
        self.path = path
        self.line = line
        self.row = row
    
    def __repr__(self):
        return f"{self.path}:{self.line}:{self.row}"

class Scanner:
    def __init__(self, path):
        self.path = path
        self.string = readfile(self.path)
        self.index = 0
        self.line = 1
        self.row = 0
    
    def __iter__(self):
        return self
    
    @property
    def position(self):
        return Position(self.path, self.line, self.row)
    
    def increment(self):
        self.index += 1
        if self.index < len(self.string):
            if self.string[self.index] == "\n":
                self.line += 1
                self.row = -1
            else:
                self.row += 1
    
    def skip(self, cond):
        while self.index < len(self.string) and cond(self.string[self.index]):
            self.increment()
    
    def until(self, stop):
        while self.index < len(self.string) and self.string[self.index] != stop:
            self.increment()
    
    def __next__(self):
        self.skip(str.isspace)
        if self.index >= len(self.string):
            raise StopIteration()
        elif self.string[self.index] == ";":
            start = self.index
            pos = self.position
            self.until("\n")
            return pos, self.string[start:self.index]
        else:
            start = self.index
            pos = self.position
            self.skip(lambda c: not c.isspace() and c not in ";\"\'")
            while self.index < len(self.string) and not self.string[self.index].isspace():
                if self.string[self.index] in "\"\'":
                    stop = self.string[self.index]
                    self.increment()
                    self.until(stop)
                    self.increment()
                    self.skip(lambda c: not c.isspace() and c not in ";\"\'")
                else:
                    break
            return pos, self.string[start:self.index]

class Kind:
    def __str__(self):
        return self.name
    
    ILLEGAL = enum.auto()
    COMMENT = enum.auto()
    WORD = enum.auto()
    
    INTEGER = enum.auto()
    FLOAT = enum.auto()
    BOOLEAN = enum.auto()
    STRING = enum.auto()
    CHARACTER = enum.auto()
    
    FUN = enum.auto()
    END = enum.auto()
    IF = enum.auto()
    THEN = enum.auto()
    ELSE = enum.auto()
    WHILE = enum.auto()
    DO = enum.auto()
    

class Token:
    __slots__ = "pos", "kind", "value"
    
    def __init__(self, pos, kind, value):
        self.pos = pos
        self.kind = kind
        self.value = value
    
    def __repr__(self):
        return f"Token({self.pos}, {self.kind}, {self.value})"

def main():
    print("[yezu]")
    
    if len(sys.argv) != 2:
        print(f"USAGE: {sys.argv[0]} <file>", file=sys.stderr)
        exit()
    else:
        path = sys.argv[1]
        for word in Scanner(path):
            print(word)


if __name__ == "__main__":
    main()

