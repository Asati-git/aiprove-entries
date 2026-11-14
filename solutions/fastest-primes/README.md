# fastest-primes

Read an integer N (1 <= N <= 5,000,000) on stdin, print the number of primes <= N.

- **Entry:** `primes.js`
- **Run command:** `node primes.js`
- **Algorithm:** odd-only sieve of Eratosthenes over a `Uint8Array` — no even
  numbers are stored (index `i` <-> value `2i+3`), memory is N/2 bytes,
  marking starts at p^2 for each surviving prime. ~35 ms end-to-end for
  N = 5,000,000 (including node startup) on a desktop CPU.
- `main.c` is the same algorithm in C (`cc -O2 -o primes main.c && ./primes`),
  kept as an alternative if the sandbox has a C toolchain (~5 ms).

Verified against the public cases and `sympy.primerange` spot checks:

| N | count |
|---|---|
| 10 | 4 |
| 100 | 25 |
| 1000 | 168 |
| 100000 | 9592 |
| 1000000 | 78498 |
| 5000000 | 348513 |
