# peggen

A parser generator library that generates a PEG-style parser for a given grammar.

It is designed to be as simple as possible to use--once the grammar specification is understood--while being as flexible as possible to allow the user to customize the parsing process and output.

## When to use <b>peggen</b>

If you want to build a parser that produces an AST that can be manipulated on the fly using a PEG parsing strategy while also providing tokenization/lexical analysis all in the same grammar/specification.

If your goal is otherwise--even if it is simpler--I suggest looking at `parsimonious`. My next option was to hack it a little bit if I couldn't get my own to work. Just watch out for the switch in operator precedence of AND/OR in `parsimonious` ("sequence"/"first_choice" in peggen); it is reversed from what you might expect reading other PEGs.

## How <b>peggen</b> works

peggen takes your grammar input and and dependent files and the `ParserGenerator` class creates 2 more files:
1) [my exported module]_.py
2) [my exported module].py

The first is the module that declares all the productions that appear in the grammar and exposes them to any imported modules. The second is the module that implements all the productions. Any modules that implement transfer functions used by productions or implement a subclass of the resulting parser should import 1), but any modules that use the resulting parser should import 2). This weirdness is because of Python import rules.

A Parser is then created (called `[my exported module]Parser`) that takes a string or file and builds an AST. The AST comprises nodes that can be transformed on the fly during parsing or in post-process by specifying transform functions in the options of each production.

### Grammar operators implemented:
- `,` "sequence" of subrules that must all succeed for the overall rule to succeed.
- `\` "first_choice" from a set of subrules in left-to-right association is returned if succeeded otherwise failure. In the future, I will have `\` or `/` behave equivalently to be more consistent with other PEGs
- `|` "long_choice" (in terms of token-to-token extent) from a set of options is returned upon success of at least one option, otherwise failure
- `{min:max}` foregoing rule must succeed a number of times in the range of `min` to `max` for the whole operation to succeed otherwise failure. `min` and `max` are each optional with defaults of 0. `max == 0` means an infinite number.
- `+` foregoing rule must succeed at least once for the overall rule to succeed otherwise failure. Equivalent to `{1:}`
- `*` foregoing rule may succeed any number of times. Equivalent to `{:}`
- `?` foregoing rule may appear once if at all for the overall rule to succeed otherwise failure. Equivalent to `{:1}`
- `.` the following rule succeeds at least once and is separated/delimited by the foregoing rule otherwise failure. The nodes that might result from the foregoing rule are discarded. Note that `a.b` is semantically equivalent to `b (a, b)*`, but the return structure is very different as the latter is a composition of a rule and repetition of a sequence.Use `b (a, b)*` if the result of `a` must be retained. Otherwise, the `a.b` form is significantly simpler to handle.
- `&` the following rule must succeed in order for the super-rule (generally only sequences) to succeed. Positive lookahead rule
- `!` the following rule must fail in order for the super-rule (generally only sequences) to succeed. Negative lookahead rule
- `"` regex rule. The contents between two double-quotes is treated as a regular expression following the `re` module
- `'` string rule. The contents between two single-quotes is treated as a plain string. Most strings may also be in double-quotes, but care must be taken that it does not contain regex escape characters
- `(` subrule `)` encapsulation rule to allow changes in order of evaluation by evaluating subrule first before any other rule that might appear adjacent to parentheses.


