# This is automatically generated code. Do not modify
from peggen.peggen_ import *
PUNC_44 = StringRule(",")
PUNC_123 = StringRule("{")
PUNC_125 = StringRule("}")
PUNC_91 = StringRule("[")
PUNC_93 = StringRule("]")
PUNC_58 = StringRule(":")
TRUE = StringRule("true")
FALSE = StringRule("false")
NULL = StringRule("null")
ROOT = Production(name = "root")
TOKEN = Production(name = "token")
PUNCTUATOR = Production(name = "punctuator")
KEYWORD = Production(name = "keyword")
KEYWORD_VALUE = Production(name = "keyword_value")
VALUE = Production(name = "value")
WHITESPACE = Production(name = "whitespace")
OBJECT = Production(name = "object")
MEMBERS = Production(name = "members")
MEMBER = Production(name = "member")
ARRAY = Production(name = "array")
ELEMENTS = Production(name = "elements")
STRING = Production(name = "string")
INT_CONSTANT = Production(name = "int_constant")
DECIMAL_FLOAT_CONSTANT = Production(name = "decimal_float_constant")
NUMBER = Production(name = "number")

class jsonpegParser(Parser):
    def __init__(self, string, *args, **kwargs):
        super().__init__(string, TOKEN, ROOT, *args, **kwargs)
__all__ = ["PUNC_44","PUNC_123","PUNC_125","PUNC_91","PUNC_93","PUNC_58","TRUE","FALSE","NULL","ROOT","TOKEN","PUNCTUATOR","KEYWORD","KEYWORD_VALUE","VALUE","WHITESPACE","OBJECT","MEMBERS","MEMBER","ARRAY","ELEMENTS","STRING","INT_CONSTANT","DECIMAL_FLOAT_CONSTANT","NUMBER","jsonpegParser"]
