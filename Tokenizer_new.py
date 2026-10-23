from dataclasses import dataclass
from enum import Enum, auto, nonmember
from typing import Callable, NamedTuple, Protocol

class Rule(Enum):
    STATIC = auto()
    DYNAMIC = auto()
    COMPLEX = auto()

class Type(Enum):
    EQUALS = auto()

@dataclass
class Token:
    type: Type
    value: str | None
    line: int
    col: int


TOKEN_RULES = [
    (Rule.STATIC, "EQUALS", "=="),
    (Rule.STATIC, "EQUALS", "="),
    (Rule.STATIC, "EQUALS", "===")
]

def _compile_static_rules():
    cherry_rules = []
    for rule, ruleType, ruleLiteral in TOKEN_RULES:
        if rule != Rule.STATIC:
            continue
        cherry_rules.append((rule, ruleType, ruleLiteral))

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

def _try_static_rules(source: str, cursor: int, sorted_static_rules):
    char = source[cursor]

    largest_offset = 0
    largest_rule: tuple[Rule, Type, str] | None = None

    for rule, ruleType, ruleLiteral in sorted_static_rules:
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

def _convert_rule_to_token(rule_data: tuple[Rule, Type, str], line: int, col: int) -> Token:
    match rule_data:
        case(Rule.STATIC, token_type, literal):
            return Token(token_type, None, line, col)
        case _:
            raise ValueError(f"Unknown rule pattern: {rule_data}")

def Lex(source: str) -> list[Token]:
    compiled_static_rules = _compile_static_rules()

    cursor: int = 0
    length: int = len(source)

    tokens = []
    line = 1
    col = 1

    # print(compiled_static_rules)

    while cursor < len(source):
        static_rule_attempt = _try_static_rules(source, cursor, compiled_static_rules)
        if static_rule_attempt is not None:
            rule_data, offset = static_rule_attempt

            token = _convert_rule_to_token(rule_data, line, col)

            cursor += offset
            col += offset
        cursor += 1

    tokens.append(Token("EOF", None, line, col))
    return tokens