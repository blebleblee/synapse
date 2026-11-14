# Lesson 1: Lexical and Syntax Analysis

## 1. First-Principles Intuition & Invariants

Every compiler begins its life as a text processor facing an ancient and deceptively simple problem: a sequence of Unicode characters arrives on standard input, and somewhere buried in that sequence is the precise semantic intent of a human programmer. The compiler's first obligation is to impose structure on that raw stream — to carve the undifferentiated characters into meaningful units, then to arrange those units into a hierarchical grammar tree that the rest of the pipeline can reason about mechanically. This two-phase process, lexical analysis followed by syntax analysis, is not merely a preprocessing convenience. It is the foundational transformation that makes all subsequent compilation possible, and understanding its invariants at the mechanical level is what separates engineers who *use* compilers from engineers who *build* them.

The deepest invariant governing this phase is the **separation of regular and context-free structure**. These two classes of formal language are not arbitrary academic partitions; they correspond precisely to what a finite-state machine can recognize versus what requires a pushdown automaton. Lexical analysis belongs entirely to the regular world: tokens such as identifiers, integer literals, string literals, and keywords can all be described by regular expressions, which means a finite automaton with no auxiliary memory can recognize them in a single left-to-right pass. Syntax analysis, by contrast, requires tracking nested structure — matching `(` with `)`, `{` with `}`, or `begin` with `end` — which is the archetypal problem a pushdown automaton solves by using a stack. Building separate phases for these two concerns is not over-engineering; it is a direct consequence of the Chomsky hierarchy. Collapsing them into a single phase would force you to run a more expensive recognition algorithm over the entire character stream, losing efficiency and obscuring the structure of your implementation.

The second invariant is **linearity of the character stream combined with the greedy longest-match rule**. When a lexer encounters the characters `>=`, it must not emit a `>` token followed by an `=` token; it must emit a single `>=` token, because the longest match wins. This rule, called *maximal munch*, is enforced by the Thompson-construction DFA used underneath every production lexer. It guarantees that the lexer makes an unambiguous decision at every position in the input using only the characters it has already consumed, without backtracking. The implication for language designers is subtle: you cannot add a new multi-character token to a language and expect all existing lexers to handle it correctly unless you rebuild the DFA. The underlying automaton is not an ad-hoc loop; it is a precisely compiled artifact derived from the token grammar.

The third invariant governs the boundary between the two phases: **the lexer produces a flat token stream; the parser produces a tree**. The lexer discards whitespace and comments because they carry no syntactic weight. It maps character sequences to token kinds, attaches source location metadata (line, column, byte offset), and optionally interns the lexeme string into a symbol table. The resulting token stream is a one-dimensional sequence that the parser reads left to right. The parser then imposes the second, hierarchical dimension by recognizing the grammar's production rules, building a parse tree or abstract syntax tree (AST) that encodes the nesting structure of the program. Everything downstream — type checking, IR generation, optimization — operates on that tree, never on the raw character stream. This irreversibility is an important design constraint: errors caught by the parser can reference source locations only because the lexer attached them to tokens.

### Regular Expressions and Finite Automata

A regular expression over an alphabet Σ is defined inductively. The empty string ε, any single character `a ∈ Σ`, the concatenation `rs` of two regular expressions, the alternation `r|s`, and the Kleene star `r*` exhaust the definition. Every modern regex extension — `+`, `?`, character classes, anchors — desugars into these five primitives. This matters because the Thompson construction, published by Ken Thompson in 1968, gives a mechanical procedure for converting any regular expression into a Nondeterministic Finite Automaton (NFA) in linear time and space.

The NFA produced by Thompson construction has a specific structural property: each regular expression operator contributes a small, well-defined fragment of states and transitions, and fragments are composed by wiring ε-transitions between them. An NFA is allowed to have multiple transitions on the same input character and may take ε-transitions (transitions that consume no input), which means it can be in multiple states simultaneously. This nondeterminism is conceptually powerful but computationally inconvenient, because simulating an NFA requires tracking sets of states rather than a single current state.

The standard remedy is the **subset construction**, which converts an NFA over *n* states into a DFA whose states correspond to subsets of NFA states. In the worst case this produces 2^n DFA states, but in practice the lexer DFAs built from programming language token grammars are small, because the token languages are simple. The resulting DFA has exactly one transition per input character per state, which means recognition is O(n) in the length of the input with no backtracking. This is the theoretical guarantee that makes DFA-based lexers fast enough to process megabytes of source code in milliseconds.

The standard lexer generator workflow codifies this pipeline: you write regular expression rules, the tool (Flex, re2c, Ragel) runs Thompson construction, computes ε-closures to build the NFA, runs subset construction to produce the DFA, then applies Hopcroft's minimization algorithm to reduce the DFA to its smallest equivalent form. The minimized DFA is then compiled into a table of integers (a two-dimensional array indexed by current state and input character, returning the next state) or into a switch-statement dispatch chain that a C compiler can further optimize into a jump table. Modern tools like `re2c` generate the second form by default because modern CPUs branch-predict switch-dispatch chains more reliably than they cache large transition tables.

### Context-Free Grammars and the Parsing Problem

A Context-Free Grammar (CFG) is a four-tuple G = (V, Σ, R, S) where V is a finite set of nonterminal symbols, Σ is the terminal alphabet (the token kinds produced by the lexer), R is a finite set of production rules of the form A → α where A ∈ V and α ∈ (V ∪ Σ)*, and S ∈ V is the distinguished start symbol. A CFG generates a language by applying productions starting from S, substituting nonterminals with their right-hand sides, until a string of terminals is produced. The language L(G) is the set of all terminal strings derivable from S.

