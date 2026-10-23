from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable


class Rule(Enum):
    STATIC = auto()
    DYNAMIC = auto()

class Type(Enum):
    IDENTIFIER = auto()
    NUMERIC = auto()
    EQUALS = auto()
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

def match_identifier(source: str, cursor: int) -> tuple[str, int]:
    offset = 1
    while cursor + offset < len(source) and (source[cursor + offset].isalnum() or source[cursor + offset] == '_'):
        offset += 1
    val = source[cursor:cursor+offset]
    return val, offset

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
    (Rule.DYNAMIC, Type.IDENTIFIER, lock_identifier, match_identifier),
    (Rule.DYNAMIC, Type.NUMERIC, lock_numeric, match_numeric)
]

def _compile_dynamic_rules():
    cherry_rules = []
    for rule, ruleType, *rest in TOKEN_RULES:
        if rule != Rule.DYNAMIC:
            continue
        rule_lock = rest[0]
        rule_match = rest[1]
        cherry_rules.append((rule, ruleType, rule_lock, rule_match))
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

def _convert_rule_to_token(rule_data, line: int, col: int) -> Token:
    match rule_data:
        case(Rule.STATIC, token_type, literal):
            return Token(token_type, None, line, col)
        case _:
            raise ValueError(f"Unknown rule pattern: {rule_data}")

def lex(source: str) -> list[Token]:
    # normalize
    source = source.replace("\r\n", "\n")

    # compile lists
    compiled_static_rules = _compile_static_rules()
    compiled_dynamic_rules = _compile_dynamic_rules()

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

        else:
            cursor += 1
            col += 1

    tokens.append(Token(Type.EOF, None, line, col))
    return tokens