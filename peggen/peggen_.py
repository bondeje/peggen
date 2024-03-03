import os, re, time, copy
from collections import deque
from _io import TextIOWrapper

# BIG TODOS
# 1) 
# I do not like the way that I handle is_SKIP_TOKEN in class Production._check_rule. 
# I do not want to have to check is_SKIP_NODE in each production. 
# This is mainly for the tokenizer, so a better way might be to use "skip_token" to
# have it as a flag in Rule and then token_action checks for it and skips as needed
# this might clean up the code but would add memory to Rule and require some refactoring

SEEK_SET = 0
SEEK_CUR = 1
SEEK_END = 2

ACTION_REGEX = re.compile("[a-zA-Z0-9_\.]*")

TRAVERSE_INORDER = 0
TRAVERSE_PREORDER = 1
TRAVERSE_POSTORDER = 2
TRAVERSE_LEVELORDER = 3
DEFAULT_INDENTATION = '    '

CACHE_CHECKING = 0
CACHE_RECORDING = 1
RULE_CHECKING = 2
LOGGING = 3
TIMES = [0.0, 0.0, 0.0, 0.0]
RULE_CHECK_NUM = 0
CACHE_HITS = 1
RULE_CHECKS = [0, 0]

# source is a file
class IOSource:
    def __init__(self, source):
        # treat source as a file
        self.source = source
        self.markers = []
        self.size = 0
    def read(self, nchar = 1):
        raise NotImplementedError("read not implemented")
    def read_until_char(self, stop_char_set, include = False, complement = False):
        self.mark()
        #print("before read_until_char:", self.tell())
        size = 0
        if isinstance(stop_char_set, str):
            stop_char_set = set(stop_char_set)
        c = self.read(1)
        if not complement:
            while c and c not in stop_char_set:
                size += 1
                c = self.read(1)
            stopped = c
        if complement:
            while c and c in stop_char_set:
                size += 1
                c = self.read(1)
            stopped = c
        
        if c and include:
            size += 1
        self.reset()
        #print("after read_until_char:", self.tell())
        return self.read(size), stopped
    # this is a pretty inefficient method
    def read_until_string(self, string, include = False):
        self.mark()
        #print("in read_until_string:", self.tell())
        size = 0
        string_size = len(string)
        c = self.read(1)
        while c:
            if c == string[size]:
                size += 1
                if size == string_size:
                    break
            else:
                self.seek(self.tell() - size, SEEK_SET)
                size = 0
            c = self.read(1)
        if c:
            if size == string_size and not include:
                self.seek(self.tell() - size, SEEK_SET)
            end = self.tell()
        elif not c:
            end = self.size
            self.seek(0, SEEK_END)
        self.reset()
        #print("found string at:", end, self.tell())
        return self.read(end-self.tell()), (string if size == string_size else '')
    def seek(self, offset, whence):
        raise NotImplementedError("seek not implemented")
    def tell(self):
        raise NotImplementedError("tell not implemented")
    def mark(self):
        self.markers.append(self.tell())
    def reset(self):
        if len(self.markers):
            self.seek(self.markers.pop(), whence = SEEK_SET)
        else:
            self.seek(0, whence = SEEK_SET)
    def peek(self, nchar = 1):
        self.mark()
        str_out = self.read(nchar)
        self.reset()
        return str_out
    def close(self):
        pass
    
class StringSource(IOSource):
    def __init__(self, source):
        super().__init__(source)
        #print("read string source")
        self.loc = 0
        self.size = len(source)
        #print(self.size)
    def read(self, nchar = 1):
        if not nchar:
            return ''
        nchar = min(self.size - self.loc, nchar)
        self.loc += nchar
        return self.source[self.loc - nchar:self.loc]
    def seek(self, offset, whence = SEEK_CUR):
        if whence == SEEK_SET:
            if offset < 0:
                offset = self.size + offset
            self.loc = offset
        elif whence == SEEK_CUR:
            if offset < 0 and -offset > self.loc:
                offset = (offset + self.loc) + self.size
            elif offset > 0:
                self.loc = min(self.loc + offset, self.size)
        else: # whence == SEEK_END
            self.seek(-offset, whence = SEEK_SET)
    def read_regex(self, regex):
        s = regex.match(self.source, self.loc, self.size).group(0)
        if s is not None:
            self.read(len(s))
        return s
    def tell(self):
        return self.loc

class FileSource(IOSource):
    def __init__(self, source):
        super().__init__(open(source, 'rb'))
        #print("opened file source")
        self.source.seek(0, SEEK_END)
        self.size = self.source.tell()
        self.source.seek(0, SEEK_SET)
        #print(self.size)
    def tell(self):
        return self.source.tell()
    def seek(self, offset, whence = SEEK_CUR): # This is UB for everything other than whence==SEEK_SET or offset==0 and whence==SEEK_END
        self.source.seek(offset, whence)
    def read(self, nchar = 1):
        if not nchar:
            return ''
        return str(self.source.read(nchar), 'ascii')
    def close(self):
        self.source.close()

WHITESPACE = {' ', '\t', '\v', '\r', '\n', '\f'}
    
WORD = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')
PROD_DEF = ':'
COMMENT_HINT = '/'
ESCAPE_CHAR = '\\'
LINE_COMMENT_OPEN = '//'
LINE_COMMENT_CLOSE = {'\n'}
BLOCK_COMMENT_OPEN = '/*'
BLOCK_COMMENT_CLOSE = '*/'
STRING_LITERAL_OPEN = "'"
STRING_LITERAL_CLOSE = {"'"}
REGEX_OPEN = '"'
REGEX_CLOSE = '"'
BINARY_OP_SEQ = 0   # ','
BINARY_OP_FIRST = 1 # '\\'
BINARY_OP_LONG = 2  # '|'
BINARY_OP = {',': BINARY_OP_SEQ, '\\': BINARY_OP_FIRST, '|': BINARY_OP_LONG}
TRANSFORM_OPEN = '('
TRANSFORM_CLOSE = {')'}
EOF = ''


PGEN_STATE_END = -1
PGEN_STATE_IDLE = 0
PGEN_STATE_WHITESPACE = 1 # this is also IDLE state
PGEN_STATE_WORD = 2

## not sure if I need these...probably useful
#PGEN_RULE_AND = 0
#PGEN_RULE_OR_LONG = 1
#PGEN_RULE_OR_FIRST = 2
#PGEN_RULE_OPT = 3
#PGEN_RULE_ZERO_OR_MORE = 4
#PGEN_RULE_ONE_OR_MORE = 5
#PGEN_RULE_LIST = 6
#PGEN_RULE_REPEAT = 7
#PGEN_RULE_NEGATIVE_LOOKAHEAD = 8
#PGEN_RULE_POSTIVIE_LOOKAHEAD = 9