The fundamental parsing problem is the inverse of derivation: given a token stream w and a grammar G, determine whether w ∈ L(G), and if so, construct the derivation. The two canonical strategies for solving this problem are **top-down parsing**, which starts at S and attempts to expand nonterminals to match the input, and **bottom-up parsing**, which starts at the input tokens and attempts to reduce sequences of symbols back to S. These two strategies give rise to the LL and LR parser families respectively, and the choice between them is one of the most consequential decisions in compiler frontend design.

The LL strategy reads the input Left-to-right and produces a Leftmost derivation. At each step, the parser looks at the current lookahead token and uses it to decide which production to apply to the leftmost unexpanded nonterminal. The LR strategy also reads input Left-to-right but produces a Rightmost derivation in reverse. At each step the parser either shifts the next token onto a stack or reduces the top of the stack to a nonterminal by applying a production rule in reverse. The critical invariant is that LR(k) parsers recognize a strictly larger class of grammars than LL(k) parsers for the same lookahead k, because bottom-up parsers can delay decisions until they have seen more context. This is why production-grade parser generators (Yacc, Bison, LALR, Menhir) are almost universally LR-based, while hand-written parsers tend to be recursive-descent LL(1) or LL(*) for the sake of readability and error recovery.

---

## 2. Core Architecture & Mechanics

### The Lexer Engine: From Characters to Tokens

A production lexer has three architectural layers that are worth examining at the implementation level. The first layer is the **buffer management system**. Modern lexers do not read character by character from a file descriptor; that would be catastrophically slow due to syscall overhead. Instead, they maintain a double-buffer of typically 4096 or 8192 bytes, filling one half while scanning the other. Two pointers into this buffer are maintained: `lexeme_start` marks the beginning of the current token candidate, and `forward` advances through characters during DFA simulation. When `forward` crosses the buffer boundary, the buffer is refilled. When a token is recognized, `lexeme_start` is advanced to `forward`. This two-pointer scheme is the standard technique described in the Dragon Book and implemented in every serious hand-written lexer.

The second layer is the **DFA simulation loop**, which in its `re2c`-generated form looks approximately like this:

```c
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

typedef enum {
    TOK_IDENT,
    TOK_INT_LIT,
    TOK_PLUS,
    TOK_MINUS,
    TOK_STAR,
    TOK_SLASH,
    TOK_LPAREN,
    TOK_RPAREN,
    TOK_ASSIGN,
    TOK_EQ,
    TOK_GEQ,
    TOK_GT,
    TOK_LEQ,
    TOK_LT,
    TOK_SEMICOLON,
    TOK_EOF,
    TOK_UNKNOWN
} TokenKind;

typedef struct {
    TokenKind kind;
    const char *start;
    uint32_t   length;
    uint32_t   line;
    uint32_t   col;
} Token;

typedef struct {
    const char *cursor;
    const char *limit;
    const char *marker;      /* re2c YYMARKER for longest-match backtrack */
    uint32_t    line;
    uint32_t    col;
} LexerState;

void lexer_init(LexerState *ls, const char *src, size_t len) {
    ls->cursor = src;
    ls->limit  = src + len;
    ls->marker = src;
    ls->line   = 1;
    ls->col    = 1;
}

/*
 * re2c source rule (conceptual, would be in a .re file):
 *
 *   identifier = [a-zA-Z_][a-zA-Z0-9_]*;
 *   int_lit    = [0-9]+;
 *   whitespace = [ \t\r\n]+;
 *
 *   /*!re2c
 *       re2c:define:YYCTYPE  = char;
 *       re2c:define:YYCURSOR = ls->cursor;
 *       re2c:define:YYMARKER = ls->marker;
 *       re2c:define:YYLIMIT  = ls->limit;
 *
 *       identifier { tok->kind = TOK_IDENT; return; }
 *       int_lit    { tok->kind = TOK_INT_LIT; return; }
 *       "+"        { tok->kind = TOK_PLUS; return; }
 *       "-"        { tok->kind = TOK_MINUS; return; }
 *       "*"        { tok->kind = TOK_STAR; return; }
 *       "/"        { tok->kind = TOK_SLASH; return; }
 *       "("        { tok->kind = TOK_LPAREN; return; }
 *       ")"        { tok->kind = TOK_RPAREN; return; }
 *       "="        { tok->kind = TOK_ASSIGN; return; }
 *       "=="       { tok->kind = TOK_EQ; return; }
 *       ">="       { tok->kind = TOK_GEQ; return; }
 *       ">"        { tok->kind = TOK_GT; return; }
 *       "<="       { tok->kind = TOK_LEQ; return; }
 *       "<"        { tok->kind = TOK_LT; return; }
 *       ";"        { tok->kind = TOK_SEMICOLON; return; }
 *       [ \t\r\n]+ { ls->line++; goto lex_start; }  // simplified
 *       "\000"     { tok->kind = TOK_EOF; return; }
 *       *          { tok->kind = TOK_UNKNOWN; return; }
 *   *\/
 *
 * The hand-expanded version below shows the generated structure explicitly.
 */

Token lexer_next(LexerState *ls) {
    Token tok;
    const char *start;

lex_start:
    start       = ls->cursor;
    tok.start   = start;
    tok.line    = ls->line;
    tok.col     = ls->col;

    if (ls->cursor >= ls->limit) {
        tok.kind   = TOK_EOF;
        tok.length = 0;
        return tok;
    }

    unsigned char c = (unsigned char)*ls->cursor;

    /* Whitespace and newline skip */
    if (c == ' ' || c == '\t' || c == '\r') {
        ls->cursor++;
        ls->col++;
        goto lex_start;
    }
    if (c == '\n') {
        ls->cursor++;
        ls->line++;
        ls->col = 1;
        goto lex_start;
    }

    /* Identifier or keyword: [a-zA-Z_][a-zA-Z0-9_]* */
    if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_') {
        do {
            ls->cursor++;
            ls->col++;
            c = (unsigned char)*ls->cursor;
        } while ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                 (c >= '0' && c <= '9') || c == '_');
        tok.kind   = TOK_IDENT;
        tok.length = (uint32_t)(ls->cursor - start);
        return tok;
    }

    /* Integer literal: [0-9]+ */
    if (c >= '0' && c <= '9') {
        do {
            ls->cursor++;
            ls->col++;
            c = (unsigned char)*ls->cursor;
        } while (c >= '0' && c <= '9');
        tok.kind   = TOK_INT_LIT;
        tok.length = (uint32_t)(ls->cursor - start);
        return tok;
    }

    /* Single and double-character operators */
    ls->cursor++;
    ls->col++;
    switch (c) {
        case '+': tok.kind = TOK_PLUS;      break;
        case '-': tok.kind = TOK_MINUS;     break;
        case '*': tok.kind = TOK_STAR;      break;
        case '/': tok.kind = TOK_SLASH;     break;
        case '(': tok.kind = TOK_LPAREN;    break;
        case ')': tok.kind = TOK_RPAREN;    break;
        case ';': tok.kind = TOK_SEMICOLON; break;
        case '=':
            if (*ls->cursor == '=') { ls->cursor++; ls->col++; tok.kind = TOK_EQ; }
            else                    { tok.kind = TOK_ASSIGN; }
            break;
        case '>':
            if (*ls->cursor == '=') { ls->cursor++; ls->col++; tok.kind = TOK_GEQ; }
            else                    { tok.kind = TOK_GT; }
            break;
        case '<':
            if (*ls->cursor == '=') { ls->cursor++; ls->col++; tok.kind = TOK_LEQ; }
            else                    { tok.kind = TOK_LT; }
            break;
        default:
            tok.kind = TOK_UNKNOWN;
            break;
    }

    tok.length = (uint32_t)(ls->cursor - start);
    return tok;
}
```

