        
from c_ import *
from peggen.peggen_ import SEEK_SET, SEEK_CUR, Node, Repeat, And, Production, Token
import os, copy

# for int completion, if type ends in 'unsigned', 'signed', 'long', or 'short', append 'int' to type description.
# if first is 'long', 'int', or 'short', prepend with 'signed'

# Special Tokens. Do not modify
POINTER_TOKEN = Token("*", 0, 1)
UNSIGNED_TOKEN = Token("unsigned", 0, 8)
SIGNED_TOKEN = Token("signed", 0, 6)
CONST_TOKEN = Token("const", 0, 5)
NULL_TOKEN = Token("NULL", 0, 4)
BOOL_TOKEN = Token("_Bool", 0, 5)
VOID_TOKEN = Token("void", 0, 4)
INT_TOKEN = Token("int", 0, 3)
SHORT_TOKEN = Token("short", 0, 5)
LONG_TOKEN = Token("long", 0, 4)
FLOAT_TOKEN = Token("float", 0, 5)
DOUBLE_TOKEN = Token("double", 0, 5)
CHAR_TOKEN = Token("char", 0, 4)

# this interface needs to change and probably expand significantly. Needs
# to cover all possible types of expressions
BOOL_UNKNOWN = -1
BOOL_FALSE = 0
BOOL_TRUE = 1
# consider possibly having a __slot__ for each type of constant to know when the result is a constant expression
class ExpressionResult:
    __slots__ = ("tokens", "type", "arb_value", "bool_result") # TODO: arb_value needs to go away
    def __init__(self, tokens = None, type_ = None, bool_result = BOOL_UNKNOWN):
        self.tokens = tokens
        self.type = type_
        self.arb_value = None
        self.bool_result = bool_result
    def build(self, *args, **kwargs):#
        return ExpressionResult(*args, **kwargs)

class ConstExpression(ExpressionResult):
    __slots__ = ()
    def build(self, *args, **kwargs):#
        return ConstExpression(*args, **kwargs)
    


class Object: # c object NOT python 'object'
    __slots__ = ("attributes", "storage_class", "type", "identifier")
    def __init__(self, attributes = None, storage_class = None, type_ = None, identifier = None):
        self.attributes = attributes
        self.storage_class = storage_class
        self.type = type_
        self.identifier = identifier
    def from_DeclSpec(self, decl_spec):
        self.attributes = decl_spec.attrs
        self.storage_class = decl_spec.storage_class
        self.type = Type(TypeSpecQual(decl_spec.specifiers, decl_spec.qualifiers))
        self.identifier = None
    def __copy__(self):
        return Object(copy.copy(self.attributes), copy.copy(self.storage_class), copy.copy(self.type), copy.copy(self.identifier))
    def __str__(self):
        return str(self.type) + (str(self.identifier) if self.identifier else "(no id)")

class Callable(Object):
    __slots__ = ("function_specifiers",)
    def __init__(self, attributes = None, storage_class = None, type_ = None, identifier = None, function_specifiers = None):
        super().__init__(attributes, storage_class, type_, identifier)
        self.function_specifiers = function_specifiers
    def from_DeclSpec(self, decl_spec):
        super().from_DeclSpec(decl_spec)
        self.function_specifiers = decl_spec.func_spec
    def __copy__(self):
        return Object(copy.copy(self.attributes), copy.copy(self.storage_class), copy.copy(self.type), copy.copy(self.identifier))

class Parameter(Object):
    __slots__ = ()
    def __init__(self, type_ = None, identifier = None):
        super().__init__([], [], type_, identifier)

class Member(Object): 
    __slots__ = ("size",) # size == None means non-bitfield
    def __init__(self, type_ = None, identifier = None, size = None):
        super().__init__([], [], type_, identifier)
        self.size = size

class BaseSubType:
    __slots__ = ("tokens",)
    def __init__(self, tokens = None):
        self.tokens = tokens if tokens is not None else []
    def is_compatible(self, other):
        return False
    def __copy__(self):
        return BaseSubType(self.tokens[:])
    def unqualify(self):
        return copy.copy(self)
    def __str__(self):
        return ' '.join(t if isinstance(t, str) else str(t) for t in self.tokens)
    
BOOL_BST = BaseSubType([BOOL_TOKEN])
VOID_BST = BaseSubType([VOID_TOKEN])
INT_BST = BaseSubType([INT_TOKEN])
UINT_BST = BaseSubType([UNSIGNED_TOKEN, INT_TOKEN])
SHORT_BST = BaseSubType([SHORT_TOKEN])
USHORT_BST = BaseSubType([UNSIGNED_TOKEN, SHORT_TOKEN])
LONG_BST = BaseSubType([LONG_TOKEN])
ULONG_BST = BaseSubType([UNSIGNED_TOKEN, LONG_TOKEN])
LLONG_BST = BaseSubType([LONG_TOKEN, LONG_TOKEN])
ULLONG_BST = BaseSubType([UNSIGNED_TOKEN, LONG_TOKEN, LONG_TOKEN])
FLOAT_BST = BaseSubType([FLOAT_TOKEN])
DOUBLE_BST = BaseSubType([DOUBLE_TOKEN])
CHAR_BST = BaseSubType([CHAR_TOKEN])
UNSIGNED_CHAR_BST = BaseSubType([UNSIGNED_TOKEN, CHAR_TOKEN])
SIGNED_CHAR_BST = BaseSubType([SIGNED_TOKEN, CHAR_TOKEN])
SIZE_T_BST = BaseSubType([Token("size_t", 0, 6, 0, 0)]) # modify in place based on implementation of size_t on the target
WCHAR_T_BST = BaseSubType([Token("wchar_t", 0, 6, 0, 0)]) # modify in place based on implementation of size_t on the target