#once initialized, Tokens should not really be changed except by the lexer
class Token:
    __slots__ = ('string', 'start', 'end', 'line', 'col', '_hash')
    def __init__(self, string, start, end, line = 0, col = 0):
        self.string = string
        self.start = start
        self.end = end
        self.line = line
        self.col = col
        self._hash = hash((id(self.string), self.start))
    def __len__(self):
        return self.end - self.start
    def coords(self):
        return self.line, self.col
    def __hash__(self):
        return self._hash
    def __str__(self):
        return self.string[self.start:self.end]
    def __getitem__(self, key):
        if key < self.end - self.start:
            return self.string[self.start + key]
        raise ValueError(f"index out of bounds in token: {Token}")

class Node:
    __slots__ = ("type", "length", 'children', 'rule', 'token_key', 'ntokens') # length and ntokens might be redundant. Have to check if PASS_NODE vs FAIL_NODE still makes sense
    def __init__(self, rule, token_key, ntokens, length, children):
        self.type = "Node"
        self.length = length # this is the length of the string covered by the node
        self.children = children
        self.rule = rule
        self.token_key = token_key
        self.ntokens = ntokens
    def __iter__(self):
        if self.children is not None:
            return iter(self.children)
        return iter([])
    def __getitem__(self, key):
        return self.children[key]
    def __len__(self):
        return 0 if not self.children else len(self.children)
    def __str__(self):
        #print(self.children)
        if self.children:
            return f"{self.type}: {self.rule} @{self.token_key}. Length: {self.length}/{self.ntokens}. Children: {len(self.children)}"
        else:
            return f"{self.type}: {self.rule} @{self.token_key}. Length: {self.length}/{self.ntokens}"
        return 'NO NODE!'
    def traverse_action(self, ctxt):
        return True
    def build_action(self, ctxt):
        return self
#    def print(self, buffer, indent = None):
#        if self.ntokens:
#            if indent is None:
#                indent = []
#            if self.ntokens == 1:
#                buffer.append(''.join(indent) + f"{self.type}: {self.rule} @{self.token_key}. Length: {self.length}/{self.ntokens}")
#            else:
#                buffer.append(''.join(indent) + f"{self.type}: {self.rule} @{self.token_key}. Length: {self.length}/{self.ntokens}. Children: {len(self.children)}")
#                indent.append(DEFAULT_INDENTATION)
#                for child in self:
#                    child.print(buffer, indent)
#                indent.pop()
    
#class ProductionNode(Node):
#    __slots__ = tuple()
#    def __init__(self, *args):
#        super().__init__(*args)
#        self.type = "ProductionNode"
#    def traverse_action(self, ctxt):
#        return self.rule.traverse_action(ctxt, self)
#    def build_action(self, ctxt):
#        return self.rule.build_action(ctxt, self)

FAIL_NODE = Node(None, 0, 0, 0, None) # this is a placeholder for an empty Node to indicate failures different from None
LOOKAHEAD_NODE = Node(None, 0, 0, 1, None) # LOOKAHEAD_NODE should have is_SKIP_NODE return True. This is handled by class And._check_rule to properly skip it

def make_SKIP_NODE(node):
    node.rule = None
    node.length = max(node.length, 1)
    #print("made skip node")
    return node

def is_SKIP_NODE(node):
    return node.length > 0 and not node.rule

# use in e.g. WHITESPACE or comments
def skip_token(parser, node):
    #print(f"skipping token for node rule: {node.rule}")
    return make_SKIP_NODE(node)

def token_action(parser, node):
    if node is not FAIL_NODE: # a token was found
        #print("token found:", parser.tell())
        #print("token (in token_action):",node, is_SKIP_NODE(node))
        if is_SKIP_NODE(node):
            #print("skipping")
            parser.skip_token(node)
        else:
            parser.add_token(node)
        parser.seek(-1, SEEK_CUR) # need to back up one token in order to ensure not erroneously moving the parser location forward
        #print("after token processed:", parser.tell())
    #else:
        #print("token search failed:", str(parser[-1]))
    return node

class Rule:
    __slots__ = ("_id", "_cache")
    def __init__(self, _id = None):
        self._id = _id
        self._cache = {} # store Token: Node key:value pair
    def __str__(self):
        return self._id if self._id is not None else "None"
    def build(self, parser_generator):
        raise NotImplementedError(f"rule did not overload build(list_name, enum_name) for id {self._id}, type={type(self)}")
    def _cache_check(self, parser, token_key, result):
        #print(f"in _cache_check for {self._id}")
        self._cache[parser[token_key]] = result
    def _check_cache(self, parser, token_key):
        #print(f"in _check_cache for {self._id}")
        token = parser[token_key]
        res = None
        if token in self._cache:
            res = self._cache[token]
            parser.seek(res.ntokens, SEEK_CUR) # this works even for FAIL_NODE since ntokens must be 0
        return res
    def clear_cache(self, token):
        if token in self._cache:
            self._cache.pop(token)
    def _check_rule(self, parser, token_key, disable_cache_check = False):
        raise NotImplementedError(f"rule did not overload _check_rule(parser, token_key) for id {self._id}, type={type(self)}")
    def check(self, parser, disable_cache_check = False):
        #print(self)
        #RULE_CHECKS[RULE_CHECK_NUM] += 1
        token_key = parser.tell()
        #print(f"checking rule: {self._id} at {token_key}...")
        if not disable_cache_check:
            #t0 = time.perf_counter_ns()
            res = self._check_cache(parser, token_key)
            #t1 = time.perf_counter_ns()
            #TIMES[CACHE_CHECKING] += t1 - t0
            if res is not None:
                #RULE_CHECKS[CACHE_HITS] += 1
                #print("returning from cache")
                return res
        #t0 = time.perf_counter_ns()
        res = self._check_rule(parser, token_key, disable_cache_check)
        #t1 = time.perf_counter_ns()
        #TIMES[RULE_CHECKING] += t1 - t0
        #t0 = time.perf_counter_ns()
        self._cache_check(parser, token_key, res)
        #t1 = time.perf_counter_ns()
        #TIMES[CACHE_RECORDING] += t1 - t0

        #t0 = time.perf_counter_ns()
        parser.log(token_key, self, res)
        #t1 = time.perf_counter_ns()
        #TIMES[LOGGING] += t1 - t0
        if res is FAIL_NODE:
            parser.seek(token_key, SEEK_SET)
        #print(f"RESULT {'Success' if res is not FAIL_NODE else 'Failed '} {self._id} ...{repr(str(parser[token_key]))}, loc = {parser.tell()}")
        return res
        
    