The third layer is the **symbol table and string interning system**. Every time the lexer recognizes an identifier, it must decide whether to store the raw string or to intern it. String interning maps every unique identifier lexeme to a single canonical pointer, so that subsequent comparisons between identifiers become pointer comparisons rather than `strcmp` calls. A production implementation uses an open-addressing hash table keyed on the lexeme bytes, returning an index or pointer into a contiguous string arena. The arena stores each unique string once, eliminating both repeated heap allocations and cache-miss-inducing pointer chasing during the parse phase.

### The Parser Engine: LL(1) Recursive Descent

Recursive-descent parsing is the dominant approach for hand-written production compilers because it maps naturally to the structure of the grammar, produces readable and maintainable code, and permits excellent error recovery through explicit error-handling logic at each nonterminal's parsing function.

The core invariant of recursive descent is that **each nonterminal in the grammar corresponds to exactly one function** in the parser, and each production rule for that nonterminal corresponds to a branch within that function. The parser maintains a single-token lookahead — the current token returned by the lexer — and uses it to select the correct production without consuming the token. Consider a minimal arithmetic grammar:

```
expr    ::= term (('+' | '-') term)*
term    ::= factor (('*' | '/') factor)*
factor  ::= INT_LIT | IDENT | '(' expr ')'
```

This grammar is LL(1) because a single lookahead token is sufficient to determine which production to apply at every point. The corresponding C implementation, integrated with the lexer above, is:

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

/* ---- AST node types ---- */

typedef enum {
    AST_INT_LIT,
    AST_IDENT,
    AST_BINOP,
} AstKind;

typedef struct AstNode AstNode;

struct AstNode {
    AstKind   kind;
    union {
        struct { int64_t value; }                       int_lit;
        struct { const char *name; uint32_t name_len; } ident;
        struct { char op; AstNode *left; AstNode *right; } binop;
    };
};

/* ---- Parser state ---- */

typedef struct {
    LexerState *ls;
    Token       current;
    bool        had_error;
} Parser;

static AstNode *parse_expr(Parser *p);
static AstNode *parse_term(Parser *p);
static AstNode *parse_factor(Parser *p);

static AstNode *ast_alloc(AstKind kind) {
    AstNode *n = calloc(1, sizeof(AstNode));
    if (!n) { fprintf(stderr, "OOM in ast_alloc\n"); exit(1); }
    n->kind = kind;
    return n;
}

static void parser_advance(Parser *p) {
    p->current = lexer_next(p->ls);
}

static bool parser_check(Parser *p, TokenKind kind) {
    return p->current.kind == kind;
}

static bool parser_match(Parser *p, TokenKind kind) {
    if (parser_check(p, kind)) {
        parser_advance(p);
        return true;
    }
    return false;
}

static void parser_expect(Parser *p, TokenKind kind, const char *msg) {
    if (!parser_match(p, kind)) {
        fprintf(stderr, "Parse error at line %u col %u: %s\n",
                p->current.line, p->current.col, msg);
        p->had_error = true;
    }
}

