from csvpeg_ import *

class csvreader(csvpegParser):
    def __init__(self, string, headers=False):
        self.headers = headers
        super().__init__(string)
    def has_headers(self):
        return self.headers

def handle_root(parser, node):
    node = node[0]
    out = [[]]
    for i, record in enumerate(node[0]):
        if not i and parser.has_headers():
            out.append(handle_record(parser, record))
        else:
            out[0].append(handle_record(parser, record))
    print([str(t) for t in parser], '=', out)
#def handle_header(parser, node):
#    return [handle_field(parser, f) for f in node[0]]
def handle_record(parser, node):
    return [handle_field(parser, f) for f in node[0]]
def handle_nonstring_field(parser, node):
    return str(parser.get_tokens(node[0])[0])
def handle_field(parser, node):
    node = node[0]
    if node.rule is STRING:
        return handle_string(parser, node)
    return handle_nonstring_field(parser, node)
def handle_string(parser, node):
    return str(parser.get_tokens(node[0])[0])