# This is an ABC, not to be instantiated
class ChainedRule(Rule):
    __slots__ = ("terms_nonterms",)
    def __init__(self, terms_nonterms, _id = None):
        super().__init__(_id)
        self.terms_nonterms = terms_nonterms
    def clear_cache(self, token):
        if token in self._cache:
            self._cache.pop(token)
            for t in self.terms_nonterms:
                t.clear_cache(token)
    
class And(ChainedRule):
    __slots__ = tuple()
    def __init__(self, terms_nonterms, _id = None):
        if _id is None:
            _id = '(' + ', '.join(str(t) for t in terms_nonterms) + ')'
        super().__init__(terms_nonterms, _id)
    def build(self, parser_generator):
        return f"And([{','.join(t.build(parser_generator) for t in self.terms_nonterms)}], '{self._id}')"
        #s = [f"And("]
        #for i, t in enumerate(self.terms_nonterms):
        #    try:
        #        s.append(t.build(parser_generator))
        #        s.append(',')
        #    except Exception as e:
        #        print(i, t if t else 'None')
        #        raise e
        #s.pop()
        #print(s)
        #return ''.join(s)
    def _check_rule(self, parser, token_key, disable_cache_check = False):
        children = []
        for t in self.terms_nonterms:
            child_res = t.check(parser, disable_cache_check)
            if child_res is FAIL_NODE:
                #parser.seek(token_key, SEEK_SET) should be unnecessary since the calling check should reset
                # in C version, make sure to clear out children
                return child_res
            if not is_SKIP_NODE(child_res):
                children.append(child_res)
        token_cur = parser.tell()
        return Node(self, token_key, token_cur - token_key, parser[token_cur].start - parser[token_key].start, children)

class LongChoice(ChainedRule):
    __slots__ = tuple()
    def __init__(self, terms_nonterms, _id = None):
        if _id is None:
            _id = '(' + ' | '.join(str(t) for t in terms_nonterms) + ')'
        super().__init__(terms_nonterms, _id)
    def build(self, parser_generator):
        #print([type(t) for t in self.terms_nonterms])
        return f"LongChoice([{','.join(t.build(parser_generator) for t in self.terms_nonterms)}], '{self._id}')"
    def _check_rule(self, parser, token_key, disable_cache_check = False):
        node = FAIL_NODE
        for t in self.terms_nonterms:
            child_res = t.check(parser, disable_cache_check)
            if child_res.length > node.length:
                node = child_res
            parser.seek(token_key, SEEK_SET)
        #print("long choice:", token_key, parser.tell(), node.ntokens)
        parser.seek(node.ntokens, SEEK_CUR)
        #print("long choice:", token_key, parser.tell(), node.ntokens)
        return node

class FirstChoice(ChainedRule):
    __slots__ = tuple()
    def __init__(self, terms_nonterms, _id = None):
        if _id is None:
            _id = '(' + ' / '.join(str(t) for t in terms_nonterms) + ')'
        super().__init__(terms_nonterms, _id)
    def build(self, parser_generator):
        return f"FirstChoice([{','.join(t.build(parser_generator) for t in self.terms_nonterms)}], '{self._id}')"
    def _check_rule(self, parser, token_key, disable_cache_check = False):
        for t in self.terms_nonterms:
            child_res = t.check(parser, disable_cache_check)
            if child_res is not FAIL_NODE:
                return child_res
        return FAIL_NODE
    
BINARY_OP_RULES = [And, FirstChoice, LongChoice]

RE_GEN_TO_ESC = {'.', '^', '$','*', '+', '?', '(', ')', '[', '{', '\\', '|'}
def simple_string_to_regex(string):
    s_out = []
    for c in string:
        if c in RE_GEN_TO_ESC:
            s_out.append('\\')
        s_out.append(c)
    return ''.join(s_out)

# Abstract Class
class LiteralRule(Rule):
    __slots__ = ("regex",)
    def __init__(self, _id, regex):
        super().__init__(_id)
        self.regex = regex
    def build(self, parser_generator):
        return parser_generator.resolve_name(self._id)
    def _check_rule(self, parser, token_key, disable_cache_check = False):
        #print(f"\tgrabbing key {token_key} in Literal {self._id}", end = '...')
        token = parser[token_key]
        if len(token) == 0:
            return FAIL_NODE
        #print(self._id, ':', token)
        m = self.regex.match(token.string, token.start, token.end)
        if self._id == "[^\()]*":
            print(self._id, "None" if m is None else m, token.string[token.start:token.end])
        if m:
            parser.seek(1, SEEK_CUR)
            #print(f"final key {parser.tell()}")
            length = m.end() - m.start()
            return Node(self, token_key, 1 if length else 0, length, None)
        #print(f"final key {parser.tell()}")
        return FAIL_NODE

class StringRule(LiteralRule):
    __slots__ = tuple()
    def __init__(self, _id):
        super().__init__(_id, re.compile(simple_string_to_regex(_id), flags = re.DOTALL))

# punctuation rules
DASH = StringRule('-')
MINUS = DASH
COMMA = StringRule(',')
COLON = StringRule(':')
BSLASH = StringRule('\\')
FSLASH = StringRule('/')
VBAR = StringRule('|')
BITOR = VBAR
LOGOR = StringRule('||')
BITAND = StringRule('&')
LOGAND = StringRule('&&')
DIV = FSLASH
MOD = StringRule('%')
PERCENT = MOD
BANG = StringRule('!')
SHEBANG = StringRule('#!')
LOGNOT = BANG
BITNOT = StringRule('~')
BITXOR = StringRule('^')
SEMICOLON = StringRule(';')
UNDERSCORE = StringRule('_')
LSHIFT = StringRule('<<')
RSHIFT = StringRule('>>')
EQUALS = StringRule('=')
POUND = StringRule('#')
PLUS = StringRule('+')
DEQUALS = StringRule('==')
TEQUALS = StringRule('===')
DEFEQUALS = StringRule(':=')
NEQUALS = StringRule('!=')
MULTEQUALS = StringRule('*=')
DIVEQUALS = StringRule('/=')
MODEQUALS = StringRule('%=')
PLUSEQUALS = StringRule('+=')
MINUSEQUALS = StringRule('-=')
LSHIFTEQUALS = StringRule('<<=')
RSHIFTEQUALS = StringRule('>>=')
ANDEQUALS = StringRule('&=')
XOREQUALS = StringRule('^=')
OREQUALS = StringRule('|=')
LBRACE = StringRule('{')
RBRACE = StringRule('}')
LPAREN = StringRule('(')
RPAREN = StringRule(')')
LBRKT = StringRule('[')
RBRKT = StringRule(']')
PERIOD = StringRule('.')
DOT = PERIOD
ELLIPSIS = StringRule('...')
LANGLE = StringRule('<')
RANGLE = StringRule('>')
LESSER = LANGLE
GREATER = RANGLE
ARROW = StringRule('->')

