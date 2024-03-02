# This is automatically generated code. Do not modify
from peggen.peggen_ import *
from csv_impl import *
from csvpeg_ import *
Production.__init__(ROOT, And([List(RECORD, CRLF),Repeat(FirstChoice([CRLF,WHITESPACE], '(crlf / whitespace)'), 0, 0)], '(crlf.record, (crlf / whitespace){0:})'), "root", handle_root)
Production.__init__(TOKEN, FirstChoice([CRLF,PUNCTUATOR,WHITESPACE,FIELD], '(crlf / punctuator / whitespace / field)'), "token", token_action)
Production.__init__(RECORD, List(FIELD, PUNC_44), "record", prod_action_default)
Production.__init__(NONSTRING_FIELD, RegexRule("[^,\r\n]*"), "nonstring_field", prod_action_default)
Production.__init__(FIELD, FirstChoice([STRING,NONSTRING_FIELD], '(string / nonstring_field)'), "field", prod_action_default)
Production.__init__(WHITESPACE, RegexRule("[ \t\f\v]+"), "whitespace", skip_token)
Production.__init__(CRLF, RegexRule("\r\n"), "crlf", prod_action_default)
Production.__init__(PUNCTUATOR, RegexRule("(,)"), "punctuator", prod_action_default)
Production.__init__(STRING, RegexRule("\"(((?<=\\\\)\")|[^\"])*\""), "string", prod_action_default)