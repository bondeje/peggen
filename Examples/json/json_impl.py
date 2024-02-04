from jsonpeg_ import *

def handle_true(parser, node):
    return True
def handle_false(parser, node):
    return False
def handle_null(parser, node):
    return None
def handle_root(parser, node):
    return print([str(t) for t in parser], '=', [handle_value(parser, v) for v in node[0]])
def handle_value(parser, node):
    rule = node[0].rule
    if rule is OBJECT:
        return handle_object(parser, node[0])
    elif rule is ARRAY:
        return handle_array(parser, node[0])
    elif rule is STRING:
        return handle_string(parser, node[0])
    elif rule is NUMBER:
        return handle_number(parser, node[0])
    else: # keyword_value
        return handle_keyword_value(parser, node[0])
def handle_object(parser, node):
    obj = {}
    if len(node[0][1]):
        handle_members(parser, node[0][1], obj)
    return obj
def handle_array(parser, node):
    #print("handling array")
    arr = []
    if len(node[0][1]):
        handle_elements(parser, node[0][1], arr)
    return arr
def handle_elements(parser, node, arr):
    #print("handle_elements")
    #print(node[0])
    for element in node[0][0]:
       # print(element)
        arr.append(handle_value(parser, element))
def handle_string(parser, node):
    return str(parser.get_tokens(node[0])[0])
def handle_number(parser, node):
    if node[0].rule is INT_CONSTANT:
        return handle_int_constant(parser, node[0])
    return handle_float_constant(parser, node[0])
def handle_keyword_value(parser, node):
    rule = node[0].rule
    if rule is TRUE:
        return handle_true(parser, node[0])
    elif rule is FALSE:
        return handle_false(parser, node[0])
    else: # null
        return handle_null(parser, node[0])
def handle_members(parser, node, obj):
    for member in node[0][0]:
        handle_member(parser, member, obj)
def handle_member(parser, node, obj):
    obj[handle_string(parser, node[0][0])] = handle_value(parser, node[0][2])
def handle_int_constant(parser, node):
    return int(str(parser.get_tokens(node[0])[0]))
def handle_float_constant(parser, node):
    return float(str(parser.get_tokens(node[0])[0]))