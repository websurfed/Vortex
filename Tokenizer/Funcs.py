from .Keywords import KEYWORDS
from .Types import Type, Token

def lock_identifier(source: str, cursor: int) -> bool:
    char = source[cursor]
    if char.isalpha() or char == '_':
        return True
    return False

def match_identifier(source: str, cursor: int, line: int, col: int) -> tuple[Token, int]:
    offset = 1
    while cursor + offset < len(source) and (source[cursor + offset].isalnum() or source[cursor + offset] == '_'):
        offset += 1
    val = source[cursor:cursor + offset]

    token_type = KEYWORDS.get(val, Type.IDENTIFIER)
    token_val = None if token_type in KEYWORDS.values() else val

    return Token(token_type, token_val, line, col), offset

def lock_numeric(source: str, cursor: int) -> bool:
    char = source[cursor]
    if char.isdigit():
        return True
    return False

def match_numeric(source: str, cursor: int) -> tuple[str, int]:
    offset = 1
    while cursor + offset < len(source) and source[cursor + offset].isdigit():
        offset += 1
    val = source[cursor:cursor + offset]
    return val, offset