### Operator precedence (Highest to Lowest top to bottom)
- `"`, `'`, `()`
- `&`, `!`
- `.`
- `+`, `*`, `?`, `{}`
- `,`
- `\` (left-to-right)
- `|`

## How to use <b>peggen</b> (high-level)

Specify a grammar for a language, file, etc. in a format that most closely resembles the [Python grammar specification](https://docs.python.org/3/reference/grammar.html); see below for details. Provide implementations (and the necessary configuration entries in your grammar) for any handlers or customizations of the parser (by inheriting from the class `[my exported module]Parser` located in `[my exported module].py`)

From a setup.py file or some configuration file for your module, create an instance of `ParserGenerator` with your grammar specification as the input. This creates the two files mentioned above. This generally only has to happen once or whenever your grammar is updated.

In your modules, simply `import [my exported module]Parser` and create an instance of the appropriate parser class with your inputs. Done.

As a quick example, the json parser (in ./Examples) is created and run as:

```
>>> from peggen import ParserGenerator
>>> ParserGenerator("json.grmr") # generates the parser named "jsonpegParser" importable from "jsonpeg.py"
>>> from jsonpeg import jsonpegParser 
>>> result = jsonpegParser("{\"key\": [1, -1.2]}")[0] # result is a dict: {"key" : [1, -1.2]}. The indexing [0] is due to the specific Parser subclass implementation
```

## Features
- simple memoization to prevent exponential time at the cost of memory (packrat-like)
- comments in grammar (C-style, though Python style also planned)
- generates abstract syntax tree and tokenizes on demand
- specify imports and handlers in grammar to link outside code
    - unlike `pyparsing` (and `parsimonious`), this syntax allows for modification of the AST while it is being generated
- (possibly annoying) unlike other PEG parser, the PEG `OR` operator is denoted `\` and NOT `/`. I intend for either to be used
- unlike other PEG parsers, I have kept in the standard `|` OR operator. I have found it convenient rather than having to try to figure out if I really want something to be returned before another is tested. It is still better to rely on `\` when possible
    - Precedence is `,` > `\` > `|`
- left-recursion is not yet handled automatically; requires manual removal

## Features to be implemented (no particular order)
- transform functions for modifying AST post-generation
- automatically handle left-recurions
- bootstrap so that the parser generator is written in the parser generator
- export PEG parser for C
- port to C with bindings to Python

## Grammar for grammars

Semantics for the productions are provided in the comments preceding the definitions

```
// peggen.grmr
// Note that the extension is arbitrary

/*
root is the entry point for the parser. In most cases, it should be a repeated 
rule using the '+' (or even '*') operator or name another production which is. 
If you can write a grammar, which isn't, then you might have a predefined 
structure and there is probably a better way to parse or unmarshall.

There are three types of entries in the grammar.
1) a configuration entry
2) a special production entry
3) a production entry

root itself is a required production, but it doesn't have the same syntactic 
restrictions as a special_production
*/
root:
    (config \ special_production \ production)+

/*
configuration entries consist of ways to configure certain parameters in the 
parser generator. For now there are only 2:
1) import - This adds to a list an external source module to be imported into 
the "production implementation file". Multiple imports can exist in the grammar
 to specify multiple source modules.
2) export - This configures the base name of the exported module. Any 
subsequent appearances of this configuration entry will overwrite previous ones
If not provided, the name of the grammar file (extensions removed) is used.
*/
config:
    ('import' | 'export'), ':', nonws_printable

/*
normal productions of the grammar. They must be identifiers that are followed
by an optional comma-separated list of transform_functions. 
transform_functions identify functions that are applied to the nodes at
different stages of processing. All transform_functions must have the signature:

function_call(parser: Parser, node: Node) -> Node

Here the Parser itself acts as the context that can be used to manipulate the 
nodes. Within the function_call, you may compare against any of the productions
in the grammar to compare types by simply referring to the production 
identifier in all uppercase letters.

As a silly, contrived example, if you have productions "float" and "int" to 
distinguish the type of an "arithmetic" production, you might have in the 
grammar:
import: handlers
arithmetic(handle_arithmetic):
    float \ int
int:
    // definition of int
float:
    // definition of float

# in handlers.py
class FloatNode(Node):
    __slots__ = ("val",)
    def __init__(self, source_node, float_val):
        # copy data from source_node
        self.val = float_val
class IntNode(Node):
    __slots__ = ("val",)
    def __init__(self, source_node, integer_val):
        # copy data from source_node
        self.val = integer_val
def handle_arithmetic(parser, arithmetic_node)
    if arithmetic_node[0].rule is INT:
        return IntNode(arithmetic_node, int(str(parser.get_tokens(arithmetic_node)[0])))
    elif arithmetic_node[0].rule is FLOAT:
        return FloatNode(arithmetic_node, float(str(parser.get_tokens(arithmetic_node)[0])))
    return FAIL_NODE

Options are currently (ordered by index in list)
1) The first one is applied while building the AST. The result is the Node 
stored in the cache for packrat so it on any given string and at any location, 
this function is only called once.
2) The second one (not yet implemented) is applied during traversal after AST is built. Each of the 
grammar operators has a default for inorder traversal and is initiated by 
parser_instance.traverse()
*/
production:
    identifier, ('(', transform_functions, ')')?, ':', long_choice
