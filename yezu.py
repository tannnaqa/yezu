import enum
import re
import sys

def report(message):
    print(message, file=sys.stderr)
    exit()

def readfile(path):
    try:
        with open(path, "r", encoding="utf8") as file:
            return file.read()
    except FileNotFoundError:
        report(f"ERROR: file {path!r} not found")

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
    def __repr__(self):
        return self.name
    
    def __str__(self):
        return self.name
    
    def filter(self, iterable):
        return filter(lambda token: token.kind == self, iterable)
    
    def exclude(self, iterable):
        return filter(lambda token: token.kind != self, iterable)
    
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
    ELIF = enum.auto()
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
    
    def __iter__(self):
        return iter((self.pos, self.kind, self.value))

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
    
    def list(self):
        return list(self)

VALUE_KINDS = {
    Kind.INTEGER,
    Kind.FLOAT,
    Kind.BOOLEAN,
    Kind.STRING,
    Kind.CHARACTER,
}

class Program:
    __slots__ = "functions", "body"
    
    def __init__(self, functions, body):
        self.functions = functions
        self.body = body
    
    def __repr__(self):
        return f"Program({len(self.functions)} functions)"
    

class Function:
    __slots__ = "pos", "name", "body"
    
    def __init__(self, pos, name, body):
        self.pos = pos
        self.name = name
        self.body = body
    
    def __repr__(self):
        return f"Function({self.name} @{self.pos})"

class If:
    __slots__ = "pos", "cases"
    
    def __init__(self, pos, cases):
        self.pos = pos
        self.cases = cases
    
    def __repr__(self):
        return f"If(@{self.pos})"

class While:
    __slots__ = "pos", "cond", "body"
    
    def __init__(self, pos, cond, body):
        self.pos = pos
        self.cond = cond
        self.body = body
    
    def __repr__(self):
        return f"While(@{self.pos})"

class Parser:
    def __init__(self, tokens):
        self.tokens = iter(tokens)
        self.current = None
        self.next_token()
    
    def next_token(self):
        try:
            self.current = next(self.tokens)
        except StopIteration:
            self.current = None
        else:
            return self.current
    
    def current_and_update(self):
        temp = self.current
        self.next_token()
        return temp
    
    def match(self, *kinds):
        return self.current is not None and self.current.kind in kinds
    
    def expect(self, *kinds):
        if self.current is None:
            report(f"ERROR: expected {kinds} but found nothing")
        elif self.current.kind not in kinds:
            report(f"ERROR: expected {kinds} but found {self.current.kind} at {self.current.pos}")
        else:
            return self.current_and_update()
    
    def collect(self, *stops):
        collected = []
        while self.current is not None and self.current.kind not in stops:
            collected.append(self.parse_atom())
        return collected
    
    def __iter__(self):
        return self
    
    @property
    def program(self):
        prog = Program([], [])
        for atom in self:
            if isinstance(atom, Function):
                prog.functions.append(atom)
            else:
                prog.body.append(atom)
        return prog
    
    def __next__(self):
        if self.current is None:
            raise StopIteration()
        elif self.current.kind == Kind.FUN:
            return self.parse_function()
        else:
            return self.parse_atom()
    
    def parse_function(self):
        pos, _, _ = self.expect(Kind.FUN)
        _, _, name = self.expect(Kind.WORD)
        body = self.collect(Kind.END)
        self.expect(Kind.END)
        return Function(pos, name, body)
    
    def parse_atom(self):
        if self.current.kind in VALUE_KINDS:
            return self.current_and_update()
        elif self.current.kind == Kind.WORD:
            return self.current_and_update()
        elif self.current.kind == Kind.IF:
            return self.parse_if()
        elif self.current.kind == Kind.WHILE:
            return self.parse_while()
        else:
            report(f"ERROR: unexpected {self.current.kind} token at {self.current.pos}")
    
    def parse_if(self):
        cases = []
        pos, _, _ = self.expect(Kind.IF)
        cond = self.collect(Kind.THEN)
        self.expect(Kind.THEN)
        body = self.collect(Kind.ELIF, Kind.ELSE, Kind.END)
        cases.append((cond, body))
        while self.match(Kind.ELIF):
            self.expect(Kind.ELIF)
            cond = self.collect(Kind.THEN)
            self.expect(Kind.THEN)
            body = self.collect(Kind.ELIF, Kind.ELSE)
            cases.append((cond, body))
        if self.match(Kind.ELSE):
            self.expect(Kind.ELSE)
            body = self.collect(Kind.END)
            cases.append((None, body))
        self.expect(Kind.END)
        return If(pos, cases)
    
    def parse_while(self):
        pos, _, _ = self.expect(Kind.WHILE)
        cond = self.collect(Kind.DO)
        self.expect(Kind.DO)
        body = self.collect(Kind.END)
        self.expect(Kind.END)
        return While(pos, cond, body)

def main():
    print("[yezu]")
    
    if len(sys.argv) != 2:
        report(f"USAGE: {sys.argv[0]} <file>")
    else:
        path = sys.argv[1]
        tokens = Lexer(path).list()
        
        illegals = list(Kind.ILLEGAL.filter(tokens))
        if illegals:
            report(f"ERROR: illegal word(s):\n" + "\n".join(
                f"    {token.value!r} at {token.pos}" for token in illegals))
        
        program = Parser(Kind.COMMENT.exclude(tokens)).program
        
        print(program)

if __name__ == "__main__":
    main()