# questionable whether this should really be a BaseSubType. Doesn't really make sense
# TODO: need to get size to work that once a type is defined, determine its size
class Type(BaseSubType):
    __slots__ = ("type_spec_quals",     # TypeSpecQual
                 "derived", # stack of derived type 
                 "size",
                 "align",) 
    def __init__(self, type_spec_quals = None, derived_types = None, size = 0, align = 0):
        super().__init__(None)
        self.type_spec_quals = type_spec_quals
        self.derived = derived_types if derived_types is not None else []
        self.size = size
        self.align = align
    def is_compatible(self, other):
        pass
    def __copy__(self):
        return Type(copy.copy(self.type_spec_quals), [copy.copy(d) for d in self.derived])
    def unqualify(self): 
        # creates a new type where the qualifiers have been removed
        return Type(self.type_spec_quals.unqualify(), [d.unqualify() for d in self.derived])
    def __str__(self):
        #this should unroll the derived stack
        #print("number of derived types:", len(self.derived))
        #for d in self.derived:
        #    print(d)
        return str(self.type_spec_quals) + ' ' + ' '.join(str(d) for d in self.derived)
    def indirection(self):
        if not self.derived:
            return FAIL_TYPE
        top = self.derived[-1]
        if not isinstance(top, (IndexedType, PointerType)):
            return FAIL_TYPE
        out = copy.copy(self)
        out.derived.pop()
        return out
    def address(self, line = 0, col = 0):
        # should really track/check if object is lvalue
        out = copy.copy(self)
        out.derived.append(PointerType([POINTER_TOKEN]))
    def call(self, params):
        if not self.derived:
            return FAIL_TYPE
        top = self.derived[-1]
        callable = False
        if isinstance(top, ParameterizedType):
            callable = True
        elif len(self.derived) > 1 and isinstance(top, PointerType) and isinstance(self.derived[-2], ParameterizedType):            
            self.derved.pop()
            callable = True
        else:
            return FAIL_TYPE
        if callable:
            # check param types. if not compatible, return FAIL_TYPE
            # if compatible, return Return type, which is just popping the last declarator off the top of self.derived
            pass
        raise NotImplementedError("calling a type not yet implemented")

class TypeDef(BaseSubType):
    __slots__ = ("type", ) # tokens are the identifier
    def __init__(self, identifier = None, type = None):
        super().__init__([identifier])
        self.type = type
    def __str__(self):
        return str(self.tokens[0]) + "(aka " + str(self.type) + ")"

class TypeSpecQual:
    __slots__ = ("base_subtype", "quals") # tokens maps to type specifiers, quals maps to its qualifiers
    def __init__(self, base_subtype, qualifiers = None):
        self.base_subtype = base_subtype # A BaseSubType
        self.quals = qualifiers if qualifiers is not None else []
    def __copy__(self):
        return TypeSpecQual(self.tokens[:], self.quals[:])
    def unqualify(self):
        return TypeSpecQual(self.tokens[:], [])
    def __str__(self):
        return str(self.base_subtype) + ' ' + ' '.join(str(t) for t in self.quals)

FAIL_TYPE = Type()
SIZE_T_TYPE = Type(TypeSpecQual(SIZE_T_BST))
WCHAR_T_TYPE = Type(TypeSpecQual(WCHAR_T_BST))

WCHAR_T_TYPEDEF = TypeDef("wchar_t", WCHAR_T_TYPE)
SIZE_T_TYPEDEF = TypeDef("size_t", SIZE_T_TYPE)

class StructUnion(BaseSubType):
    __slots__ = ("members", "modifiable") # empty member list is incomplete struct
    def __init__(self, struct_union, identifier = None, members = None, modifiable = True):
        if identifier:
            struct_union.append(identifier)
        super().__init__(struct_union)
        self.members = members if members is not None else [] # may not be None, may be empty, but then it is incomplete
        self.modifiable = modifiable
    def complete(self, members):
        if self.members or not members:
            return FAIL_TYPE
        out = copy.copy(self)
        out.members = members
        return out
    def __str__(self):
        #print(len(self.tokens))
        return super().__str__() + ' {\n\t' + ',\n\t'.join(str(m) for m in self.members) + "}"
    
class StructSpec(StructUnion):
    __slots__ = ()
    def __copy__(self):
        struct = self.tokens[0]
        identifier = None
        if len(self.tokens) > 1:
            identifier = self.tokens[1]
        return StructSpec(struct, copy.copy(self.quals), identifier, [copy.copy(m) for m in self.members])
    
class UnionSpec(StructUnion):
    __slots__ = ()
    def __copy__(self):
        union = self.tokens[0]
        identifier = None
        if len(self.tokens) > 1:
            identifier = self.tokens[1]
        return UnionSpec(union, copy.copy(self.quals), identifier, [copy.copy(m) for m in self.members])

class EnumSpec(BaseSubType):
    __slots__ = ("constants", ) # constants is a dict mapping identifiers to integers
    def __init__(self, enum, identifier = None, constants = None):
        if identifier:
            enum.append(identifier)
        super().__init__(enum)
        self.constants = constants if constants is not None else {}
    def complete(self, constants):
        if self.constants or not constants:
            return FAIL_TYPE
        out = copy.copy(self)
        out.constants = constants
        return out
    def __copy__(self):
        enum_token = self.tokens[0]
        identifier = None
        if len(self.tokens) > 1:
            identifier = self.tokens[1]
        return EnumSpec(enum_token, copy.copy(self.quals), identifier, copy.copy(self.constants))
    def __str__(self):
        #print(len(self.tokens))
        return super().__str__() + ' {\n\t' + ',\n\t'.join(str(k) + " = " + str(v) for k, v in self.constants.items()) + "}"

class PointerType(TypeSpecQual):
    __slots__ = ("quals", "attrs")
    def __init__(self, pointer_tokens, quals = None, attrs = None):
        super().__init__(BaseSubType(pointer_tokens), quals)
        self.attrs = attrs
    def __copy__(self):
        return PointerType(self.base_subtype.tokens[:], copy.copy(self.quals), copy.copy(self.attrs))
    def unqualify(self):
        return PointerType(self.base_subtype.tokens[:], [], copy.copy(self.attrs))
    def __str__(self):
        return super().__str__() + ' ' + ' '.join(self.quals)
    
POINTER_TYPE = PointerType([POINTER_TOKEN])
STRING_LITERAL_TYPE = Type(TypeSpecQual(CHAR_BST, [CONST_TOKEN]), [POINTER_TYPE])
WSTRING_LITERAL_TYPE = Type(TypeSpecQual(WCHAR_T_TYPEDEF, [CONST_TOKEN]), [POINTER_TYPE])
CHAR_LITERAL_TYPE = Type(TypeSpecQual(CHAR_BST))
VOID_TYPE = Type(TypeSpecQual(VOID_BST))
BOOL_TYPE = Type(TypeSpecQual(BOOL_BST))
DOUBLE_TYPE = Type(TypeSpecQual(DOUBLE_BST))
SHORT_TYPE = Type(TypeSpecQual(SHORT_BST))
USHORT_TYPE = Type(TypeSpecQual(USHORT_BST))
INT_TYPE = Type(TypeSpecQual(INT_BST))
UINT_TYPE = Type(TypeSpecQual(UINT_BST))
LONG_TYPE = Type(TypeSpecQual(LONG_BST))
ULONG_TYPE = Type(TypeSpecQual(ULONG_BST))
LLONG_TYPE = Type(TypeSpecQual(LLONG_BST))
ULLONG_TYPE = Type(TypeSpecQual(ULLONG_BST))
NULL = Object(None, None, Type(TypeSpecQual(VOID_BST), [POINTER_TYPE]), NULL_TOKEN) # never change