class RegexRule(LiteralRule):
    __slots__ = tuple()
    def __init__(self, _id):
        super().__init__(_id, re.compile(_id, flags = re.DOTALL))

class NamedProduction(Rule):
    __slots__ = tuple()
    def __init__(self, _id):
        super().__init__(_id)
    def build(self, parser_generator):
        name = parser_generator.resolve_name(self._id)
        if name is None:
            raise ValueError(f"Could not resolve named production \"{self._id}\"...none found")
        return name
    # shouldn't have to implemented _check_rule as this would be a grammar error if it still exists in generated parser

# Abstract Class
class DerivedRule(Rule):
    INDICATOR = ''
    __slots__ = ("rule")
    def __init__(self, rule):
        super().__init__(f"{self.INDICATOR}{rule}")
        self.rule = rule
    def clear_cache(self, token):
        if token in self._cache:
            self._cache.pop(token)
            self.rule.clear_cache(token)

class List(DerivedRule):
    INDICATOR = '.'
    __slots__ = ("delim",)
    def __init__(self, rule, delimiter):
        super().__init__(rule)
        self._id = str(delimiter) + str(self)
        self.delim = delimiter # this is a StringLiteralRule Instance
        #print(self._id, self.delim, type(self.delim))
    def build(self, parser_generator):
        return f"List({self.rule.build(parser_generator)}, {self.delim.build(parser_generator)})"
    def _check_rule(self, parser, token_key, disable_cache_check = False):
        node = self.rule.check(parser, disable_cache_check)
        if node is FAIL_NODE:
            return node
        node_list = [node]
        #print(self._id, self.delim)
        while True:
            delim = self.delim.check(parser, disable_cache_check)
            if delim is FAIL_NODE:
                break
            node_list.append(delim)
            node = self.rule.check(parser, disable_cache_check)
            if node is FAIL_NODE:
                # undo delim
                parser.seek(-delim.ntokens, SEEK_CUR)
                break
            node_list.append(node)
        token_cur = parser.tell()
        return Node(self, token_key, token_cur - token_key, parser[token_cur].start - parser[token_key].start, node_list)
    def clear_cache(self, token):
        if token in self._cache:
            self._cache.pop(token)
            self.delim.clear_cache(token)
            self.rule.clear_cache(token)

class Repeat(DerivedRule):
    __slots__ = ("min_rep", "max_rep")
    def __init__(self, rule, min_rep, max_rep):
        super().__init__(rule)
        self._id = f"{self}{{{min_rep if min_rep else 0}:{str(max_rep) if max_rep else ''}}}"
        self.min_rep = min_rep
        self.max_rep = max_rep # <= 0 means infinite
    def build(self, parser_generator):
        return f"Repeat({self.rule.build(parser_generator)}, {self.min_rep}, {self.max_rep})"
    def _check_rule(self, parser, token_key, disable_cache_check = False):
        #print(self, '\n', self.rule)
        node = self.rule.check(parser, disable_cache_check)
        ct = 0
        node_list = []
        while node is not FAIL_NODE:
            ct += 1
            node_list.append(node)
            node = self.rule.check(parser, disable_cache_check)
        if ct < self.min_rep or (self.max_rep and ct > self.max_rep):
            #parser.seek(token_key, SEEK_SET) # should be unnecessary since calling check should reset from FAIL_NODE
            return FAIL_NODE
        token_cur = parser.tell()
        return Node(self, token_key, token_cur - token_key, parser[token_cur].start - parser[token_key].start, node_list)
    
class Optional(DerivedRule):
    __slots__ = ()
    def __init__(self, rule):
        super().__init__(rule)
        self._id = f"{self}?"
    def build(self, parser_generator):
        return f"Optional({self.rule.build(parser_generator)})"
    def _check_rule(self, parser, token_key, disable_cache_check = False):
        child = []
        node = self.rule.check(parser, disable_cache_check)
        if node is not FAIL_NODE:
            child.append(node)
        return Node(self, token_key, node.ntokens, node.length, child)
    
class AnonymousProduction(DerivedRule):
    __slots__ = tuple()
    def build(self, parser_generator):
        return self.rule.build(parser_generator)
    # shouldn't have to implemented _check_rule as this would be a grammar error if it still exists in generated parser
    
def build_action_default(ctxt, node): # ctxt is anything
    return node

BUILD_ACTION_DEFAULT = "build_action_default"

def traverse_action_default(ctxt, node):
    return True

TRAVERSE_ACTION_DEFAULT = "None"
#UNESCAPED_RULES = []
class Production(AnonymousProduction):
    #UNESCAPED_RULES = [StringRule, RegexRule, ]
    __slots__ = ("build_action", "build_action_name", "traverse_action", "traverse_action_name")
    def __init__(self, rule=None, name=None, build_action = None, traverse_action = None):
        super().__init__(rule)
        self._id = name
        if build_action is None:
            build_action = build_action_default
        self.build_action = build_action
        if traverse_action is None:
            traverse_action = traverse_action_default
        self.traverse_action = traverse_action
    def build(self, parser_generator):
        try:
            resolved_rule = self.rule.build(parser_generator)
        except Exception as e:
            print(f"Failed to build Production {self._id} due to rule build failure")
            raise e
        #print(self._id, self.transform)
        #print(repr(self.build_action_name))
        
        if resolved_rule is None:
            s = f"RegexRule(\"{self.rule._id}\"), \"{self._id}\""
        else:
            s = f"{resolved_rule}, \"{self._id}\""
        if self.build_action is not None:
            s += f", {self.build_action}"
        else:
            s += ", None"
        if self.traverse_action is not None:
            s += f", {self.traverse_action}"
        return s
    UNESCAPED_RULES = None
    def _check_rule(self, parser, token_key, disable_cache_check = False):
        #print("disable check:", disable_cache_check)
        #print("production:", self, '\n', self.rule)
        node = self.rule.check(parser, disable_cache_check)
        if node is not FAIL_NODE:
            #print(f"succes with {self} ({node.rule}) at {token_key}")
            #return self.build_action(parser, ProductionNode(self, node.token_key, node.ntokens, node.length, [node]))
            
            if not is_SKIP_NODE(node):
                #if not isinstance(node.rule, Production):
                if not isinstance(node.rule, Production.UNESCAPED_RULES):
                    Node.__init__(node, self, node.token_key, node.ntokens, node.length, node.children)
                else:
                    node = Node(self, node.token_key, node.ntokens, node.length, [node])

            #print(f"\tfinal node {node}")
            return self.build_action(parser, node)
        return node
Production.UNESCAPED_RULES = (Production, StringRule, RegexRule)

