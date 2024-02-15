from c_ import *
from peggen.peggen_ import SEEK_SET
"""
class Scope:
    def __init__(self, parent = None, name = None):
        self.parent = parent # a parent scope
        self.name = name
        self.structs = {}
        self.enums = {}
        self.unions = {}
        self.identifiers = {}
    def add_identifier(name):


class CParser(cParser):
    def __init__(self, string, *args, **kwargs):
        self.scope = Scope(None, "Global")
        super().__init__(string, *args, **kwargs)
        """

def directive_line(parser, prod_node):
    start = prod_node.token_key
    line = parser[start].line
    end = start + 1
    token = parser[end]
    while len(token) and token.line == line:
        end += 1

        token = parser[end]
    # token now points to a token on the next line or the final token in the parser stream
    prod_node.length = parser[end].start - parser[start].start
    prod_node.ntokens = end - start
    parser.seek(end, SEEK_SET)
    return prod_node

def from_file(filename, file_out = None, *args, **kwargs):
    result = None
    with open(filename, 'r') as file_in:
        result = from_string(file_in.read(), file_out, *args, **kwargs)
    return result
def from_string(string, file_out, *args, **kwargs):
    result = cParser(string, *args, **kwargs).print_ast()
    if file_out is not None:
        with open(file_out, 'w') as file_out:
            file_out.write(result)
    return result