SQUARE_BRACKET_TOKENS = ['[', ']']

class IndexedType(PointerType):
    __slots__ = ("size", "static")
    def __init__(self, quals = None, size = 0, static = False):
        super().__init__(quals)
        self.tokens = SQUARE_BRACKET_TOKENS
        self.size = size # 0 marks an incomplete, <0 marks VLA
        self.static = static # static means that the size is interpreted as a mininum. if static, size shall be > 0
    def complete(self, size): # somewhat paradoxically, this creates a new Type
        if self.size > 0 or size <= 0: # it's already complete or not completing
            return FAIL_TYPE
        out = copy.copy(self)
        out.size = size
        return out
    def __copy__(self):
        return IndexedType(self.quals[:], self.size, self.static)
    def __str__(self):
        return self.tokens[0] + ('static' if self.static else '') + ' '.join(self.quals) + str(self.size) + self.tokens[-1]
    def unqualify(self):
        return IndexedType([], self.size, self.static)

PARENTHESES_TOKENS = ['(', ')']

class ParameterizedType(BaseSubType):
    __slots__ = ("params", "has_ellipses")
    def __init__(self, params = None, has_ellipses = False): # params == None means no parameters specified. An empty least means no argument accepted
        super().__init__(PARENTHESES_TOKENS)
        self.params = params # params are Objects. In Function Definition, they must be Members
        self.has_ellipses = has_ellipses
    def __copy__(self):
        return ParameterizedType([copy.copy(p) for p in self.params])
    #def unqualify(self): inherits from BaseSubType
    def __str__(self):
        return self.tokens[0] + ','.join(str(p) for p in self.params) + self.tokens[-1]

CERROR_SEVERITY_INFO = 0 # no error
# warnings
CERROR_SEVERITY_USB = CERROR_SEVERITY_INFO + 1 # unspecified behavior
CERROR_SEVERITY_MEMORYWARN = CERROR_SEVERITY_USB + 1 # a potential memory issue is detected, double free, dangling pointer, non-freed memory in global scope, out of bounds read
CERROR_SEVERITY_UDB = CERROR_SEVERITY_MEMORYWARN + 1 # undefined behavior
# errors
CERROR_SEVERITY_LEXICAL = CERROR_SEVERITY_UDB + 1 # failure in tokenization
CERROR_SEVERITY_SYNTACTIC = CERROR_SEVERITY_LEXICAL + 1 # failure during parsing
CERROR_SEVERITY_SEMANTIC = CERROR_SEVERITY_SYNTACTIC + 1 # failure in interpretation or implementation of syntax
CERROR_SEVERITY_CRITICAL = CERROR_SEVERITY_SEMANTIC + 1 # detected a memory issue or other critical program failure issues, e.g. out of bounds write, null dereference, non-freed memory allocated and identifiers leaving scope
CERROR_SEVERITY_DEFAULT = CERROR_SEVERITY_LEXICAL

class CError:
    __slots__ = ("msg", "file", "line", "col", "severity") # file is optional as we may be parsing a string
    def __init__(self, msg, severity, file = "", line = -1, col = -1): # severity of 0 is breaking/will fail to compile
        self.msg = msg
        self.file = file
        self.line = line
        self.col = col
        self.severity = severity
    def set_location(self, file, line, col):
        self.file = file
        self.line = line
        self.col = col
    def __str__(self):
        if self.line >= 0:
            return self.msg + f" in {self.file}:{self.line}:{self.col}"
        return self.msg
    def get(self, threshold = CERROR_SEVERITY_DEFAULT):
        if self.severity >= threshold:
            return str(self)
        return ""

class Scope:
    def __init__(self, parent = None, name = None):
        self.parent = parent # a parent scope
        self.name = name
        self.objects = {} # maps identifiers to objects. This is the ordinary identifier name space
        self.enums = {} # maps identifiers to enum constants
        self.typedefs = {} # maps identifiers to their type definitions that are available. objects and typedefs share the same namespace so self.objects and self.typedefs must remain disjoint
        self.tags = {} # maps tag identifiers to their type definitions. This is the tag name space.
        # labels are separate because their use is separate and they only have disambiguating punctuator syntax.
        self.labels = set() # labels do not map to anything for now, so they are simply a set representing a separate namespace

    def open(self, name):
        return Scope(self, name)
    
    def cleanup(self):
        # for automatic deallocation
        return None
    
    def add_label(self, label_name):
        if label_name in self.labels:
            return self._return_namespace_conflict_error("label", label_name, True)
        self.labels.add(label_name)
        return None
    
    def add_tag(self, tag, type_):
        if tag in self.tags:
            return self._return_namespace_conflict_error("tag", tag, True, f" with type {self.tags[tag]}.")
        self.tags[tag] = type_
        return None
    
    def _check_for_conflict(self, identifier):
        if identifier in self.objects:
            return self._return_namespace_conflict_error("object", identifier, True)
        elif identifier in self.typedefs:
            return self._return_namespace_conflict_error("typedef", identifier, True, f" with type {self.typedefs[identifier]}")
        elif identifier in self.enums:
            return self._return_namespace_conflict_error("enum", identifier, True, f" with enum constant {self.enums[identifier]}")
    
    def add_object(self, identifier, object_):
        self._check_for_conflict(identifier)
        self.objects[identifier] = object_
        return None
    
    def add_enum(self, identifier, enum_constant):
        self._check_for_conflict(identifier)
        self.enums[identifier] = enum_constant
        return None
    
    def add_typedef(self, typedef_name, type_):
        self._check_for_conflict(typedef_name)
        self.typedefs[typedef_name] = type_
        return None
    
    def _check_typedef(self, type_):
        if type_ in self.typedefs:
            return self.typedefs
        if self.parent:
            return self.parent._check_typedef(type_)
        return None
    
    def is_typedef(self, type_):
        return self._check_typedef is not None
    
    def get_typedef(self, type_):
        found = self._check_typedef(type_)
        if found is not None:
            return found[type_]
        return self._return_namespace_conflict_error("typedef", type_, False)

    def _check_object(self, identifier):
        if identifier in self.objects:
            return self.objects
        if self.parent:
            return self.parent._check_object(identifier)
        return None
    
    def is_object(self, identifier):
        return self._check_object is not None
    
    def get_object(self, identifier):
        found = self._check_object(identifier)
        if found is not None:
            return found[identifier]
        return self._return_namespace_conflict_error("object", identifier, False)
    
    def _check_enum(self, identifier):
        if identifier in self.objects:
            return self.objects
        if self.parent:
            return self.parent._check_enum(identifier)
        return None
    
    def is_enum(self, identifier):
        return self._check_enum is not None
    
    def get_enum(self, identifier):
        found = self._check_enum(identifier)
        if found is not None:
            return found[identifier]
        return self._return_namespace_conflict_error("enum", identifier, False)
    
    def _return_namespace_conflict_error(self, namespace, identifier, found, additional = None):
        if found:
            return CError(f"{identifier} in {namespace} namespace of scope {self.name} already defined" + (additional if additional else "."), CERROR_SEVERITY_SYNTACTIC)
        else:
            return CError(f"{identifier} in {namespace} namespace of scope {self.name} not found" + (additional if additional else "."), CERROR_SEVERITY_SYNTACTIC)

