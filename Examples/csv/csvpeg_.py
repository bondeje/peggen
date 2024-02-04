# This is automatically generated code. Do not modify
from peggen.peggen_ import *
PUNC_44 = StringRule(",")
ROOT = Production(name = "root")
TOKEN = Production(name = "token")
RECORD = Production(name = "record")
NONSTRING_FIELD = Production(name = "nonstring_field")
FIELD = Production(name = "field")
WHITESPACE = Production(name = "whitespace")
CRLF = Production(name = "crlf")
PUNCTUATOR = Production(name = "punctuator")
STRING = Production(name = "string")

class csvpegParser(Parser):
    def __init__(self, string, line_offset = 0, col_offset = 0):
        super().__init__(string, TOKEN, ROOT, line_offset, col_offset)