transform_functions:
    ','.nonws_printable

/*
special_productions are those that have some special meaning or processing for
the ParserGenerator to work correctly. 
token is required in each grammar for tokenization, but punctuator and keyword are not
(though they will often appear, especially punctuator)
Note that they may NOT be transformed directly.
*/
special_production:
    ('token'), ':', rule |
    ('punctuator' | 'keyword'), ':', ','.string_literal

/*
token is the entry point for the tokenizer. This generally comprises the 
"special_production"s, whitespace, and some form of identifiers. This is the 
production that you should definitely focus on using the `\` operator. It 
is pretty easy to mess up the tokenizer step by using the wrong one.

The resulting node of the token production should NEVER result in more than one
"token". This would otherwise likely result in a broken parser. The guideline 
is basically that if you operators other than '\' or '|' are present when the 
rule is fully expanded, it is probably wrong. If you find the need to know more
information of nearby tokens (implying your grammar is not really context 
free), I suggest making a separate production that uses lookaheads/lookbehinds 
or adding some context analysis to a subclass of the parser. The latter can be
implemented using the transform functions
*/
token:
    whitespace \ string_literal \ regex_literal \ punctuator \ keyword \ identifier

/*
punctuators are general characters that delimit other non-whitespace tokens in 
grammar. The implementation is such that each punctuator has its own production
made and then an overall production representing any (generally by '|' linking 
each one)
*/
punctuator:
    '!','\\', ',', '?', '.', '&', ':', '+', '*', '(', ')', '{', '}' // to include '/' in the future for a proper "first_choice"
/*
same as punctuator but separated for ease of semantics to identify keywords
*/
keyword:
    'import', 'export', 'punctuator', 'keyword', 'token', 'root'

/*
productions long_choice through base_rule implement the grammar operators and 
their precedence as described in How peggen works
*/
long_choice(simplify_rule):
    '|'.first_choice
first_choice(simplify_rule):
    '\'.sequence     // eventually will be ('\' | '/').sequence
sequence(simplify_rule):
    ','.repeated_rule
repeated_rule(simplify_rule):
    ('+' | '*' | '?' | '{', \d*, ':', \d* '}')?, list_rule
list_rule(simplify_rule):
    '.'.lookahead_rule
lookahead_rule(simplify_rule):
    ('&' | '!')?, base_rule
base_rule:
    terminal | nonterminal | identifier | '(', long_choice, ')'

/*
terminal string_literals or regex_literals
*/
terminal:
    string_literal \ regex_literal
string_literal:
    "'(((?<=\\\\)\')|[^\'])*'"
regex_literal:
    "\"(((?<=\\\\)\")|[^\"])*\""

/*
nonterminals identify other productions
*/
nonterminal:
    identifier
identifier:
    "\w+"

/*
For specific options that need not be restricted to alphanumeric + '_' "words"
*/
nonws_printable:
    "\S+"

/*
whitespace. skip_token is a built-in transform function that takes a successful
node built during tokenization and marks it for skipping so that it is not used
during parsing. If whitespace is significant or needed for parsing
*/
whitespace(skip_token):
    "(\s+|//[^\n]*\n|/\*.*\*/)+" // includes C-style comments as whitespace

```