class CParser(cParser):
    def __init__(self, filename_or_string, *args, **kwargs):
        if os.path.isfile(filename_or_string):
            self.filename = filename_or_string
            with open(filename_or_string, 'r') as file_in:
                string = file_in.read()
        else:
            self.filename = None
            string = filename_or_string
        self.scope = Scope(None, "Global")
        super().__init__(string, *args, **kwargs)  

def from_file(filename, file_out = None, *args, **kwargs):
    result = None
    with open(filename, 'r') as file_in:
        result = from_string(file_in.read(), file_out, *args, **kwargs)
    return result
    
def from_string(string, file_out = None, *args, **kwargs):
    result = CParser(string, *args, **kwargs)
    if file_out is not None:
        with open(file_out, 'w') as file_out:
            file_out.write(result.print_ast())
    #c_root(result, result.ast)
    return result

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


### C Interpretation

def c_pragma_directive(parser, node):
    print("c_pragma_directive:", node, '\n\t', node[0])

def c_compound_statement(parser, cmpd_stmt, initial_scope):
    pass

def c_function_definition(parser, node):
    print("c_function_definition not implemented yet")

def c_type_name(parser, node, type_):
    print("c_type_name not yet implemented")

# EXPRESSIONS

def c_expression(parser, expr_n, expr_o):
    for i, assign_expr in enumerate(expr_n[0]):
        if not (i & 1):
            c_assignment_expression(parser, assign_expr, expr_o)

def c_assignment_expression(parser, assign_expr, RHS):
    print("c_assignment_expression not implemented yet")
    # TODO: handle RHS of assignment expression
    c_conditional_expression(parser, assign_expr[1], RHS)
    # TODO: handle LHS of assignment expression
    if assign_expr[0]:
        for LHS_eq in reversed(assign_expr[0]):
            LHS = ExpressionResult()
            c_assign_handler(parser, LHS_eq, LHS, RHS)
            RHS = LHS

def c_assign_handler(parser, unary_assign_op, LHS, RHS):
    print("handling assignments in c_assignment_expression not fully implemented")

def c_constant_expression(parser, const_expr, expr):
    c_conditional_expression(parser, const_expr[0], expr)

def c_conditional_expression(parser, cond_expr, expr):
    if len(cond_expr) > 1: # ternary operator. first child is not returned
        cond = expr.build()
        c_logOR_expression(parser, cond_expr[0], cond)
        if cond.bool_result == BOOL_TRUE:
            c_expression(parser, cond_expr[2], expr)
            c_conditional_expression(parser, cond_expr[4], cond)
        else:
            c_conditional_expression(parser, cond_expr[4], expr)
            c_expression(parser, cond_expr[2], cond)
            
        print("ternary operator not fully implemented")
    else:
        c_logOR_expression(parser, cond_expr[0], expr) # sets tokens/evaluates
def c_handle_logor(parser, LHS, RHS):
    print("c_handle_logor not yet implemented")

LOGOR_PAIRS = ((PUNC_124_124, c_handle_logor), )
def c_logOR_expression(parser, logOR_expr, expr):
    c_handle_left_right_binary(parser, logOR_expr, expr, c_logAND_expression, LOGOR_PAIRS)
    if len(logOR_expr[1]) > 1:
        expr.type = BOOL_TYPE # result must be of bool type

def c_handle_logand(parser, LHS, RHS):
    print("c_handle_logand not yet implemented")

LOGAND_PAIRS = ((PUNC_38_38, c_handle_logand), )
def c_logAND_expression(parser, logAND_expr, expr):
    c_handle_left_right_binary(parser, logAND_expr, expr, c_OR_expression, LOGAND_PAIRS)
    if len(logAND_expr[1]) > 1:
        expr.type = BOOL_TYPE # result must be of bool type

def c_handle_bitor(parser, LHS, RHS):
    print("c_handle_bitor not yet implemented")

BITOR_PAIRS = ((PUNC_124, c_handle_bitor), )
def c_OR_expression(parser, OR_expr, expr):
    c_handle_left_right_binary(parser, OR_expr, expr, c_XOR_expression, BITOR_PAIRS)
    if len(OR_expr[1]) > 1:
        expr.type = BOOL_TYPE # result must be of bool type

def c_handle_bitxor(parser, LHS, RHS):
    print("c_handle_bitxor not yet implemented")

BITXOR_PAIRS = ((PUNC_94, c_handle_bitxor), )
def c_XOR_expression(parser, XOR_expr, expr):
    c_handle_left_right_binary(parser, XOR_expr, expr, c_AND_expression, BITXOR_PAIRS)
    if len(XOR_expr[1]) > 1:
        expr.type = BOOL_TYPE # result must be of bool type

def c_handle_bitand(parser, LHS, RHS):
    print("c_handle_bitand not yet implemented")

