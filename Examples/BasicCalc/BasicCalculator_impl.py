from BasicCalculator_ import *
import operator

OPERATIONS = {'+': operator.add, 
              '-': operator.sub, 
              '*': operator.mul, 
              '/': operator.truediv, 
              '%': operator.mod, 
              '^': operator.pow}

def handle_number(parser, node):
    if node[0].rule == INTEGER:
        return int(str(parser.get_tokens(node[0])[0]))
    else:
        return float(str(parser.get_tokens(node[0])[0]))

def handle_evaluated_expression(parser, node):
    #print("handle_evaluated_expression")
    #print(node[0])
    if node[0].rule is NUMBER:
        result = handle_number(parser, node[0])
    else:
        result = handle_expression(parser, node[0][1])
    #print(result)
    return result
    #return 1

def handle_unary_expression(parser, node):
    #print("handle_unary_expression")
    #print(node[0])
    result = handle_evaluated_expression(parser, node[0][1])
    for op in reversed(node[0][0]):
        if op[0].rule is SUBTRACT:
            result *= -1
    #print(result)
    return result

def handle_power_expression(parser, node):
    #print("handle_power_expression")
    #print(node[0])
    result = 1
    for bin_op in reversed(node[0][1]):
        #print(bin_op.rule)
        result = handle_unary_expression(parser, bin_op[1])**result
    #result = handle_unary_expression(parser, node[0][0])**result
        
    # manually breaking up the unary_expression into the unary_operator* and evaluated_expression
    # means we can replicate the python operator precedence with the power operator
    result = handle_evaluated_expression(parser, node[0][0][0][1])**result
    #print(result)
    for op in reversed(node[0][0][0][0]):
        if op[0].rule is SUBTRACT:
            result *= -1
    #print(result)
    return result

def handle_mul_div_mod_expression(parser, node):
    #print("handle_mul_div_mod_expression")
    #print(node[0])
    result = handle_power_expression(parser, node[0][0])
    #print(result)
    for bin_op in node[0][1]:
        denom = handle_power_expression(parser, bin_op[1])
        if denom == 0:
            raise ValueError(f"divide by zero at {parser._get_line_col_end(parser[bin_op[1].token_key])[0]}")
        result = OPERATIONS[str(parser.get_tokens(bin_op[0])[0])](result, denom)
    #print(result)
    return result

def handle_add_sub_expression(parser, node):
    #print("handle_add_sub_expression")
    #print(node[0])
    result = handle_mul_div_mod_expression(parser, node[0][0])
    #print(result)
    #print(node[0][1])
    for bin_op in node[0][1]:
        #print(bin_op[0])
        result = OPERATIONS[str(parser.get_tokens(bin_op[0])[0])](result, handle_mul_div_mod_expression(parser, bin_op[1]))
    #print(result)
    return result

def handle_expression(parser, node):
    #print("handle_expression")
    return handle_add_sub_expression(parser, node[0])

def run_basic_calculator(parser, root):
    #print(root)
    print([str(t) for t in parser], '=', handle_expression(parser, root[0]))
    return root