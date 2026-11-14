/* fastest-primes — C alternative (odd-only sieve of Eratosthenes).
   Build & run: cc -O2 -o primes main.c && ./primes
   Reads N on stdin, prints the count of primes <= N. */
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char buf[32];
    if (!fgets(buf, sizeof buf, stdin)) return 1;
    long n = strtol(buf, NULL, 10);
    if (n < 2) { puts("0"); return 0; }
    long long m = (n - 1) / 2;         /* odds 3,5,...: index i <-> 2i+3 */
    unsigned char *comp = calloc(m ? (size_t)m : 1, 1);
    if (!comp) return 1;
    long long count = 1;               /* the prime 2 */
    for (long long i = 0; i < m; i++) {
        if (!comp[i]) {
            long long p = 2 * i + 3;
            count++;
            for (long long j = (p * p - 3) / 2; j < m; j += p) comp[j] = 1;
        }
    }
    printf("%ld\n", count);
    free(comp);
    return 0;
}