BITAND_PAIRS = ((PUNC_38, c_handle_bitand), )
def c_AND_expression(parser, AND_expr, expr):
    c_handle_left_right_binary(parser, AND_expr, expr, c_equality_expression, BITAND_PAIRS)
    if len(AND_expr[1]) > 1:
        expr.type = BOOL_TYPE # result must be of bool type

def c_handle_compare_equal(parser, LHS, RHS):
    print("c_handle_compare_equal not yet implemented")

def c_handle_not_equal(parser, LHS, RHS):
    print("c_handle_not_equal not yet implemented")

EQUALITY_PAIRS = ((PUNC_61_61, c_handle_compare_equal), (PUNC_33_61, c_handle_not_equal))
def c_equality_expression(parser, eq_expr, expr):
    c_handle_left_right_binary(parser, eq_expr, expr, c_relational_expression, EQUALITY_PAIRS)
    if len(eq_expr[1]) > 1:
        expr.type = BOOL_TYPE # result must be of bool type

def c_handle_less_than(parser, LHS, RHS):
    print("c_handle_less_than not yet implemented")

def c_handle_less_than_equal(parser, LHS, RHS):
    print("c_handle_less_than_equal not yet implemented")

def c_handle_greater_than(parser, LHS, RHS):
    print("c_handle_greater_than not yet implemented")

def c_handle_greater_than_equal(parser, LHS, RHS):
    print("c_handle_greater_than_equal not yet implemented")

RELATIONAL_PAIRS = ((PUNC_60, c_handle_less_than), (PUNC_62, c_handle_greater_than), (PUNC_60_61, c_handle_less_than_equal), (PUNC_62_61, c_handle_greater_than_equal))
def c_relational_expression(parser, rel_expr, expr):
    c_handle_left_right_binary(parser, rel_expr, expr, c_shift_expression, RELATIONAL_PAIRS)
    if len(rel_expr[1]) > 1:
        expr.type = BOOL_TYPE # result must be of bool type

def c_handle_left_shift(parser, LHS, RHS):
    print("c_handle_left_shift not yet implemented")

def c_handle_right_shift(parser, LHS, RHS):
    print("c_handle_right_shift not yet implemented")

SHIFT_PAIRS = ((PUNC_60_60, c_handle_left_shift), (PUNC_62_62, c_handle_right_shift))
def c_shift_expression(parser, shift_expr, expr):
    c_handle_left_right_binary(parser, shift_expr, expr, c_additive_expression, SHIFT_PAIRS)

# additional handlers
# assigns result metadata to LHS
def c_handle_add(parser, LHS, RHS):
    print("c_handle_add not yet implemented")

# assigns result metadata to LHS
def c_handle_sub(parser, LHS, RHS):
    print("c_handle_sub not yet implemented")

def c_handle_left_right_binary(parser, node, expr, subrule, rule_handler_pairs):
    subrule(parser, node[0], expr)
    if node[1]:
        LHS = expr
        RHS = LHS.build()
        N = len(rule_handler_pairs)
        for chain in node[1]:
            subrule(parser, chain[1], RHS)
            i = 0
            while i < N and chain[0].rule is not rule_handler_pairs[i][0]:
                i += 1
            if i == N:
                raise ValueError(f"unknown operator. Should not have reached here")
            rule_handler_pairs[i][1](parser, LHS, RHS)
    
ADDITION_PAIRS = ((PUNC_43, c_handle_add), (PUNC_45, c_handle_sub))
def c_additive_expression(parser, add_expr, expr):
    c_handle_left_right_binary(parser, add_expr, expr, c_multiplicative_expression, ADDITION_PAIRS)                

# multiplication handles
# assigns result metadata to LHS
def c_handle_multiply(parser, LHS, RHS):
    print("c_handle_multiply not yet implemented")

# assigns result metadata to LHS
def c_handle_divide(parser, LHS, RHS):
    print("c_handle_divide not yet implemented")

# assigna result metadata to LHS
def c_handle_mod(parser, LHS, RHS):
    print("c_handle_mod not yet implemented")

MULTIPLICATION_PAIRS = ((PUNC_42, c_handle_multiply), (PUNC_47, c_handle_divide), (PUNC_37, c_handle_mod))
def c_multiplicative_expression(parser, mult_expr, expr):
    c_handle_left_right_binary(parser, mult_expr, expr, c_cast_expression, MULTIPLICATION_PAIRS)

def c_cast_expression(parser, cast_expr, expr):
    if len(cast_expr) > 1:
        type_ = Type()
        c_type_name(parser, cast_expr[1], type_)
        c_cast_expression(parser, cast_expr[3], expr)
        # TODO: add checks for type compatibility
        expr.type = type_
    else:
        c_unary_expression(parser, cast_expr[0], expr)

def c_unary_op(parser, op, expr):
    op = op[0]
    if op.rule is PUNC_38: # &
        expr.type = expr.type.address()
    elif op.rule is PUNC_42: # *
        expr.type = expr.type.indirection()
    elif op.rule is PUNC_43: # +, no-op
        pass
    elif op.rule is PUNC_45: # -, negate
        # TODO: take negative if able
        pass
    elif op.rule is PUNC_126: # ~, logical not, no-op for now
        # TODO: perform bitwise negation if able
        pass
    else: # !
        # TODO: perform logical negation if able
        if expr.bool_result is BOOL_TRUE:
            expr.bool_result = BOOL_FALSE
        elif expr.bool_result is BOOL_FALSE:
            expr.bool_result = BOOL_TRUE

def c_unary_expression(parser, unary_expr, expr):
    if unary_expr[0].rule is SIZEOF:
        if unary_expr[1] is UNARY_EXPRESSION:
            c_unary_expression(parser, unary_expr[1], expr)
            expr.arb_value = expr.type.size
            expr.type = SIZE_T_TYPE
        else:
            c_type_name(parser, unary_expr[2], expr)
            expr.arb_value = expr.type.size
            expr.type = SIZE_T_TYPE
    elif unary_expr[0].rule is _ALIGNOF:
        c_type_name(parser, unary_expr[2], expr)
        expr.arb_value = expr.type.align
        expr.type = SIZE_T_TYPE
    elif unary_expr[0].rule is POSTFIX_EXPRESSION:
        c_postfix_expression(parser, unary_expr[0], expr)
    elif unary_expr[0].rule is UNARY_OPERATOR:
        c_cast_expression(parser, unary_expr[1], expr)
        c_unary_op(parser, unary_expr[0], expr)
    else: # ++ or -- prefix
        c_unary_expression(parser, unary_expr[1], expr)
        # TODO: handle increment if constant

