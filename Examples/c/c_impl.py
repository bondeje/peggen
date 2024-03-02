from c_ import *
import os
from peggen.peggen_ import SEEK_SET, SEEK_CUR, Node

class CParser(cParser):
    def __init__(self, filename_or_string, *args, astfile = None, **kwargs):
        if os.path.isfile(filename_or_string):
            self.filename = filename_or_string
            with open(filename_or_string, 'r') as file_in:
                string = file_in.read()
        else:
            self.filename = None
            string = filename_or_string
        self.astfile = astfile
        super().__init__(string, *args, **kwargs)        

def directive_line(parser, prod_node):
    start = prod_node.token_key
    line = parser[start].line
    end = start + prod_node.ntokens
    token = parser[end]
    #print(f"directive found on line {line} at token {start}: '{str(parser[start])}'")
    while len(token) and token.line == line:
        #print(f"absorbing token '{str(token)}'")
        parser.seek(1, SEEK_CUR)
        end += 1
        token = parser[end]
    # token now points to a token on the next line or the final token in the parser stream
    prod_node.length = parser[end].start - parser[start].start
    prod_node.ntokens = end - start
    parser.seek(end, SEEK_SET)
    return prod_node

#def interpret_root(parser, ast):
#    print("called traverse function", parser.astfile)
#    if parser.astfile is not None:
#        with open(parser.astfile, 'w') as file_out:
#            file_out.write(parser.print_ast())

def from_file(filename, file_out = None, *args, **kwargs):
    result = None
    with open(filename, 'r') as file_in:
        result = from_string(file_in.read(), file_out, *args, **kwargs)
    return result
def from_string(string, file_out, *args, **kwargs):
    result = CParser(string, *args, **kwargs).print_ast()
    if file_out is not None:
        with open(file_out, 'w') as file_out:
            file_out.write(result)
    return result