class NegativeLookahead(DerivedRule):
    INDICATOR = '!'
    def build(self, parser_generator):
        return f"NegativeLookahead({self.rule.build(parser_generator)})"
    def _check_rule(self, parser, token_key, disable_cache_check = False):
        result = self.rule.check(parser, disable_cache_check)
        if result is FAIL_NODE:
            return LOOKAHEAD_NODE
        parser.seek(token_key, SEEK_SET)
        return FAIL_NODE

class PositiveLookahead(DerivedRule):
    INDICATOR = '&'
    def build(self, parser_generator):
        return f"PositiveLookahead({self.rule.build(parser_generator)})"
    def _check_rule(self, parser, token_key, disable_cache_check = False):
        result = self.rule.check(parser, disable_cache_check)
        if result is not FAIL_NODE:
            parser.seek(token_key, SEEK_SET)
            return LOOKAHEAD_NODE
        return result

class ParserGenerator:
    def __init__(self, filename = None, output = 'py'):
        dir_, file = os.path.split(filename) 
        self.dir_ = dir_
        self.grammar = os.path.splitext(file)[0]
        self.export_type = output
        self.export = self.grammar # remove extension. Will add later
        self.imports = []
        self.state = PGEN_STATE_IDLE
        self.punctuators = {}
        self.keywords = {}
        self.productions = {} # dictionary of names to productions
        self.transform = {PGEN_STATE_IDLE: self._idle,
                          PGEN_STATE_WHITESPACE: self._whitespace,
                          PGEN_STATE_WORD: self._word
                          }
        if filename is not None:
            self.from_file(filename)
        else:
            self.contents = None

    def close(self): # cleanup
        if isinstance(self.contents, TextIOWrapper):
            self.contents.close()
    def _idle(self):
        #print("in idle", self.contents.tell())
        c = self.contents.peek(1)
        #print(c)
        if c in WORD:
            self.state = PGEN_STATE_WORD
        elif c in WHITESPACE:
            self.state = PGEN_STATE_WHITESPACE
        elif c == COMMENT_HINT:
            c = self.contents.peek(2)
            #print(c)
            if c == LINE_COMMENT_OPEN or c == BLOCK_COMMENT_OPEN:
                self.state = PGEN_STATE_WHITESPACE
            else:
                raise ValueError(f"syntax error at {self.contents.read(20)}.")
        elif c == '':
            self.state = PGEN_STATE_END
        else:
            raise ValueError(f"syntax error at {self.contents.read(20)}.")
        
    def _skip_whitespace(self):
        stop = False
        while not stop:
            #print("current location:", self.contents.tell())
            c = self.contents.peek(1)
            #print("current character:", c, self.contents.tell())
            if c == COMMENT_HINT:
                c = self.contents.peek(2)
                if c == LINE_COMMENT_OPEN:
                    #print("skipping line comment")
                    string, stopped = self.contents.read_until_char(LINE_COMMENT_CLOSE, include = True)
                    #print("length of comment:", len(string), string)
                elif c == BLOCK_COMMENT_OPEN:
                    #print("skipping block comment")
                    string, stopped = self.contents.read_until_string(BLOCK_COMMENT_CLOSE, include = True)
                    #print("length of block:", len(string), string)
                elif len(c) < 2: # TODO: this might actually be an error state
                    self.state = PGEN_STATE_END
                    stop = True
            elif c in WHITESPACE:
                #print("skipping whitespace")
                self.contents.read_until_char(WHITESPACE, complement = True)
            elif c == EOF:
                self.state = PGEN_STATE_END
                stop = True
            else:
                stop = True

    def _whitespace(self):
        #print("in whitespace")
        self._skip_whitespace()
        self.state = PGEN_STATE_IDLE

    def _word(self):
        #print("in word")
        string, stopped = self.contents.read_until_char(WORD, complement = True)
        self._skip_whitespace()
        #print("found word:", string)
        if string == "export":
            self._get_export()
        elif string == "import":
            self._get_import()
        elif string == "punctuator":
            self._punctuators()
        elif string == "keyword":
            self._keywords()
        elif string == "token":
            self.productions[string] = [self._get_named_production(string), string.upper()]
            self.productions[string][0].build_action = f"token_action" # this is a little hacky
        elif stopped == '':
            self.state = PGEN_STATE_END
            return
        else:
            self.productions[string] = [self._get_named_production(string), string.upper()]
        self.state = PGEN_STATE_IDLE            

    def _skip_punctuator(self, punc):
        #print("skipping punctuation:", punc)
        string = self.contents.read(len(punc))
        if string != punc:
            raise ValueError(f"syntax error: expected {punc} at {self.contents.read(20)}")            

    def _read_string_literal(self):
        string = self.contents.read(1)
        if string != "'":
            raise ValueError(f"syntax error: expected string literal at {self.contents.read(20)}")
        out = []
        string, stopped = self.contents.read_until_char(STRING_LITERAL_CLOSE)
        while string[-1] == ESCAPE_CHAR: # the double-quote was escaped
            out.append(string + "'")
            string, stopped = self.contents.read_until_char(STRING_LITERAL_CLOSE)
        out.append(string)
        if stopped == EOF:
            self.state = PGEN_STATE_END
        self.contents.read(1)
        string = ''.join(out)
        #print("found string literal:", string)
        return string
    
    def _read_regex(self):
        string = self.contents.read(1)
        if string != '"':
            raise ValueError(f"syntax error: expected regex at {self.contents.tell()}")
        out = []
        string, stopped = self.contents.read_until_char(REGEX_CLOSE)
        while string and string[-1] == ESCAPE_CHAR: # the double-quote was escaped
            out.append(string + self.contents.read(len(REGEX_CLOSE)))
            string, stopped = self.contents.read_until_char(REGEX_CLOSE)
        out.append(string)
        if stopped == EOF:
            self.state = PGEN_STATE_END
        self.contents.read(1)
        string = ''.join(out)
        #print("found string literal:", string)
        return string
    
    def _read_word(self):
        return self.contents.read_until_char(WORD, complement = True)[0]
    def _read_action(self):
        action = self.contents.read_regex(ACTION_REGEX)
        if action:
            return action
        return None
    
    def _get_export(self):
        self._skip_punctuator(PROD_DEF)
        self._skip_whitespace()
        self.export = self._read_word()
        #print(f"found export: {self.export}")

    def _get_import(self):
        self._skip_punctuator(PROD_DEF)
        self._skip_whitespace()
        string = self._read_word()
        #print(f"found import: {string}")
        self.imports.append(string)

    def _get_comma_separated_list(self):
        out = []
        string = self._read_string_literal()
        out.append(string)
        self._skip_whitespace()
        c = self.contents.peek(1)
        while c and c == ',':
            self.contents.read(1)
            self._skip_whitespace()
            string = self._read_string_literal()
            out.append(string)
            self._skip_whitespace()
            c = self.contents.peek(1)
        if c == '':
            self.state = PGEN_STATE_END
        return out

    def _punctuators(self):
        self._skip_punctuator(PROD_DEF)
        self._skip_whitespace()
        puncs = self._get_comma_separated_list()
        for punc in puncs:
            self.punctuators[punc] = [StringRule(punc), '_'.join(["PUNC"] + [str(ord(c)) for c in punc])]
        self.productions["punctuator"] = [Production(RegexRule('|'.join('(' + simple_string_to_regex(s) + ')' for s in puncs)), "punctuator", BUILD_ACTION_DEFAULT, TRAVERSE_ACTION_DEFAULT), "PUNCTUATOR"]

    def _keywords(self):
        self._skip_punctuator(PROD_DEF)
        self._skip_whitespace()
        keys = self._get_comma_separated_list()
        for key in keys:
            self.keywords[key] = [StringRule(key), key.upper()]
        self.productions["keyword"] = [Production(RegexRule('|'.join('(' + simple_string_to_regex(s) + ')' for s in keys)), "keyword", BUILD_ACTION_DEFAULT, TRAVERSE_ACTION_DEFAULT), "KEYWORD"]

    def _get_term_nonterm(self):
        c = self.contents.peek(1)
        rule = None
        if c == '"': # regex terminal
            rule = RegexRule(self._read_regex())
        elif c == "'": # string literal terminal or delimited list
            string = self._read_string_literal()
            c = self.contents.peek(1)
            if c == '.': # delimited list
                self.contents.read(1)
                elem_rule = self._get_term_nonterm()
                if elem_rule is not None:
                    rule = List(elem_rule, StringRule(string))
                else:
                    raise ValueError(f"syntax error: invalid rule for delimiter list near {self.contents.read(20)}")
            else: # string literal
                rule = StringRule(string)
        elif c == '&': # positive lookahead
            self._skip_punctuator(c)
            la_rule = self._get_term_nonterm()
            if la_rule is None:
                raise ValueError(f"syntax error: invalid rule for positive lookahead list near {self.contents.read(20)}")
            rule = PositiveLookahead(la_rule)
        elif c == '!': # negative lookahead
            self._skip_punctuator(c)
            la_rule = self._get_term_nonterm()
            if la_rule is None:
                raise ValueError(f"syntax error: invalid rule for negative lookahead list near {self.contents.read(20)}")
            rule = NegativeLookahead(la_rule)
        
        elif c == '(': # anonymous sub-production
            self._skip_punctuator(c)
            self._skip_whitespace()
            rule = self._get_production() # modify rule in place
        elif c in WORD: # sub-production
            string = self._read_word()
            #print("found NamedProduction:", string)
            rule = NamedProduction(string)
            c = self.contents.peek(1)
            if c == '.': # delimited list
                self.contents.read(1)
                delim = self._get_term_nonterm()
                if delim is not None:
                    rule = List(delim, rule)
                else:
                    raise ValueError(f"syntax error: invalid rule for delimiter list near {self.contents.read(20)}")

        # should encapsulate in another function
        if rule is not None:
            c = self.contents.peek(1)
            if c == '+':
                self._skip_punctuator(c)
                rule = Repeat(rule, 1, 0)
            elif c == '*':
                self._skip_punctuator(c)
                rule = Repeat(rule, 0, 0)
            elif c == '?':
                self._skip_punctuator(c)
                #rule = Repeat(rule, 0, 1)
                rule = Optional(rule)
            elif c == '{':
                self._skip_punctuator(c)
                self._skip_whitespace()
                val = self._read_word()
                if not val:
                    min_rep = 0
                else:
                    min_rep = int(val)
                self._skip_whitespace()
                self._skip_punctuator(PROD_DEF)
                self._skip_whitespace()
                val = self._read_word()
                if not val:
                    max_rep = -1
                else:
                    max_rep = int(val)
                self._skip_whitespace()
                self._skip_punctuator('}')
                rule = Repeat(rule, min_rep, max_rep)
        return rule
    
    def _get_binary_operator(self):
        op = None
        c = self.contents.peek()
        if c in BINARY_OP:
            op = BINARY_OP[self.contents.read(1)]
        elif c == ')':
            self.contents.read(1)
        # searches for ',', '|', '\\' else None. if ')' is found, it is consumed but returns None
        return op
    
    # this is basically a shunting yard to collapse a sequence of binary operations with equivalent n-ary operators into their respective n-ary operations
    def _reorg_production(self, binary_ops, terms_nonterms):
        if not binary_ops:
            return terms_nonterms[0]
        op_stack = [binary_ops.pop()]
        term_stack = [[terms_nonterms.pop()]]
        while binary_ops and op_stack:
            #print(op_stack, term_stack)
            if binary_ops[-1] == op_stack[-1]:
                binary_ops.pop()
                term_stack[-1].append(terms_nonterms.pop())
            elif binary_ops[-1] < op_stack[-1]:
                op_stack.append(binary_ops.pop())
                term_stack.append([terms_nonterms.pop()])
            else: # binary_ops[-1] > op_stack[-1]
                # a lower precedence operator is found. Complete the current op on the stack
                term_stack[-1].append(terms_nonterms.pop())
                next_op = binary_ops.pop()
                while op_stack and op_stack[-1] < next_op:
                    cur_op = op_stack.pop() # discard the result of this operation
                    terms = term_stack.pop()
                    terms.reverse()
                    if op_stack:
                        if op_stack[-1] < next_op:
                            term_stack[-1].append(BINARY_OP_RULES[cur_op](terms))
                        elif op_stack[-1] > next_op:
                            term_stack.append([terms])
                            op_stack.append(next_op)
                        else: # op_stack[-1] == next_op
                            term_stack[-1].append(BINARY_OP_RULES[cur_op](terms))
                    else:
                        term_stack.append([BINARY_OP_RULES[cur_op](terms)])
                        op_stack.append(next_op)
        
        # collapse remainder of term_stack
        term_stack[-1].append(terms_nonterms.pop())
        terms = term_stack.pop()
        terms.reverse()
        if term_stack:
            while len(term_stack):
                term_stack[-1].append(BINARY_OP_RULES[op_stack.pop()](terms))
                term_stack[-1].reverse()
                terms = term_stack.pop()
        #print(term_stack)            
        return BINARY_OP_RULES[op_stack.pop()](terms)

    def _get_production(self, name = None, build_action = None, traverse_action = None):
        binary_ops = deque([])
        terms_nonterms = deque([])
        #print("getting production", production_obj)
        term_nonterm = self._get_term_nonterm()
        if term_nonterm is None:
            raise ValueError(f"syntax error: expecting term in production near {self.contents.read(20)}, no first term found")
        terms_nonterms.append(term_nonterm)
        #print("term_nonterm:", term_nonterm)
        self._skip_whitespace()
        op = self._get_binary_operator()
        while op is not None:
            #print("op:", op)
            binary_ops.append(op)
            self._skip_whitespace()
            term_nonterm = self._get_term_nonterm()
            if term_nonterm is None:
                raise ValueError(f"syntax error: expecting term or nonterm in production near {self.contents.read(20)}")
            #print("term_nonterm:", term_nonterm)
            terms_nonterms.append(term_nonterm)
            self._skip_whitespace()
            op = self._get_binary_operator()
        rule = self._reorg_production(binary_ops, terms_nonterms)
        #print(f"production {name}:", type(rule))
        if name is not None:
            return Production(rule, name, build_action, traverse_action)
        return AnonymousProduction(rule)
        
    def _get_named_production(self, name):
        #print("handling named production:", production_obj)
        c = self.contents.peek(1)
        build_action = BUILD_ACTION_DEFAULT
        traverse_action = TRAVERSE_ACTION_DEFAULT
        if c == TRANSFORM_OPEN:
            self.contents.read()
            self._skip_whitespace()
            #build_action = self._read_word()
            build_action = self._read_action()
            if not build_action:
                build_action = BUILD_ACTION_DEFAULT
            #print("found action:", build_action)
            s, c = self.contents.read_until_char(',)', include = True)
            if c == ',':
                self._skip_whitespace()
                traverse_action = self._read_action()
                if not traverse_action:
                    traverse_action = TRAVERSE_ACTION_DEFAULT
                self.contents.read_until_char(',)', include = True)
            self._skip_whitespace()
        self._skip_punctuator(PROD_DEF)
        self._skip_whitespace()
        return self._get_production(name, build_action, traverse_action)
    
    def resolve_name(self, _id):
        if _id in self.punctuators:
            #return f"{self.list_name}[{self.punctuators[_id][2]}]"
            return self.punctuators[_id][1]
        elif _id in self.keywords:
            #return f"{self.list_name}[{self.keywords[_id][2]}]"
            return self.keywords[_id][1]
        elif _id in self.productions:
            #return f"{self.list_name}[{self.productions[_id][2]}]"
            return self.productions[_id][1]
        #print(f"could not resolve {_id}")
        #raise ValueError(f"Could not resolve name {_id}")
        return None # this is a failure
    
    def build_parser(self):
        parser_file = []
        all_string = []
        #enums = [f"{self.list_name} = [-1 for it in range({self._enum_ct})]"]
        if not "root" in self.productions:
            print("root production not provided.")
            return
        auto_traverse = self.productions["root"][0].traverse_action is not TRAVERSE_ACTION_DEFAULT
        #print(auto_traverse)

        # declare and define the punctuators and keywords first
        for k, v in self.punctuators.items():
            #enums.append(f"{v[2]} = {v[1]}")
            parser_file.append(f"{v[1]} = StringRule(\"{k}\")")
            all_string.append(f'"{v[1]}"')
        for k, v in self.keywords.items():
            #enums.append(f"{v[2]} = {v[1]}")
            parser_file.append(f"{v[1]} = StringRule(\"{k}\")")
            all_string.append(f'"{v[1]}"')

        # must declare all the productions first
        for k, v in self.productions.items():
            #enums.append(f"{v[2]} = {v[1]}")
            parser_file.append(f"{v[1]} = Production(name = \"{k}\")")
            all_string.append(f'"{v[1]}"')

        declaration_module = self.export + '_'
        with open(os.path.join(self.dir_, declaration_module) + '.' + self.export_type, 'w') as file_out:
            file_out.write("# This is automatically generated code. Do not modify\n")
            file_out.write(f"from {__name__} import *\n")
            file_out.write('\n'.join(parser_file))
            file_out.write(f"""\n
class {self.export}Parser(Parser):
    def __init__(self, string, *args, **kwargs):
        super().__init__(string, TOKEN, ROOT, *args, auto_traverse={auto_traverse}, **kwargs)
""")
            all_string.append(f'"{self.export}Parser"')
            file_out.write(f"__all__ = [{','.join(all_string)}]\n")
        parser_file.clear()

        for k, v in self.productions.items():
            #enums.append(f"{v[2]} = {v[1]}")
            parser_file.append(f"Production.__init__({v[1]}, {v[0].build(self)})")

        with open(os.path.join(self.dir_, self.export + '.') + self.export_type, 'w') as file_out:
            file_out.write("# This is automatically generated code. Do not modify\n")
            file_out.write(f"from {__name__} import *\n")
            for import_ in self.imports:
                file_out.write(f"from {import_} import *\n")
            file_out.write(f"from {declaration_module} import *\n")
            file_out.write('\n'.join(parser_file))

    def generate_parser(self):
        #t = time.time()
        
        # do stuff
        ctxt = None
        while self.state != PGEN_STATE_END:
            self.transform[self.state]()
        self.close()

        self.build_parser()
        #t = time.time() - t
        #print("execution time with StringSource:", t)
    def from_string(self, grammar):
        self.contents = grammar
        self.generate_parser()
    def from_file(self, filename):
        with open(filename, 'r') as file_in:
            self.from_string(StringSource(file_in.read()))