void parser_init(Parser *p, LexerState *ls) {
    p->ls        = ls;
    p->had_error = false;
    parser_advance(p);   /* prime the lookahead */
}

/*
 * expr ::= term (('+' | '-') term)*
 *
 * Left-associative binary operator loop. Each iteration wraps the
 * accumulated left subtree as the left child of a new BINOP node.
 */
static AstNode *parse_expr(Parser *p) {
    AstNode *left = parse_term(p);

    while (parser_check(p, TOK_PLUS) || parser_check(p, TOK_MINUS)) {
        char op = (p->current.kind == TOK_PLUS) ? '+' : '-';
        parser_advance(p);
        AstNode *right = parse_term(p);

        AstNode *node  = ast_alloc(AST_BINOP);
        node->binop.op    = op;
        node->binop.left  = left;
        node->binop.right = right;
        left = node;
    }

    return left;
}

/*
 * term ::= factor (('*' | '/') factor)*
 */
static AstNode *parse_term(Parser *p) {
    AstNode *left = parse_factor(p);

    while (parser_check(p, TOK_STAR) || parser_check(p, TOK_SLASH)) {
        char op = (p->current.kind == TOK_STAR) ? '*' : '/';
        parser_advance(p);
        AstNode *right = parse_factor(p);

        AstNode *node  = ast_alloc(AST_BINOP);
        node->binop.op    = op;
        node->binop.left  = left;
        node->binop.right = right;
        left = node;
    }

    return left;
}

/*
 * factor ::= INT_LIT | IDENT | '(' expr ')'
 */
static AstNode *parse_factor(Parser *p) {
    if (parser_check(p, TOK_INT_LIT)) {
        AstNode *node = ast_alloc(AST_INT_LIT);
        /* Atoi-equivalent over the raw lexeme bytes */
        int64_t val = 0;
        for (uint32_t i = 0; i < p->current.length; i++) {
            val = val * 10 + (p->current.start[i] - '0');
        }
        node->int_lit.value = val;
        parser_advance(p);
        return node;
    }

    if (parser_check(p, TOK_IDENT)) {
        AstNode *node        = ast_alloc(AST_IDENT);
        node->ident.name     = p->current.start;
        node->ident.name_len = p->current.length;
        parser_advance(p);
        return node;
    }

    if (parser_match(p, TOK_LPAREN)) {
        AstNode *node = parse_expr(p);
        parser_expect(p, TOK_RPAREN, "expected ')' after expression");
        return node;
    }

    fprintf(stderr, "Parse error at line %u col %u: unexpected token\n",
            p->current.line, p->current.col);
    p->had_error = true;
    return ast_alloc(AST_INT_LIT);  /* error recovery: return a dummy node */
}

/* ---- Pretty-printer for the AST ---- */

void ast_print(const AstNode *node, int depth) {
    for (int i = 0; i < depth * 2; i++) putchar(' ');
    if (!node) { puts("<null>"); return; }

    switch (node->kind) {
        case AST_INT_LIT:
            printf("IntLit(%lld)\n", (long long)node->int_lit.value);
            break;
        case AST_IDENT:
            printf("Ident(%.*s)\n", (int)node->ident.name_len, node->ident.name);
            break;
        case AST_BINOP:
            printf("BinOp('%c')\n", node->binop.op);
            ast_print(node->binop.left,  depth + 1);
            ast_print(node->binop.right, depth + 1);
            break;
    }
}

/* ---- Driver ---- */

int main(void) {
    const char *src = "x + 42 * (y - 7)";
    LexerState ls;
    lexer_init(&ls, src, strlen(src));

    Parser p;
    parser_init(&p, &ls);

    AstNode *tree = parse_expr(&p);
    if (!p.had_error) {
        ast_print(tree, 0);
    }
    return p.had_error ? 1 : 0;
}
```

Compiling and running this program against `x + 42 * (y - 7)` produces the following AST printout, confirming correct operator precedence (multiplication binds tighter than addition, and the parenthesized sub-expression is correctly isolated):

```
BinOp('+')
  Ident(x)
  BinOp('*')
    IntLit(42)
    BinOp('-')
      Ident(y)
      IntLit(7)
