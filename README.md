# peggen
PEG generator;

A parser generator library that generates a PEG-style parser for a given grammar.

## Features
- simple memoization to prevent exponential time at the cost of memory (packrat-like)
- comments in grammar (C-style, though may change)
- tokenizes and generates abstract syntax tree at the same time
- specify import and handlers in grammar to link outside code
    - unlike `pyparsing` (and `parsimonious`), this syntax allows for modification of the AST while it is being generated
- (possibly annoying) unlike other PEG parser, the PEG `OR` operator is denoted `\` and NOT `/`. I intend for either to be used
- unlike other PEG parsers, I have kept in the standard '|' or operator 
    - Precedence is ',' > '\' > '|'
- left-recursion is not yet handled automatically; requires removal

## Features to be implemented
- automatically handle left-recurions
- bootstrap so that the parser generator is written in the parser-generator
- export to C

## Example use
TBD. For now, look at folders in ./Examples