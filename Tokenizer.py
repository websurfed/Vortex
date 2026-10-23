from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable


class Rule(Enum):
    STATIC = auto() # basic, maximal munch on a string
    DYNAMIC = auto() # pass a lock and then figure out what else belongs to the token
    VARIABLE = auto() # same as dynamic but it emits the token itself
    COMPLEX = auto() # same as variable but it also handles line and col

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

@dataclass
class Token:
    type: Type
    value: str | None
    line: int
    col: int

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

TOKEN_RULES = [
    (Rule.STATIC, Type.EQUALS, "="),
    (Rule.STATIC, Type.COLON, ":"),
    (Rule.STATIC, Type.LPAREN, "("),
    (Rule.STATIC, Type.RPAREN, ")"),
    (Rule.STATIC, Type.ARROW, "->"),
    (Rule.STATIC, Type.COMMA, ","),
    (Rule.STATIC, Type.PLUS, "+"),
    (Rule.STATIC, Type.SUB, "-"),
    (Rule.STATIC, Type.STAR, "*"),
    (Rule.STATIC, Type.SLASH, "/"),
    (Rule.VARIABLE, lock_identifier, match_identifier),
    (Rule.DYNAMIC, Type.NUMERIC, lock_numeric, match_numeric)
]

KEYWORDS = {
    "def": Type.DEF,
    "return": Type.RETURN
}

def _compile_dynamic_rules():
    cherry_rules = []
    for rule, ruleType, *rest in TOKEN_RULES:
        if rule != Rule.DYNAMIC:
            continue
        rule_lock = rest[0]
        rule_match = rest[1]
        cherry_rules.append((rule, ruleType, rule_lock, rule_match))
    return cherry_rules

def _compile_variable_rules():
    cherry_rules = []
    for rule, *rest in TOKEN_RULES:
        if rule != Rule.VARIABLE:
            continue
        rule_lock = rest[0]
        rule_match = rest[1]
        cherry_rules.append((rule, rule_lock, rule_match))
    return cherry_rules

def _compile_static_rules():
    cherry_rules = []
    for rule, ruleType, *rest in TOKEN_RULES:
        if rule != Rule.STATIC:
            continue
        rule_literal = rest[0]
        cherry_rules.append((rule, ruleType, rule_literal))

    compiled_rules = []
    cherry_length = len(cherry_rules)
    while len(compiled_rules) < cherry_length:
        rule: Rule
        rule_type: Type
        rule_literal: str
        longest_literal = -1
        largest_index: int = -1

        index = 0
        for r1, r2, r3 in cherry_rules:
            if len(r3) > longest_literal:
                longest_literal = len(r3)
                rule = r1
                rule_type = r2
                rule_literal = r3
                largest_index = index

            index += 1

        del cherry_rules[largest_index]

        compiled_rules.append((rule, rule_type, rule_literal))

    return compiled_rules

def _try_static_rules(source: str, cursor: int, compiled_static_rules):
    char = source[cursor]

    largest_offset = -1
    largest_rule: tuple[Rule, Type, str] | None = None

    for rule, ruleType, ruleLiteral in compiled_static_rules:
        if rule != Rule.STATIC:
            continue

        m_offset = 0
        if ruleLiteral[m_offset] == char:
            while m_offset + cursor < len(source) and m_offset < len(ruleLiteral) and source[m_offset + cursor] == ruleLiteral[m_offset]:
                m_offset += 1

            if m_offset > largest_offset and m_offset == len(ruleLiteral):
                largest_offset = m_offset
                largest_rule = (rule, ruleType, ruleLiteral)

    if largest_rule is not None:
        return largest_rule, largest_offset

    return None

def _try_dynamic_rules(source: str, cursor: int, compiled_dynamic_rules):
    for rule, ruleType, ruleLock, ruleMatch in compiled_dynamic_rules:
        if rule != Rule.DYNAMIC:
            continue

        if ruleLock(source, cursor):
            return *ruleMatch(source, cursor), ruleType

    return None

def _try_variable_rules(source: str, cursor: int, line: int, col: int, compiled_variable_rules):
    for rule, ruleLock, ruleMatch in compiled_variable_rules:
        if rule != Rule.VARIABLE:
            continue

        if ruleLock(source, cursor):
            return ruleMatch(source, cursor, line, col)

    return None

def _convert_rule_to_token(rule_data, line: int, col: int) -> Token:
    match rule_data:
        case(Rule.STATIC, token_type, literal):
            return Token(token_type, None, line, col)
        case _:
            raise ValueError(f"Unknown rule pattern: {rule_data}")

def lex(source: str) -> list[Token]:
    # compile lists
    compiled_static_rules = _compile_static_rules()
    compiled_dynamic_rules = _compile_dynamic_rules()
    compiled_variable_rules = _compile_variable_rules()

    cursor: int = 0
    length: int = len(source)

    tokens = []
    line = 1
    col = 1

    while cursor < len(source):
        if source[cursor] == '\n':
            tokens.append(Token(Type.NEWLINE, None, line, col))

            cursor += 1
            line += 1
            col = 1

            continue

        static_rule_attempt = _try_static_rules(source, cursor, compiled_static_rules)
        dynamic_rule_attempt = _try_dynamic_rules(source, cursor, compiled_dynamic_rules)
        variable_rule_attempt = _try_variable_rules(source, cursor, line, col, compiled_variable_rules)

        if static_rule_attempt is not None:
            rule_data, offset = static_rule_attempt

            token = _convert_rule_to_token(rule_data, line, col)
            tokens.append(token)

            cursor += offset
            col += offset

        elif dynamic_rule_attempt is not None:
            rule_val, offset, rule_type = dynamic_rule_attempt

            token = Token(rule_type, rule_val, line, col)
            tokens.append(token)

            cursor += offset
            col += offset

        elif variable_rule_attempt is not None:
            token, offset = variable_rule_attempt
            tokens.append(token)

            cursor += offset
            col += offset

        else:
            if source[cursor] == ' ':
                cursor += 1
                col += 1
            else:
                raise SyntaxError(
                    f"Unexpected character {source[cursor]!r} at line {line}, col {col}"
                )

    tokens.append(Token(Type.EOF, None, line, col))
    return tokens