```

### LR Parsing Mechanics: Shift-Reduce Automata

Where recursive descent is a *predictive* strategy — predicting which production to expand before consuming a token — LR parsing is a *deferred decision* strategy. The parser accumulates tokens on a stack until it has seen enough context to identify and reduce a complete right-hand side. This ability to delay recognition is precisely what allows LR parsers to handle a larger class of grammars, including left-recursive productions that would cause infinite recursion in an LL parser.

The LR parsing algorithm maintains two parallel stacks: a **symbol stack** holding grammar symbols (terminals and nonterminals), and a **state stack** holding DFA states. At each step the parser takes one of two actions. A *shift* action pushes the current lookahead token onto the symbol stack, pushes the DFA's next state onto the state stack, and advances the lexer. A *reduce* action pops a number of symbols equal to the length of a production's right-hand side, then pushes the production's left-hand side nonterminal and transitions to a new state determined by the *goto* table.

These decisions are encoded in two tables — the **action table** (indexed by state and lookahead token) and the **goto table** (indexed by state and nonterminal) — which are computed statically by the parser generator from the grammar. LALR(1), the construction used by Bison, computes these tables from *merged* LR(1) item sets: items whose core (the production and dot position) are identical are merged even if their lookahead sets differ. This keeps the table size proportional to the number of grammar states rather than the number of LR(1) items, which can be exponentially larger. The tradeoff is that LALR(1) may introduce spurious reduce-reduce conflicts that a full LR(1) construction would not, though in practice the grammars of real programming languages are designed to avoid this.

The anatomy of the LR automaton for even a small grammar is best understood through a concrete parse trace. Given the grammar:

```
(1) E → E + T
(2) E → T
(3) T → T * F
(4) T → F
(5) F → ( E )
(6) F → id
```

and the input `id + id * id`, the LR(1) parse proceeds as follows:

```
Stack (states)    Symbol Stack       Input Remaining      Action
─────────────────────────────────────────────────────────────────────
[0]               []                 id + id * id $       Shift id → state 5
[0, 5]            [id]               + id * id $          Reduce F → id  (rule 6)
[0, 3]            [F]                + id * id $          Reduce T → F   (rule 4)
[0, 2]            [T]                + id * id $          Reduce E → T   (rule 2)
[0, 1]            [E]                + id * id $          Shift + → state 6
[0, 1, 6]         [E, +]             id * id $            Shift id → state 5
[0, 1, 6, 5]      [E, +, id]         * id $               Reduce F → id  (rule 6)
[0, 1, 6, 3]      [E, +, F]          * id $               Reduce T → F   (rule 4)
[0, 1, 6, 9]      [E, +, T]          * id $               Shift * → state 7
[0, 1, 6, 9, 7]   [E, +, T, *]       id $                 Shift id → state 5
[0, 1, 6, 9, 7,5] [E, +, T, *, id]   $                    Reduce F → id  (rule 6)
[0, 1, 6, 9, 7,10][E, +, T, *, F]    $                    Reduce T → T*F (rule 3)
[0, 1, 6, 9]      [E, +, T]          $                    Reduce E → E+T (rule 1)
[0, 1]            [E]                $                    Accept
```

Notice how the LR automaton correctly handles left recursion in rule (1) and enforces `*` over `+` precedence through the state machine's deferred reduce decisions, without any special-case precedence annotations. The grammar's structure encodes precedence directly.

### Parse Tree vs. Abstract Syntax Tree

The distinction between a **parse tree** (also called a concrete syntax tree or CST) and an **abstract syntax tree** (AST) is architecturally significant. A parse tree is a faithful, lossless record of every production rule applied during the parse: it includes every intermediate nonterminal, every parenthesis token, every comma delimiter. It is isomorphic to the derivation. An AST, by contrast, discards all syntactic scaffolding and retains only the semantically essential structure. Parentheses, which exist only to encode precedence for the parser, disappear entirely in the AST because precedence is already encoded in the tree's nesting structure. Delimiter tokens like semicolons and commas vanish because their positional information is implied by the node's children.

Production compilers almost universally build ASTs, not parse trees, because every downstream pass — name resolution, type inference, borrow checking, IR lowering — operates on tree structure. Carrying parse-tree nodes through those passes would impose constant overhead: every pass would need to skip syntactic scaffolding nodes to reach the semantic content. The transition from parse tree to AST is typically performed during the parse itself, in the semantic actions attached to each production rule, rather than as a separate tree-transformation pass.

```
Parse tree for: x + 42 * (y - 7)         AST for: x + 42 * (y - 7)

        E                                        BinOp(+)
       /|\                                      /         \
      E + T                                 Ident(x)     BinOp(*)
      |   |\ \                                           /         \
      T   T  *  F                                   IntLit(42)   BinOp(-)
      |   |     |\ \                                            /         \
      F  id   ( E )                                         Ident(y)   IntLit(7)
      |       /|\
      x      E - T
             |   |
             T   F
             |   |
             F  id
             |   |
            id   7
             |
             y
