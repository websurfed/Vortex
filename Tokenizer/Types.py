from enum import Enum, auto
from dataclasses import dataclass

@dataclass
class Token:
    type: Type
    value: str | None
    line: int
    col: int

class Rule(Enum):
    STATIC = auto()
    DYNAMIC = auto()
    VARIABLE = auto()
    COMPLEX = auto()

class Type(Enum):
    IDENTIFIER = auto()
    NUMERIC = auto()
    LPAREN = auto()
    RPAREN = auto()
    COLON = auto()
    COMMA = auto()
    ARROW = auto()
    DEF = auto()
    EQUALS = auto()
    PLUS = auto()
    SUB = auto()
    STAR = auto()
    SLASH = auto()
    RETURN = auto()
    EOF = auto()
    NEWLINE = auto()
    COMMENT = auto()