def traverse_action_print(ctxt, node):
    level = ctxt[1].pop()
    if node.ntokens:
        ctxt[0].append(DEFAULT_INDENTATION * level + str(node))
    for child in node:
        ctxt[1].append(level + 1)

# any parser will inherit from this
class Parser:
    def __init__(self, string, token_rule, root_rule, auto_traverse = False, line_offset = 0, col_offset = 0, lazy_parse = False, logfile = None):
        self.token_rule = token_rule
        self.root_rule = root_rule
        self._loc = 0 # this is the token_key number
        self.tokens = [Token(string, 0, len(string), line_offset, col_offset)] # offsets in line and column in case parsing a template string in the middle of a file
        self.auto_traverse = auto_traverse
        self.longest_rule = []
        self.longest_loc = 0
        self.disable_cache_check = False
        self._log = None if logfile is None else []
        self.logfile = logfile
        self.ast = None
        if not lazy_parse:
            self.parse()
    def __iter__(self):
        return iter(self.tokens)
    def tell(self):
        return self._loc
    # TODO: should check that locations make sense with respect to origin
    def seek(self, loc, origin = SEEK_SET):
        if origin == SEEK_SET:
            #print("\tseeking relative to start:", loc, self._loc)
            self._loc = loc
        elif origin == SEEK_CUR:
            #print("\tseeking relative to loc:", loc, self._loc)
            self._loc += loc
        else: # SEEK_END
            self._loc = self.tokens[-1].end + loc
    # for general logging
    def log(self, loc, rule, res):
        if self._log is not None:
            token_str = str(self[loc])
            self._log.append(' - '.join([str(rule), "Succeeded" if res is not FAIL_NODE else "Failed", str(loc) + "-"+str(loc + res.ntokens), token_str[:min(len(token_str), 20)]]))
        if res is FAIL_NODE:
            self._log_check_fail(loc, rule)
    # for stack trace
    def _log_check_fail(self, loc, rule):
        if loc >= self.longest_loc: # if just '>' then it will always show tokenization rule
            self.longest_loc = loc
            self.longest_rule.clear()
            self.longest_rule.append(rule)
        else:
            self.longest_rule.append(rule)

    def _get_line_col_end(self, token): # need to record the overall line positions for retrieving lines
        #print(str(token))
        string = token.string
        start = token.start
        end = token.end
        line = token.line
        loc = string.find('\n', start, end)
        while loc >= 0:
            #print(loc)
            line += 1
            start = loc + 1
            loc = string.find('\n', start, end)
        col = end - start
        if line == token.line: # no change
            col += token.col
        return line, col
    def _gen_final_token(self, node):
        # a new token represented by node is found. clear fail log to distinguish tokenization failure from syntax failure
        self.longest_rule.clear()
        # generate a new final_token/remaining string
        final_token = self.tokens[-1]
        end = final_token.end
        final_token.end = final_token.start + node.length
        start = final_token.end
        line, col = self._get_line_col_end(final_token)
        return Token(final_token.string, start, end, line, col)
    def skip_token(self, node):
        new_token = self._gen_final_token(node)
        self.tokens.pop()
        self.tokens.append(new_token)
    def add_token(self, node):
        #print("adding token")
        new_token = self._gen_final_token(node)
        self.tokens.append(new_token)
    def _gen_next_token(self, key):
        # throw away the result...C version has to clean it up
        self.disable_cache_check = True
        #print("_gen_next_token:", key, self._loc)
        res = self.token_rule.check(self, disable_cache_check = True)
        #print("result of token:", res, res[0])
        #print(res[0], is_SKIP_NODE(res[0]))
        #if not is_SKIP_NODE(res[0]):
            #print("next token:", repr(str(self.tokens[res.token_key])), " - key/loc:", key, self._loc)
        if len(self.tokens[-1]):
            self.disable_cache_check = False
        else:
            #print("permanently disable cache")
            pass
        return res is not FAIL_NODE
    def __getitem__(self, key):
        # need to handle if this doesn't return
        #print(f"key request {key}, length {len(self.tokens)}")
        if not self.disable_cache_check:
            #print("enabled_check_cache")
        #    while key > len(self.tokens) - 1 and self._gen_next_token():
        #        pass
        #else:
            while key >= len(self.tokens) - 1:
                #print("generating next token", key, self._loc)
                #print(f"key request {key}, length {len(self.tokens)}, final_string: {repr(str(self.tokens[-1]))}, token_length: {len(self.tokens[-1])}")
                if len(self.tokens[-1]) == 0 or not self._gen_next_token(key):
                    #print("breaking search")
                    break
                #if len(self.tokens) > 1:
                #    print("built token:", str(self.tokens[-2]))
        else:
            #print("disabled_check_cache")
            pass
        #while key >= len(self.tokens) - 1 and self._gen_next_token():
        #    pass
        #print(self.tokens[key])
        #print(key, len(self.tokens))
        try:
            return self.tokens[key]
        except IndexError as e:
            print(key)
            exit(0)
    def get_tokens(self, node):
        return [self[i] for i in range(node.token_key, node.token_key + node.ntokens)]
    def parse(self):
        #print(self[0], self._loc)
        #self._loc += 1
        #print(self[1], self._loc)
        #self._loc += 1
        #print(self[2], self._loc)
        #t = time.time()
        self.ast = self.root_rule.check(self)
        #t = time.time() - t
        #print("parse time:", t, "seconds")
        if self.ast is FAIL_NODE or self.ast.ntokens < len(self.tokens)-1:
            print("parsing failed", self.longest_loc, repr(str(self.tokens[self.ast.ntokens-1])))
            #for rule in reversed(self.longest_rule):
            #    print(rule)
        else:
            if self.auto_traverse:
                self.traverse()

        # recursively clear caches to reclaim memory
        #t = time.time()
        for token in self.tokens:
            self.root_rule.clear_cache(token)
            self.token_rule.clear_cache(token)
        #t = time.time() - t
        #print("cache clearing time:", t, "seconds")        
        #if self.logfile:
            #print("writing log file")
        if self._log:
            #print("writing log")
            #t = time.time()
            with open(self.logfile, 'w') as file_out:
                file_out.write('\n'.join(self._log))
                file_out.write('\n[')
                out = []
                l = 4
                for i, tok in enumerate(self):
                    s = '(' + repr(str(tok))+ ',' + str(i) + ')'
                    sl = len(s) + 1
                    if l + sl > 1000:
                        out.append('\n    ')
                        l = 0
                    out.append(s)
                    out.append(',')
                    l += sl
                out.pop() # pop last comma
                file_out.write(''.join(out))
                file_out.write(']\n')
            #t = time.time() - t
            #print("logging time:", t, "seconds")
    def check_cache(self, rule):
        cache_loc = (rule, self.tell())
        if cache_loc in self._cache:
            res = self._cache[cache_loc]
            self.seek(res.ntokens, SEEK_CUR) # this works even for FAIL_NODE since ntokens must be 0
        return res
    
    # for default traverse action
    def traverse(self, traverse_action = None, ctxt = None, order = TRAVERSE_PREORDER):
        if order != TRAVERSE_PREORDER:
            raise NotImplementedError("non-level_order traversals are not yet implemented")
        if traverse_action is not None:
            if order == TRAVERSE_PREORDER:
                stack = [self.ast]
                while stack:
                    node = stack.pop()
                    #print(node)
                    try:
                        traverse_action(ctxt, node)
                    except Exception as e:
                        print(ctxt)
                        print(node)
                        raise e
                    for child in reversed(node):
                        stack.append(child)
        else: # action is None, use user defined actions on Productions. Skip those visited
            if ctxt is None:
                ctxt = self
            stack = [self.ast]
            while stack:
                node = stack.pop()
                if node.traverse_action(ctxt): # if traverse returns a non-False answer, continue traversal down node
                    for child in reversed(node):
                        stack.append(child)
    
    def print_ast(self):
        ctxt = [["AST:"], deque([0])]
        self.traverse(traverse_action_print, ctxt)
        #out = []
        #self.ast.print(out)
        #print('\n'.join(out))
        return '\n'.join(ctxt[0])