```

The parse tree's depth and node count scales with the grammar's production count, while the AST's depth scales with the program's semantic nesting. For a deeply factored grammar with five or six levels of precedence, the parse tree can be six times taller than the AST it encodes.

### Syntax-Directed Translation

Syntax-directed translation (SDT) is the mechanism by which the parser computes values alongside the structural recognition, associating **attributes** with grammar symbols and **semantic actions** with productions. An attribute is simply a value computed at a parse-tree node: an integer, a type, a pointer to an AST node, a code fragment. When every attribute of a nonterminal can be computed from the attributes of its children in the same production, the attribute is **synthesized**, and computation flows bottom-up from leaves to root. When an attribute depends on the parent or sibling symbols, it is **inherited**, and computation flows top-down.

Synthesized attributes integrate naturally into both recursive-descent parsers (the parsing function returns the computed value) and LR parsers (the value is computed in the reduce action and pushed onto a value stack parallel to the state stack). Inherited attributes in LR parsers require more care because the LR automaton processes symbols bottom-up and cannot conveniently pass information from parent to child during the parse; they typically require additional grammar rules or post-parse tree annotations. This asymmetry is why type information in real language front-ends is often computed in a separate tree walk after the parse rather than during it.

The invariant of syntax-directed translation is that **every attribute computation is attached to a specific production rule and executes precisely when that rule is recognized**. This determinism is what makes SDT-based front-ends predictable: the semantic action for a production fires exactly once per occurrence of that production in the derivation, in a well-defined order relative to the input stream.

---

## 3. High-Performance Optimization & Failure Modes

### Lexer Performance: Eliminating Memory and Branch Overhead

The most significant performance concern in production lexers is not the DFA transition cost but the **memory traffic** associated with token allocation. A naive lexer that heap-allocates a `Token` struct for every lexeme will spend the majority of its time in `malloc` and cache-miss-prone pointer indirection. The standard mitigation is to separate token *identity* (the kind and location, stored in a compact struct) from token *content* (the lexeme string, stored in the input buffer itself or in a string arena). The `Token` struct shown earlier stores only a pointer into the original source buffer and a length, never a heap-allocated copy of the lexeme. The source buffer itself is memory-mapped from the file at startup, so no copying occurs during lexing at all.

A further optimization, used in Clang's `Lexer` and Rust's `rustc` lexer, is to separate the **fast path** (ASCII identifiers, single-character punctuation, integer literals) from the **slow path** (UTF-8 identifiers, raw string literals, block comments). The fast path is a tightly packed switch statement that the CPU branch-predictor learns quickly. The slow path handles the rare cases without penalizing common-case throughput. Clang's lexer is additionally careful to avoid any function call overhead on the hot path, inlining the character classification predicates directly into the scan loop.

For tokenizing very large source files (500,000+ lines, as seen in generated code or large translation units), **parallel lexing** is possible because lexer states have bounded lookahead. The source can be split into chunks, each chunk can be lexed independently with a small overlap to handle tokens that straddle chunk boundaries, and the token streams can be concatenated. This is the approach taken by some parallel parser projects, though it adds engineering complexity that is rarely justified for typical source files.

### Parser Failure Modes and Error Recovery

The most dangerous failure mode for a parser in production use is **cascading errors**: a single syntax mistake causes the parser to lose synchronization with the input, triggering dozens of spurious follow-on error messages that obscure the real mistake. The standard mitigation in recursive-descent parsers is **panic-mode recovery** combined with **synchronization sets**. When an unexpected token is encountered, the parser discards tokens from the input until it finds a token in the synchronization set for the current context — typically statement-terminating tokens like `;` or block-closing tokens like `}`. This anchors the parser to a known point in the grammar and allows parsing to resume from a consistent state.

Clang's approach is more sophisticated: it maintains a **recovery context** at each call level and uses heuristics about likely insertions and deletions to synthesize hypothetical corrections, allowing the parser to continue with a modified token stream and report the error precisely at the point of likely programmer intent. GCC historically used a simpler synchronization approach and was notorious for confusing error cascades; Clang's improvement in diagnostics was a significant factor in its adoption.

A subtler failure mode is **ambiguous grammars**. A grammar is ambiguous if some token string has more than one parse tree under it. The classic example is the dangling-else problem: in `if (a) if (b) s1 else s2`, the `else` can syntactically attach to either `if`. Both LR and LL parsers resolve this by convention (the `else` attaches to the nearest unmatched `if`), but the ambiguity is a property of the grammar, not the parser. LALR parser generators like Bison will report a **shift-reduce conflict** for the dangling-else grammar, requiring the programmer to annotate the grammar with explicit precedence and associativity declarations to resolve it. These declarations change the generated action table but do not change the grammar itself; they are a shorthand for grammar refactoring.

**Reduce-reduce conflicts** in LALR parsers are more serious because they indicate that two distinct production rules match the same right-hand-side sequence in the same state with the same lookahead, and the parser cannot determine which semantic action to execute. This often signals a genuine ambiguity in the language design — a string that has two semantically distinct interpretations — and must be resolved by refactoring the grammar, not merely by adding precedence annotations.

### FIRST and FOLLOW Sets: The LL(1) Feasibility Check

Before committing to a recursive-descent architecture, you must verify that the grammar is LL(1) by computing its FIRST and FOLLOW sets. The FIRST(α) set for a string α of grammar symbols is the set of terminals that can begin a string derivable from α. The FOLLOW(A) set for a nonterminal A is the set of terminals that can appear immediately to the right of A in any sentential form derivable from the start symbol.

The LL(1) condition requires that for every nonterminal A with productions A → α₁ | α₂ | ... | αₙ, the sets FIRST(αᵢ) ∩ FIRST(αⱼ) must be empty for all i ≠ j, and if αᵢ can derive ε (the empty string), then FIRST(αⱼ) ∩ FOLLOW(A) must also be empty. If these conditions hold, then the single lookahead token is always sufficient to select the correct production unambiguously. If they do not hold — typically because the grammar is left-recursive or has common prefixes — the grammar must be transformed by **left-recursion elimination** and **left-factoring** before recursive descent will work.

Left-recursion elimination converts a production like `E → E + T | T` into `E → T E'` and `E' → + T E' | ε`, eliminating the infinite recursion while preserving the language. Left-factoring extracts common prefixes into a new nonterminal, deferring the branching decision until the prefix has been consumed and additional lookahead is available. These transformations are mechanical and well-defined, but they produce grammars that are less readable and can degrade the quality of error messages, which is one reason many production compiler authors prefer to write LR grammars and use a table-driven parser generator rather than applying these transformations manually.

### Rust Implementation: A Type-Safe Token Arena

For engineers moving from C to Rust in a compiler project, the token and AST representation benefits substantially from Rust's ownership model. The following Rust implementation demonstrates a bump-allocator arena for AST nodes, which eliminates individual heap allocations and allows the entire AST to be dropped in O(1) by freeing the arena's backing memory.

