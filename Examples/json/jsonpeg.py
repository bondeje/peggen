# This is automatically generated code. Do not modify
from peggen.peggen_ import *
from json_impl import *
from jsonpeg_ import *
Production.__init__(ROOT, Repeat(VALUE, 1, 0), "root", handle_root)
Production.__init__(TOKEN, FirstChoice([WHITESPACE,STRING,KEYWORD_VALUE,NUMBER,PUNCTUATOR], '(whitespace \ string \ keyword_value \ number \ punctuator)'), "token", token_action)
Production.__init__(PUNCTUATOR, RegexRule("(,)|(\{)|(})|(\[)|(])|(:)"), "punctuator", prod_action_default)
Production.__init__(KEYWORD, RegexRule("(true)|(false)|(null)"), "keyword", prod_action_default)
Production.__init__(KEYWORD_VALUE, FirstChoice([TRUE,FALSE,NULL], '(true \ false \ null)'), "keyword_value", prod_action_default)
Production.__init__(VALUE, FirstChoice([OBJECT,ARRAY,KEYWORD_VALUE,STRING,NUMBER], '(object \ array \ keyword_value \ string \ number)'), "value", prod_action_default)
Production.__init__(WHITESPACE, RegexRule("\s+"), "whitespace", skip_token)
Production.__init__(OBJECT, And([PUNC_123,Repeat(MEMBERS, 0, 1),PUNC_125], '({, members{0:1}, })'), "object", prod_action_default)
Production.__init__(MEMBERS, List(MEMBER, PUNC_44), "members", prod_action_default)
Production.__init__(MEMBER, And([STRING,PUNC_58,VALUE], '(string, :, value)'), "member", prod_action_default)
Production.__init__(ARRAY, And([PUNC_91,Repeat(ELEMENTS, 0, 1),PUNC_93], '([, elements{0:1}, ])'), "array", prod_action_default)
Production.__init__(ELEMENTS, List(VALUE, PUNC_44), "elements", prod_action_default)
Production.__init__(STRING, RegexRule("\"(((?<=\\\\)\")|[^\"])*\""), "string", prod_action_default)
Production.__init__(INT_CONSTANT, RegexRule("[-+]?(([1-9]\d*)|(0(x|X)[A-Fa-f0-9]+)|(0[0-7]*))"), "int_constant", prod_action_default)
Production.__init__(DECIMAL_FLOAT_CONSTANT, RegexRule("[-+]?((((\d*\.\d+)|(\d+\.))([eE][-+]?\d+)?)|(\d+[eE][-+]?\d+))"), "decimal_float_constant", prod_action_default)
Production.__init__(NUMBER, LongChoice([INT_CONSTANT,DECIMAL_FLOAT_CONSTANT], '(int_constant | decimal_float_constant)'), "number", prod_action_default)