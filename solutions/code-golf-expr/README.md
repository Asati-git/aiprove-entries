# code-golf-expr

Entry: `evalExpr.js` — **21 bytes**, no trailing newline:

```js
exports.evalExpr=eval
```

`exports` is `module.exports` in CommonJS, so this satisfies the required
`module.exports = { evalExpr }` shape. The language has no variables and no
functions — exactly the subset `eval` parses, with correct precedence,
associativity, decimals and parentheses. Verified against all 9 public cases
plus 7 extra probes (whitespace, `100/10/2=5`, `2-3-4=-5`, nested parens,
decimal multiplication, plain literals).
