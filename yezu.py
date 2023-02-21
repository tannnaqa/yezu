import enum
import re
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

class Kind(enum.Enum):
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

STRING_TO_KIND = {
    "fun": Kind.FUN,
    "end": Kind.END,
    "if": Kind.IF,
    "then": Kind.THEN,
    "else": Kind.ELSE,
    "while": Kind.WHILE,
    "do": Kind.DO,
}

class Token:
    __slots__ = "pos", "kind", "value"
    
    def __init__(self, pos, kind, value):
        self.pos = pos
        self.kind = kind
        self.value = value
    
    def __repr__(self):
        return f"Token({self.pos}, {self.kind}, {self.value!r})"

REGEX_INTEGER = re.compile(r"^-?\d+$")
REGEX_FLOAT = re.compile(r"^-?\d+\.\d+$")
REGEX_STRING = re.compile(r"^\"[^\"]*\"$")
REGEX_CHARACTER = re.compile(r"^\'[^\']\'$")
REGEX_WORD = re.compile(r"^[^\"\']+$")

def tokenize(pos, string):
    if REGEX_INTEGER.match(string):
        return Token(pos, Kind.INTEGER, int(string, base=10))
    elif REGEX_FLOAT.match(string):
        return Token(pos, Kind.FLOAT, float(string))
    elif string in ["true", "false"]:
        return Token(pos, Kind.BOOLEAN, string == "true")
    elif REGEX_STRING.match(string):
        return Token(pos, Kind.STRING, string[1:-1])
    elif REGEX_CHARACTER.match(string):
        return Token(pos, Kind.CHARACTER, string[1:-1])
    elif string in STRING_TO_KIND:
        return Token(pos, STRING_TO_KIND[string], None)
    elif string.startswith(";"):
        return Token(pos, Kind.COMMENT, string[1:])
    elif REGEX_WORD.match(string):
        return Token(pos, Kind.WORD, string)
    else:
        return Token(pos, Kind.ILLEGAL, string)

class Lexer:
    def __init__(self, path):
        self.scanner = Scanner(path)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        return tokenize(*next(self.scanner))

def main():
    print("[yezu]")
    
    if len(sys.argv) != 2:
        print(f"USAGE: {sys.argv[0]} <file>", file=sys.stderr)
        exit()
    else:
        path = sys.argv[1]
        for token in Lexer(path):
            print(token)


if __name__ == "__main__":
    main()