def c_pointer_access_expression(parser, ptr_access_expr, expr):
    print("c_pointer_access_expression not yet implemented")

def c_namespace_access_expression(parser, namespace_expr, expr):
    print("c_AND_expression not yet implemented")

def c_call_expression(parser, call_expr, expr):
    print("c_call_expression not yet implemented")

def c_get_member_expression(parser, get_expr, expr):
    print("c_get_member_expression not yet implemented")

def c_compound_literal(parser, cmpd_lit, expr):
    print("c_compound_literal not yet implemented")

def c_postfix_expression(parser, postfix, expr):
    start = postfix[0][0]
    if start.rule is PRIMARY_EXPRESSION:
        c_primary_expression(parser, start, expr)
    elif start.rule is COMPOUND_LITERAL:
        c_compound_literal(parser, start, expr)
    for op in postfix[1]:
        if op.rule is GET_MEMBER_EXPRESSION:
            c_get_member_expression(parser, op, expr)
        elif op.rule is CALL_EXPRESSION:
            c_call_expression(parser, op, expr)
        elif op.rule is NAMESPACE_ACCESS_EXPRESSION:
            c_namespace_access_expression(parser, op, expr)
        elif op.rule is POINTER_ACCESS_EXPRESSION:
            c_pointer_access_expression(parser, op, expr)
        elif op.rule is PUNC_43_43: # ++ increment postfix
            # TODO: increment postfix
            pass
        else: # -- decrement postfix
            # TODO: decrement
            pass

def c_generic_selection(parser, generic, expr):
    print("c_generic_expression not yet implemented")

def c_constant(parser, const, expr):
    expr.arb_value = parser.get_tokens(const)[0]
    const = const[0]
    # TODO: distinguish the unsigned types
    if const.rule is FLOAT_CONSTANT:
        expr.type = DOUBLE_TYPE
    elif const.rule is INT_CONSTANT:
        expr.type = INT_TYPE
    elif const.rule is CHAR_CONSTANT:
        expr.type = CHAR_LITERAL_TYPE

WIDE_LITERAL_PREFIX = {'u', 'U', 'L'}
def c_primary_expression(parser, primary, expr):
    nonterm = primary[0]
    if nonterm.rule is IDENTIFIER:
        expr.type = parser.scope.get_identifier(parser.get_tokens(nonterm)[0])
    elif nonterm.rule is CONSTANT:
        c_constant(parser, nonterm, expr)
    elif nonterm.rule is STRING_LITERAL:
        expr.arb_value = parser.get_tokens(nonterm)[0]
        # TODO: fix when string_literal is broken into utf-8 string literal vs wide-character string literal
        if expr.arb_value[0] in WIDE_LITERAL_PREFIX and expr.arb_value[1] != '8':
            expr.type = WSTRING_LITERAL_TYPE
        else:
            expr.type = STRING_LITERAL_TYPE
    elif nonterm.rule is GENERIC_SELECTION:
        c_generic_selection(parser, nonterm, expr)
    else:
        c_expression(parser, nonterm[1], expr)

# DECLARATORS and DECLARATIONS

def c_pointer(parser, pointer, type_):
    quals = []
    attrs = []
    #print(pointer)
    for attr in pointer[1]:
        if attr.rule is TYPE_QUALIFIER:
            quals.extend(parser.get_tokens(attr)) # each qualifier is a single token
        else:
            attrs.append(parser.get_tokens(attr)) # each attribute is a sequence of tokens
    type_.derived.append(PointerType(parser.get_tokens(pointer[0]), quals, attrs))

def c_pointers(parser, pointers, type_):
    #print(pointers, "...number of pointers found:", len(pointers))
    for pointer in pointers:
        c_pointer(parser, pointer, type_)



def param_decl_next(node):
    if node:
        node = node[0][1]
    return node

def c_direct_abstract_declarator(parser, dir_abs_declrtr, type_):
    sub_declarator = []
    
    # first production is ('(', declarator, ')')
    # this would be an automatic allocated Obj
    if len(dir_abs_declrtr) == 2:
        if dir_abs_declrtr[0]:
            temp_type = Type(None, sub_declarator)
            c_abstract_declarator(parser, dir_abs_declrtr[0][1], temp_type)
        stack = []
        for array_or_func in dir_abs_declrtr[1]: # binding reverses these
            if array_or_func.rule is ARRAY_DECLARATOR:
                temp_type = IndexedType()
                c_array_declarator(parser, array_or_func, temp_type)
            else:
                temp_type = ParameterizedType()
                c_func_declarator(parser, array_or_func, temp_type)
            stack.append(temp_type)
        # TODO: unwind the stack and build the type
    else:
        temp_type = Type(None, sub_declarator)
        c_abstract_declarator(parser, dir_abs_declrtr[1], temp_type)

def c_abstract_declarator(parser, abs_declrtr, type_):
    if abs_declrtr[0].rule is POINTER:
        c_pointers(parser, abs_declrtr[0], type_)
    else: # production is (pointer?, direct_abstract_declarator)
        if abs_declrtr[0]:
            c_pointers(parser, abs_declrtr[0], type_)
        c_direct_abstract_declarator(parser, abs_declrtr[1], type_)

def c_parameter_list(parser, param_list, call_type):
    #print("c_parameter_list in development")
    Nparam = ((len(param_list) - 1) >> 1) + 1
    for i, param_decl in enumerate(param_list):
        if not (i & 1):
            decl_spec = DeclSpec()
            #declrtr_opt = c_parameter_declaration(parser, node[0], decl_spec)[0]
            declrtr_opt = extract_declaration_specifiers(parser, param_list[i], decl_spec, PARAMETER_DECLARATION)
            obj = Parameter()
            obj.from_DeclSpec(decl_spec)
            if declrtr_opt:
                if declrtr_opt[0][0].rule is DECLARATOR:
                    c_declarator(parser, declrtr_opt[0][0], obj)
                    # TODO!!!! Per the standard (and ambiguity in the grammar) if the identifier here can be interpreted as a typedef name, then it is a typedef name. This needs to be reconciled
                else: # is ABSTRACT_DECLARATOR
                    c_abstract_declarator(parser, declrtr_opt[0][0], obj.type)
            if i == 0 and obj.type.is_compatible(VOID_TYPE):
                if Nparam == 1:
                    break
                else:
                    raise ValueError("invalid type for parameter")
            else:
                call_type.params.append(obj)
    #print("function parameter list\n\t" + ',\n\t'.join(str(param) for param in call_type.params))