```rust
use std::cell::Cell;

/// A bump allocator for AST nodes. Allocates from a Vec<u8> backing store.
/// All nodes live for the lifetime 'arena, enforced by the borrow checker.
pub struct Arena {
    buf: Vec<u8>,
    offset: Cell<usize>,
}

impl Arena {
    pub fn new(capacity: usize) -> Self {
        Arena {
            buf: vec![0u8; capacity],
            offset: Cell::new(0),
        }
    }

    /// Allocate `size` bytes aligned to `align` bytes.
    /// Returns a raw pointer valid for the lifetime of the Arena.
    pub fn alloc_raw(&self, size: usize, align: usize) -> *mut u8 {
        let current = self.offset.get();
        let aligned = (current + align - 1) & !(align - 1);
        let next    = aligned + size;
        assert!(next <= self.buf.capacity(), "arena exhausted");
        self.offset.set(next);
        // SAFETY: aligned is within buf's allocation, and we have exclusive
        // logical access to this slice because Arena is !Sync.
        unsafe { self.buf.as_ptr().add(aligned) as *mut u8 }
    }

    /// Allocate a single value of type T in the arena.
    /// The returned reference borrows from the arena's lifetime.
    pub fn alloc<T>(&self, value: T) -> &T {
        let ptr = self.alloc_raw(
            std::mem::size_of::<T>(),
            std::mem::align_of::<T>(),
        ) as *mut T;
        // SAFETY: ptr is properly aligned and points to uninitialized memory
        // within the arena's exclusive region. We write exactly one T and
        // immediately convert to a shared reference bounded by 'self lifetime.
        unsafe {
            ptr.write(value);
            &*ptr
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TokenKind {
    Ident,
    IntLit,
    Plus,
    Minus,
    Star,
    Slash,
    LParen,
    RParen,
    Semicolon,
    Eof,
    Unknown,
}

#[derive(Debug, Clone, Copy)]
pub struct Token<'src> {
    pub kind:   TokenKind,
    pub lexeme: &'src str,
    pub line:   u32,
    pub col:    u32,
}

/// The AST node type. Nodes reference the source buffer for identifiers
/// and reference other nodes via arena lifetimes — no heap allocation,
/// no reference counting, no GC.
#[derive(Debug)]
pub enum Expr<'arena, 'src> {
    IntLit(i64),
    Ident(&'src str),
    BinOp {
        op:    char,
        left:  &'arena Expr<'arena, 'src>,
        right: &'arena Expr<'arena, 'src>,
    },
}

pub struct Lexer<'src> {
    src:    &'src [u8],
    cursor: usize,
    line:   u32,
    col:    u32,
}

impl<'src> Lexer<'src> {
    pub fn new(src: &'src str) -> Self {
        Lexer { src: src.as_bytes(), cursor: 0, line: 1, col: 1 }
    }

    fn peek(&self) -> Option<u8> {
        self.src.get(self.cursor).copied()
    }

    fn advance(&mut self) -> Option<u8> {
        let c = self.src.get(self.cursor).copied();
        if let Some(ch) = c {
            self.cursor += 1;
            if ch == b'\n' { self.line += 1; self.col = 1; }
            else            { self.col  += 1; }
        }
        c
    }

    pub fn next_token(&mut self) -> Token<'src> {
        // Skip whitespace
        while matches!(self.peek(), Some(b' ') | Some(b'\t') | Some(b'\r') | Some(b'\n')) {
            self.advance();
        }

        let start = self.cursor;
        let line  = self.line;
        let col   = self.col;

        let kind = match self.advance() {
            None       => TokenKind::Eof,
            Some(b'+') => TokenKind::Plus,
            Some(b'-') => TokenKind::Minus,
            Some(b'*') => TokenKind::Star,
            Some(b'/') => TokenKind::Slash,
            Some(b'(') => TokenKind::LParen,
            Some(b')') => TokenKind::RParen,
            Some(b';') => TokenKind::Semicolon,
            Some(c) if c.is_ascii_alphabetic() || c == b'_' => {
                while matches!(self.peek(),
                    Some(c) if c.is_ascii_alphanumeric() || c == b'_') {
                    self.advance();
                }
                TokenKind::Ident
            }
            Some(c) if c.is_ascii_digit() => {
                while matches!(self.peek(), Some(c) if c.is_ascii_digit()) {
                    self.advance();
                }
                TokenKind::IntLit
            }
            _ => TokenKind::Unknown,
        };

        // SAFETY: source is valid UTF-8 (enforced by &str at construction),
        // and start..self.cursor is a valid byte range within it.
        let lexeme = unsafe {
            std::str::from_utf8_unchecked(&self.src[start..self.cursor])
        };

        Token { kind, lexeme, line, col }
    }
}

pub struct Parser<'arena, 'src> {
    lexer:   Lexer<'src>,
    current: Token<'src>,
    arena:   &'arena Arena,
    error:   bool,
}

impl<'arena, 'src> Parser<'arena, 'src> {
    pub fn new(src: &'src str, arena: &'arena Arena) -> Self {
        let mut lexer = Lexer::new(src);
        let current   = lexer.next_token();
        Parser { lexer, current, arena, error: false }
    }

    fn advance(&mut self) {
        self.current = self.lexer.next_token();
    }

    fn check(&self, kind: TokenKind) -> bool {
        self.current.kind == kind
    }

    fn eat(&mut self, kind: TokenKind) -> bool {
        if self.check(kind) { self.advance(); true } else { false }
    }

    fn expect(&mut self, kind: TokenKind, msg: &str) {
        if !self.eat(kind) {
            eprintln!("error at {}:{}: {}", self.current.line, self.current.col, msg);
            self.error = true;
        }
    }

    pub fn parse_expr(&mut self) -> &'arena Expr<'arena, 'src> {
        let mut left = self.parse_term();
        loop {
            let op = if self.check(TokenKind::Plus)  { '+' }
                     else if self.check(TokenKind::Minus) { '-' }
                     else { break };
            self.advance();
            let right = self.parse_term();
            left = self.arena.alloc(Expr::BinOp { op, left, right });
        }
        left
    }

    fn parse_term(&mut self) -> &'arena Expr<'arena, 'src> {
        let mut left = self.parse_factor();
        loop {
            let op = if self.check(TokenKind::Star)  { '*' }
                     else if self.check(TokenKind::Slash) { '/' }
                     else { break };
            self.advance();
            let right = self.parse_factor();
            left = self.arena.alloc(Expr::BinOp { op, left, right });
        }
        left
    }

    fn parse_factor(&mut self) -> &'arena Expr<'arena, 'src> {
        if self.check(TokenKind::IntLit) {
            let val: i64 = self.current.lexeme.parse().unwrap_or(0);
            self.advance();
            return self.arena.alloc(Expr::IntLit(val));
        }
        if self.check(TokenKind::Ident) {
            let name = self.current.lexeme;
            self.advance();
            return self.arena.alloc(Expr::Ident(name));
        }
        if self.eat(TokenKind::LParen) {
            let node = self.parse_expr();
            self.expect(TokenKind::RParen, "expected ')'");
            return node;
        }
        eprintln!("error at {}:{}: unexpected token '{}'",
            self.current.line, self.current.col, self.current.lexeme);
        self.error = true;
        self.arena.alloc(Expr::IntLit(0))
    }

    pub fn had_error(&self) -> bool { self.error }
}

fn main() {
    let src   = "x + 42 * (y - 7)";
    let arena = Arena::new(1024 * 64);  // 64 KiB for a small expression
    let mut parser = Parser::new(src, &arena);
    let tree  = parser.parse_expr();
    if !parser.had_error() {
        println!("{:#?}", tree);
    }
}
```

