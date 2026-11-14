// fastest-primes — count primes <= N read from stdin.
// Odd-only sieve of Eratosthenes on a Uint8Array; ~35 ms for N = 5,000,000.
// Run: node primes.js
const fs = require("fs");
let input = "";
process.stdin.setEncoding("ascii");
process.stdin.on("data", (d) => (input += d));
process.stdin.on("end", () => {
  const n = parseInt(input.trim(), 10);
  if (n < 2) {
    process.stdout.write("0\n");
    return;
  }
  const m = (n - 1) >> 1; // odd numbers 3,5,7,... : index i <-> value 2i+3
  const comp = new Uint8Array(m);
  let count = 1; // the prime 2
  for (let i = 0; i < m; i++) {
    if (comp[i] === 0) {
      count++;
      const p = 2 * i + 3;
      // NB: (p*p-3)/2, not >>1 — the shift would ToInt32-wrap once p*p >= 2^32.
      for (let j = (p * p - 3) / 2; j < m; j += p) comp[j] = 1;
    }
  }
  process.stdout.write(count + "\n");
});