def c_func_declarator(parser, func_declarator, call_type):
    #print(func_declarator, func_declarator[1], func_declarator[1][0])
    if func_declarator[1]:
        call_type.params = []
        call_type.has_ellipses = True if func_declarator[1][0][1] else False
        c_parameter_list(parser, func_declarator[1][0][0], call_type)

def c_array_declarator(parser, array_declarator, ret_type):
    if array_declarator[1] or array_declarator[3]:
        ret_type.static = True
    ret_type.quals = parser.get_tokens(array_declarator[2])

    if array_declarator[4]:
        if array_declarator[4][0].rule is ASSIGNMENT_EXPRESSION:
            exp = ExpressionResult()
            c_assignment_expression(parser, array_declarator[4][0], exp)
    # TODO!!!!!! need to fix this based on result of c_assignment_expression
    ret_type.size = 0

def c_direct_declarator(parser, direct_declarator, obj):
    sub_declarator = []
    if direct_declarator[0][1].rule is IDENTIFIER: # this is kind of dangerous
        # first production is (msattribute*, identifier)
        for attr in direct_declarator[0][0]:
            obj.attributes.append(parser.get_tokens(attr))
        obj.identifier = parser.get_tokens(direct_declarator[0][1])[0]
    else:
        # first production is ('(', declarator, ')')
        # this would be an automatic allocated Obj
        temp_obj = Object([], None, Type(None, sub_declarator))
        c_declarator(parser, direct_declarator[0][1], temp_obj)
        obj.identifier = temp_obj.identifer
    stack = []
    for array_or_func in direct_declarator[1]: # binding reverses these
        if array_or_func.rule is ARRAY_DECLARATOR:
            temp_type = IndexedType()
            c_array_declarator(parser, array_or_func, temp_type)
        else:
            temp_type = ParameterizedType()
            c_func_declarator(parser, array_or_func, temp_type)
        stack.append(temp_type)
    # TODO: here is where I flip the types.
    # TODO: also check that the arrays/funcs are valid (func cannot return array or func)

def c_declarator(parser, declarator, obj):
    #print("declarator:", declarator, declarator[0])#, "\ttype:", type_)
    if declarator[0]:
        c_pointers(parser, declarator[0][0], obj.type)
    c_direct_declarator(parser, declarator[1], obj)

def c_initializer(parser, initializer, type_):
    print("c_initializer not yet implemented")

def c_init_declarator(parser, init_declarator, obj):
    #print(init_declarator)
    for attr_spec in init_declarator[1]:
        obj.attributes.append(parser.get_tokens(attr_spec))
    c_declarator(parser, init_declarator[0], obj)
    if init_declarator[2]: # an initializer was provided
        type_initer = Type()
        c_initializer(parser, init_declarator[2][1], type_initer)
        # check for type compatibility between initializer and object
        # if not obj.type.is_compatible(type_initer)
        #     raise ValueError(f"{obj.type} is not compatible with {type_initer}" )

def c_init_declarator_list(parser, init_declarator_list, obj_list):
    #print(init_declarator_list)
    i = 0
    N = len(init_declarator_list)
    while i < N - 1:
        obj_list.append(copy.copy(obj_list[i]))
        c_init_declarator(parser, init_declarator_list[i], obj_list[i])
        i += 1
    c_init_declarator(parser, init_declarator_list[i], obj_list[i])

def c_atomic_type_specifier(parser, atomic_type_spec, decl_spec):
    print("c_atomic_type_specifier not yet implemented")

def c_static_assert_declaration(parser, static_assert):
    print("c_static_assert_declaration not yet implemented")

def c_struct_declarator(parser, struct_declrtr, member):
    if len(struct_declrtr) == 1: # simple declarator
        c_declarator(parser, struct_declrtr[0], member)
    else: # declarator?, ':', constant_expression
        #print("bitfield struct members not yet implemented (missing size interpretation)")
        if struct_declrtr[0]:
            c_declarator(parser, struct_declrtr[0], member)
        exp = ExpressionResult()
        c_constant_expression(parser, struct_declrtr[2], exp)
        # TODO: FIX THIS!!!! 0 is not acceptable
        member.size = str(exp.tokens[0]) if exp.tokens else 0

def c_struct_declarator_list(parser, struct_declrtr_list, member_list):
    #print(struct_declrtr_list)
    i = 0
    N = ((len(struct_declrtr_list) - 1) >> 2) + 1
    while i < N - 1:
        member_list.append(copy.copy(member_list[i]))
        c_struct_declarator(parser, struct_declrtr_list[2*i], member_list[i])
        i += 1
    c_struct_declarator(parser, struct_declrtr_list[2*i], member_list[i])

def c_struct_declaration(parser, struct_decl, member_list):
    #print(struct_decl)
    if struct_decl[0].rule is STATIC_ASSERT_DECLARATION:
        c_static_assert_declaration(parser, struct_decl[0])
    else:
        decl_spec = DeclSpec()
        node = extract_declaration_specifiers(parser, struct_decl[0], decl_spec, MEMBER_DECLARATION)
        member_list[0].from_DeclSpec(decl_spec)
        if node[0]:
            c_struct_declarator_list(parser, node[0][0], member_list)

def c_struct_or_union_specifier(parser, struct_or_union_spec, decl_spec):
    if struct_or_union_spec[0].rule is STRUCT:
        decl_spec.specifiers = StructSpec(parser.get_tokens(struct_or_union_spec[0]))
    else:
        decl_spec.specifiers = UnionSpec(parser.get_tokens(struct_or_union_spec[0]))
    spec_type = decl_spec.specifiers
    identifier = None
    node = struct_or_union_spec[1]
    if len(node) > 1: # (identifier?, '{', struct_declaration+, '}')
        if node[0]:
            identifier = parser.get_tokens(node[0][0])[0]
        for struct_decl in node[2]:
            member_list = [Member()]
            c_struct_declaration(parser, struct_decl, member_list)
            spec_type.members.extend(member_list)
    else:
        identifier = parser.get_tokens(node[0])[0]
    if identifier:
        spec_type.tokens.append(identifier)

def c_enumerator(parser, enumer, pair):
    pair.append(parser.get_tokens(enumer[0])[0])
    if enumer[1]:
        #print(enumer[1][0][1])
        exp = ExpressionResult()
        c_constant_expression(parser, enumer[1][0][1], exp)

