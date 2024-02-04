# This is automatically generated code. Do not modify
from peggen.peggen_ import *
from BasicCalculator_impl import *
from BasicCalculator_ import *
Production.__init__(ROOT, EXPRESSION, "root", run_basic_calculator)
Production.__init__(TOKEN, LongChoice([PUNCTUATOR,NUMBER,WHITESPACE], '(punctuator | number | whitespace)'), "token", token_action)
Production.__init__(WHITESPACE, RegexRule("\s+"), "whitespace", skip_token)
Production.__init__(PUNCTUATOR, RegexRule("(\+)|(-)|(/)|(\*)|(\^)|(\()|(\))|(%)"), "punctuator", prod_transform_def)
Production.__init__(ADD_SUB_EXPRESSION, And([MUL_DIV_MOD_EXPRESSION,Repeat(And([UNARY_OPERATOR,MUL_DIV_MOD_EXPRESSION], '(unary_operator, mul_div_mod_expression)'), 0, 0)], '(mul_div_mod_expression, (unary_operator, mul_div_mod_expression){0:})'), "add_sub_expression", prod_transform_def)
Production.__init__(MUL_DIV_MOD_EXPRESSION, And([POWER_EXPRESSION,Repeat(And([LongChoice([MULTIPLY,DIVIDE,MOD], '(multiply | divide | mod)'),POWER_EXPRESSION], '((multiply | divide | mod), power_expression)'), 0, 0)], '(power_expression, ((multiply | divide | mod), power_expression){0:})'), "mul_div_mod_expression", prod_transform_def)
Production.__init__(POWER_EXPRESSION, And([UNARY_EXPRESSION,Repeat(And([POWER,UNARY_EXPRESSION], '(power, unary_expression)'), 0, 0)], '(unary_expression, (power, unary_expression){0:})'), "power_expression", prod_transform_def)
Production.__init__(EVALUATED_EXPRESSION, LongChoice([NUMBER,And([PUNC_40,EXPRESSION,PUNC_41], '((, expression, ))')], '(number | ((, expression, )))'), "evaluated_expression", prod_transform_def)
Production.__init__(UNARY_EXPRESSION, And([Repeat(UNARY_OPERATOR, 0, 0),EVALUATED_EXPRESSION], '(unary_operator{0:}, evaluated_expression)'), "unary_expression", prod_transform_def)
Production.__init__(UNARY_OPERATOR, LongChoice([ADD,SUBTRACT], '(add | subtract)'), "unary_operator", prod_transform_def)
Production.__init__(EXPRESSION, ADD_SUB_EXPRESSION, "expression", prod_transform_def)
Production.__init__(ADD, PUNC_43, "add", prod_transform_def)
Production.__init__(SUBTRACT, PUNC_45, "subtract", prod_transform_def)
Production.__init__(DIVIDE, PUNC_47, "divide", prod_transform_def)
Production.__init__(MULTIPLY, PUNC_42, "multiply", prod_transform_def)
Production.__init__(POWER, PUNC_94, "power", prod_transform_def)
Production.__init__(MOD, PUNC_37, "mod", prod_transform_def)
Production.__init__(NUMBER, LongChoice([INTEGER,FLOAT], '(integer | float)'), "number", prod_transform_def)
Production.__init__(INTEGER, RegexRule("([1-9]\d*)|0"), "integer", prod_transform_def)
Production.__init__(FLOAT, RegexRule("((((\d*\.\d+)|(\d+\.))([eE][-+]?\d+)?)|(\d+[eE][-+]?\d+))"), "float", prod_transform_def)