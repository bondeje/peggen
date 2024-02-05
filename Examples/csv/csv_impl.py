from csvpeg_ import *
from collections.abc import Sequence

class CSV:
    __slots__ = ("headers", "records")
    def __init__(self, records, headers = None):
        self.headers = headers
        self.records = records
    def __getitem__(self, key):
        if isinstance(key, slice) or (isinstance(key, int) and (0 <= key < len(self.records))):
            return self.records[key]
        if isinstance(key, Sequence) and len(key) == 2:
            return self.records[key[0]][key[1]]
        raise KeyError(f"Invalid format of key {key} for type 'CSV'. Requires integer [0, {len(self)}), slice, or 2-element tuple")
    def __len__(self):
        return len(self.records)
    def get_headers(self):
        return self.headers
    def get_records(self):
        return self.records
    def __iter__(self):
        return iter(self.records)
    def __str__(self):
        out = ["headers:",f"\t{','.join(str(f) for f in self.headers) if self.headers else ''}"]
        out.append("records:")
        for row in self:
            out.append(f"\t{','.join(str(f) for f in row)}")
        return '\n'.join(out)

class csvreader(csvpegParser):
    def __init__(self, string, has_headers=False):
        self.has_headers_ = has_headers
        super().__init__(string)
    def has_headers(self):
        return self.has_headers_
    def load(self, default = None):
        if self.ast is None:
            self.parse()
        if self.ast is not FAIL_NODE:
            return CSV(*self.ast.get_value())
        return default
    
class CSVData(Node):
    __slots__ = ("value", )
    def __init__(self, base_node, value):
        super().__init__(base_node.rule, base_node.token_key, base_node.ntokens, base_node.length, base_node.children)
        self.value = value
    def get_value(self):
        return self.value
    
def load(filename, has_headers = False):
    with open(filename, 'r') as file_in:
        return loads(file_in.read())
    return None
def loads(string, has_headers = False):
    return csvreader(string, has_headers).load()

def handle_root(parser, node):
    nodec = node[0]
    out = [[]]
    for i, record in enumerate(nodec[0]):
        if not i and parser.has_headers():
            out.append(handle_record(parser, record))
        else:
            out[0].append(handle_record(parser, record))
    return CSVData(node, out)
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