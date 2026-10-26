from argparse import ArgumentError

from .Types import Rule, Type, Token
from .Rules import TOKEN_RULES

INDENTATION_NUM: int = 4

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
        rule = None
        rule_type = None
        rule_literal = ""
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

def _is_line_blank(source: str, cursor: int) -> tuple[bool, int]:
    length = len(source)
    if length == 0:
        return True, 0

    char = source[cursor]
    if char == '\n':
        return True, 0

    offset = 0
    while cursor + offset < length and source[cursor + offset] != '\n':
        offset += 1

    final_cursor = cursor + offset
    final_str = source[cursor:final_cursor]
    stripped = final_str.strip(' ')
    if stripped == '' or stripped.startswith('#'):
        if stripped.startswith('#'):
            offset = source[cursor:len(source)].find('#')
        return True, min(offset, length)

    return False, 0

def lex(source: str) -> list[Token]:
    if source.strip() == '':
        return [Token(Type.EOF, None, 1, 1)]

    if source and not source.endswith('\n'):
        source += '\n'

    compiled_static_rules = _compile_static_rules()
    compiled_dynamic_rules = _compile_dynamic_rules()
    compiled_variable_rules = _compile_variable_rules()

    cursor: int = 0
    length: int = len(source)
    newline = True

    indent_stack = [0]
    promise_non_logical = False
    last_indent_stack = indent_stack.copy()
    tokens = []
    line = 1
    col = 1

    while cursor < length:
        char: str = source[cursor]

        # tracking
        if newline:
            newline = False

            blank_check, offset = _is_line_blank(source, cursor)
            if blank_check:
                # tokens.append(Token(Type.NON_LOGICAL_LINE, None, line, col))
                promise_non_logical = True

                col += offset
                cursor += offset

                continue

            if char == '\t':
                raise IndentationError("Tabs are not accepted for indentation, use spaces")

            spaces = 0
            while cursor + spaces < length and source[cursor + spaces] == ' ':
                spaces += 1

            if spaces % INDENTATION_NUM != 0:
                raise IndentationError("Invalid indentation level")

            normalized: int = spaces // INDENTATION_NUM
            level = indent_stack[-1]
            diff = normalized - level

            if normalized > level:
                if diff > 1:
                    raise IndentationError("Indented too much")
                indent_stack.append(level + 1)
                tokens.append(Token(Type.INDENT, '1', line, col))
            elif normalized < level:
                for _ in range(abs(diff)):
                    del indent_stack[-1]
                tokens.append(Token(Type.DEDENT, str(abs(diff)), line, col))

        # specials
        if char == '\n':
            last_token = None
            if len(tokens) > 0:
                last_token = tokens[-1].type

            current_token = max(len(tokens) - 1, 0)
            offset = current_token
            while offset > 0 and tokens[offset].type not in (Type.NEWLINE, Type.NON_LOGICAL_LINE):
                offset -= 1
            offset = offset + 1 if tokens[offset].type in (Type.NEWLINE, Type.NON_LOGICAL_LINE) else offset
            token_slice = tokens[offset:current_token + 1]

            logical_tokens = False
            for t in token_slice:
                if t.type not in (Type.INDENT, Type.DEDENT, Type.COMMENT):
                    logical_tokens = True
                    break
            if not logical_tokens:
                indent_stack = last_indent_stack.copy()
                token_slice = [t for t in token_slice if t.type == Type.COMMENT]
            tokens[offset:current_token + 1] = token_slice
            print(f"LOGICAL TOKEN: {logical_tokens} | TOKENS: {token_slice}")

            this_type = Type.NEWLINE
            tokens.append(Token(this_type, None, line, col))

            cursor += 1
            line += 1
            col = 1

            newline = True
            last_indent_stack = indent_stack.copy()
            continue
        elif char == '#':
            offset = 0
            while cursor + offset < length and source[cursor + offset] != '\n':
                offset += 1

            comment = source[cursor:cursor+offset]
            tokens.append(Token(Type.COMMENT, comment, line, col))

            col += offset
            cursor += offset

            continue

        # standards
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
            if char == ' ':
                cursor += 1
                col += 1
            else:
                raise SyntaxError(
                    f"Unexpected character {char!r} at line {line}, col {col}"
                )

    # if len(tokens) > 0 and tokens[-1].type not in (Type.NEWLINE, Type.NON_LOGICAL_LINE):
    #     tokens.append(Token(Type.NEWLINE, None, line, col))

    if len(indent_stack) > 1:
        levels = indent_stack[-1]
        tokens.append(Token(Type.DEDENT, str(levels), line, col))
        indent_stack = []

    tokens.append(Token(Type.EOF, None, line, col))
    return tokens