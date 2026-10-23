from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, NamedTuple, Protocol

class Rule(Enum):
    STATIC = auto()
    DYNAMIC = auto()
    COMPLEX = auto()

@dataclass
class Token:
    type: str
    value: str | None
    line: int
    col: int


TOKEN_RULES = [
    (Rule.STATIC, "EQUALS", "=="),
    (Rule.STATIC, "EQUALS", "="),
    (Rule.STATIC, "EQUALS", "===")
]

def Lex(source: str) -> list[Token]:
    cursor = 0
    length = len(source)

    tokens = []
    line = 1
    col = 1

    token_type: str
    token_val = None
    token_line = line
    token_col = col

    while cursor < length:
        char = source[cursor]
        cursor_shift = 1

        if char == "\n":
            token_col = col
            token_line = line

            tokens.append(Token("NEWLINE", None, token_line, token_col))

            col = 0
            line += 1
            print("NEW LINE")

        elif char.isalpha():
            print("IDENTIFIER")
            token_type = "IDENTIFIER"
            token_line = line
            token_col = col

            init_cursor = cursor
            cursor_shift = 0
            while cursor < length and source[cursor].isalnum():
                cursor += 1

            col += cursor - init_cursor
            token_val = source[init_cursor:cursor]
            tokens.append(Token(token_type, token_val, token_line, token_col))

        elif char.isdigit():
            print("NUMERIC")
            token_type = "NUMERIC"
            token_line = line
            token_col = col

            init_cursor = cursor
            cursor_shift = 0
            while cursor < length and source[cursor].isdigit():
                cursor += 1

            col += cursor - init_cursor
            token_val = source[init_cursor:cursor]
            tokens.append(Token(token_type, token_val, token_line, token_col))

        elif char == '=':
            print("EQUALS")
            tokens.append(Token("EQUALS", None, line, col))

        col += cursor_shift
        cursor += cursor_shift

    tokens.append(Token("EOF", None, line, col))
    return tokens