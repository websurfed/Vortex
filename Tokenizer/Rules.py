from . import Funcs
from .Types import Rule, Type

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
    (Rule.VARIABLE, Funcs.lock_identifier, Funcs.match_identifier),
    (Rule.DYNAMIC, Type.NUMERIC, Funcs.lock_numeric, Funcs.match_numeric)
]