The lifetime parameters `'arena` and `'src` in the Rust implementation are not ceremony; they are mechanically enforced invariants. `'src` guarantees that identifier lexemes borrow directly from the source string without copying, and are valid for as long as the source string lives. `'arena` guarantees that AST node references are valid for as long as the arena lives, and that the arena cannot be dropped while any node reference is live. The borrow checker rejects any code that would violate these invariants at compile time, eliminating an entire class of use-after-free bugs that C implementations must guard against through discipline and ASan instrumentation.

### Diagnosing Lexer and Parser Bugs in Production

When a parser in production begins misclassifying tokens or producing incorrect ASTs, the diagnostic workflow proceeds in three steps. First, **isolate the token stream** by inserting a debug dump between the lexer and the parser, printing each `(kind, lexeme, line:col)` triple on a separate line. This immediately reveals whether the problem is in the lexer (wrong token kinds or boundaries) or the parser (correct tokens but wrong tree shape). Second, if the bug is in the lexer, **trace the DFA transitions** for the failing input by running the lexer with a character-level trace enabled, verifying that each state transition matches the expected DFA diagram. For `re2c`-generated lexers, this means annotating the generated C with logging before each state transition — tedious but definitive. Third, if the bug is in the parser, **trace the parse stack** for the failing input, printing the state stack and symbol stack at each shift and reduce step. For recursive-descent parsers, this is equivalent to printing the call stack at each function entry and exit, which a debugger watchpoint or a `--trace-parse` flag can automate.

The most common lexer bug in practice is an incorrect **rule priority ordering** when two rules can match the same prefix. In Flex-style lexers, the first matching rule wins when two rules match a string of equal length. If a keyword like `if` and the identifier rule `[a-zA-Z_][a-zA-Z0-9_]*` are both listed, the keyword rule must appear *before* the identifier rule, or identifiers named `iff` will tokenize as `TOK_IF` followed by `TOK_IDENT(f)`. The correct fix is to treat keywords as identifiers during lexing and resolve them in a **keyword hash table lookup** immediately after the identifier rule fires, which is the approach taken by Clang: every identifier is initially classified as `tok::identifier`, then the keyword table maps the lexeme to the correct keyword token kind in O(1) with a perfect hash function.

The most common parser bug is an off-by-one in the precedence encoding, usually manifesting as an expression like `a + b * c` parsing as `(a + b) * c`. The diagnostic is to print the AST and check whether multiplication's node is the parent or child of addition's node: in a correctly precedenced parse, `*` must always be deeper in the tree than `+` for expressions without explicit parenthesization. If the precedence is wrong in a recursive-descent parser, the fix is to reorder the parsing functions so that lower-precedence operators are parsed at the top level and higher-precedence operators are parsed deeper in the call chain, as in the `parse_expr` / `parse_term` / `parse_factor` structure shown throughout this lesson. If the precedence is wrong in an LR parser generated by Bison, the fix is to adjust the `%left`, `%right`, and `%nonassoc` declarations so that higher-precedence tokens appear later in the precedence hierarchy — Bison's convention is that declarations later in the file have higher precedence.

---

The machinery covered in this lesson — DFA-based lexers, recursive-descent and LR parsers, synthesized attributes, and the structural invariants that separate each phase — constitutes the foundation on which every subsequent compiler pass depends. The semantic analyzer, type checker, and IR generator in the following lessons all receive their input as the AST produced here. Getting this phase right, with clean token boundaries, correct operator precedence, robust error recovery, and efficient memory layout, is not preliminary work. It is the first and most pervasive correctness requirement of the entire compiler, because every downstream computation is only as reliable as the structure it receives.
