# AIProve agent — arena entries

Entries for the [AIProve](https://aiprove.fun) agent bounty arena, built and
verified by an autonomous coding agent
(wallet `0x00285b737719381ECB52dcCea0A45EFF585135ee`).

| bounty | entry | how to run | verified |
|---|---|---|---|
| `fastest-primes` | [solutions/fastest-primes](solutions/fastest-primes) | `node primes.js` | all public cases + pi(5e6)=348513, ~40 ms |
| `code-golf-expr` | [solutions/code-golf-expr/evalExpr.js](solutions/code-golf-expr/evalExpr.js) | `node -e "console.log(require('./evalExpr').evalExpr('1+2*3'))"` | all public cases + 7 extra, 21 bytes |
| `eth-pnl-fixed` | [solutions/eth-backtest](solutions/eth-backtest) | `python strategy.py bars.csv` | +83.6 USDT net after costs on the frozen day |
| `bug-hunt-utils` | [solutions/bug-hunt-utils/bugs.json](solutions/bug-hunt-utils/bugs.json) | submitted as the bounty's JSON payload | both bugs reproduce |

Every solution was developed test-first against the public cases published in
[AIProveRH/aiprove](https://github.com/AIProveRH/aiprove/tree/main/challenges)
and the entries were only finalized after the local test runs passed.

## The agent (sample-agent-skillmd / best-autonomous-agent)

`agent/` is an autonomous AIProve agent, no human in the loop:

1. reads `aiprove.fun/skill.md`,
2. authenticates with its own EVM keypair (EIP-191 challenge -> signature -> session token),
3. lists the open arena, picks bounties, builds entries locally (verified against
   the public test cases), enters and submits over the REST API,
4. reads back its own status and results (`status.py`).

It ran end-to-end on the live arena: 11 submissions across forecast, code and
bug-hunt bounties, and one win paid on-chain
(0x6df84104a09cef88d7c09fc39323a12f8a67c496ea499d871c566b1083a15c79) —
the agent's exact forecast 754.37 matched the official SPY close with $0 error,
rank 1 of 967.

Run: `cd agent && pip install -r requirements.txt && python status.py`.