def c_enum_list(parser, enum_list, constants):
    #print(struct_declrtr_list)
    cur_val = 0
    for i, enumer in enumerate(enum_list):
        if not (i & 1):
            pair = []
            c_enumerator(parser, enumer, pair)
            if len(pair) > 1:
                cur_val = pair[1]
            else:
                cur_val += 1
            constants[pair[0]] = cur_val

def c_enum_specifier(parser, enum_spec, decl_spec):
    #print("c_enum_specifier not yet implemented")
    decl_spec.specifiers = EnumSpec(parser.get_tokens(enum_spec[0]))
    spec_type = decl_spec.specifiers
    identifier = None
    node = enum_spec[1]
    if len(node) > 1: # (identifier?, '{', enumerator_list, '}')
        if node[0]:
            identifier = parser.get_tokens(node[0][0])[0]
        c_enum_list(parser, node[2], spec_type.constants)
    else:
        identifier = parser.get_tokens(node[0])[0]
    if identifier:
        spec_type.tokens.append(identifier)

def c_typedef_name(parser, typedef_name, decl_spec):
    id_ = parser.get_tokens(typedef_name)[0]
    decl_spec.specifiers = TypeDef(id_, parser.scope.get_typedef(id_))

class DeclSpec:
    __slots__ = ("typedef_tf", "storage_class", "specifiers", "qualifiers", "func_spec", "attrs")
    def __init__(self, typedef_tf = False, storage_class = None, specifiers = None, qualifiers = None, func_spec = None, attrs = None):
        self.typedef_tf = typedef_tf
        self.storage_class = storage_class if storage_class is not None else []
        # TODO: consider changing the specifiers to an instance of BaseSubType
        self.specifiers = specifiers
        self.qualifiers = qualifiers if qualifiers is not None else []
        self.func_spec = func_spec if func_spec is not None else []
        self.attrs = attrs if attrs is not None else []
    def __copy__(self):
        return DeclSpec(self.typedef_tf, copy.copy(self.storage_class), copy.copy(self.specifiers), copy.copy(self.qualifers), copy.copy(self.func_spec), copy.copy(self.attrs))
    def __str__(self):
        return f"""declaration specifiers:
\ttypedef (True/False): {'True' if self.typedef_tf else "False"}
\tstorage class: {' '.join(str(t) for t in self.storage_class) if self.storage_class else "None"}
\tspecifiers: {' '.join(str(t) for t in self.specifiers) if self.specifiers else "None"}
\tqualifiers: {' '.join(str(t) for t in self.qualifiers) if self.qualifiers else "None"}
\tfunction specifiers: {' '.join(str(t) for t in self.func_spec) if self.func_spec else "None"}
\tattributes: {' '.join(str(t) for t in self.attrs) if self.attrs else "None"}
"""

def ext_decl_spec_next(node):
    return node[1]

def extract_declaration_specifiers(parser, node, decl_spec, recursive_rule, get_next_node = ext_decl_spec_next):
    while node.rule is recursive_rule:
        # in C version, need to properly release all these nodes as they are reorg'd
        #print(node, len(node))
        ds = node[0][0]
        #print(ds.rule, ds[0].rule)
        if ds.rule == STORAGE_CLASS_SPECIFIER:
            if ds[0].rule is TYPEDEF:
                decl_spec.typedef_tf = True
            else:
                decl_spec.storage_class.extend(parser.get_tokens(ds[0]))
        elif ds.rule is FUNCTION_SPECIFIER:
            decl_spec.func_spec.extend(parser.get_tokens(ds[0]))
        elif ds.rule is ATTRIBUTE_SPECIFIER:
            decl_spec.attrs.append(parser.get_tokens(ds[0]))
        elif ds.rule is TYPE_SPECIFIER:
            ds = ds[0]
            if ds.rule is ATOMIC_TYPE_SPECIFIER:
                c_atomic_type_specifier(parser, ds, decl_spec)
            elif ds.rule is STRUCT_OR_UNION_SPECIFIER:
                c_struct_or_union_specifier(parser, ds, decl_spec)
            elif ds.rule is ENUM_SPECIFIER:
                c_enum_specifier(parser, ds, decl_spec)
            elif ds.rule is TYPEDEF_NAME:
                c_typedef_name(parser, ds, decl_spec)
            else:
                if decl_spec.specifiers is None:
                    decl_spec.specifiers = BaseSubType(parser.get_tokens(ds))
                else:
                    decl_spec.specifiers.tokens.extend(parser.get_tokens(ds))
        elif ds.rule is TYPE_QUALIFIER:
            decl_spec.qualifiers.extend(parser.get_tokens(ds[0]))
        else:
            raise ValueError(f"declaration specifier of type {ds.rule} is not recognized")
        node = get_next_node(node)
    
    return node

#def c_declaration_standard(parser, decl_std, decl_spec):
#    return extract_declaration_specifiers(parser, decl_std, decl_spec, DECLARATION_STANDARD)

def c_declaration(parser, node):
    #print("c_declaration:", node, '\n\t', node[0])
    obj_list = []
    if node[0].rule is DECLARATION_STANDARD:
        decl_spec = DeclSpec()
        #init_decl_list_opt = c_declaration_standard(parser, node[0], decl_spec)[0]
        init_decl_list_opt = extract_declaration_specifiers(parser, node[0], decl_spec, DECLARATION_STANDARD)[0]
        if decl_spec.func_spec:
            obj_list.append(Callable())
        else:
            obj_list.append(Object())
        obj_list[0].from_DeclSpec(decl_spec)
        if init_decl_list_opt:
            c_init_declarator_list(parser, init_decl_list_opt[0], obj_list)
        #print(init_decl_list, "Occupied" if init_decl_list else "Empty")
    else:
        c_static_assert_declaration(parser, node[0])
    #for obj in obj_list:
    #    print("new object:", str(obj))

def c_external_declaration(parser, node):
    #print("c_external_declaration:", node, '\n\t', node[0])
    node_ = node[0]
    if node_.rule is PRAGMA_DIRECTIVE:
        c_pragma_directive(parser, node_)
    elif node_.rule is FUNCTION_DEFINITION:
        c_function_definition(parser, node_)
    elif node_.rule is DECLARATION:
        c_declaration(parser, node_)

def c_root(parser, node):
    for ext_decl in node:
        c_external_declaration(parser, ext_decl)
    return node
