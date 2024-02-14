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
    def __init__(self, string, *args, **kwargs):
        super().__init__(string, TOKEN, ROOT, *args, **kwargs)
__all__ = ["PUNC_44","ROOT","TOKEN","RECORD","NONSTRING_FIELD","FIELD","WHITESPACE","CRLF","PUNCTUATOR","STRING","csvpegParser"]
