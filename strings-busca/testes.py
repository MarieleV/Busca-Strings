import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from algoritmos import NaiveSearch, RabinKarpSearch, KMPSearch, BoyerMooreSearch

STRATEGIES = [NaiveSearch(), RabinKarpSearch(), KMPSearch(), BoyerMooreSearch()]

CASES = [
    # (texto, padrão, posições esperadas)
    ("AABAACAADAABAABA", "AABA",    [0, 9, 12]),
    ("abcabcabc",        "abc",     [0, 3, 6]),
    ("hello world",      "world",   [6]),
    ("aaaaaaa",          "aaa",     [0, 1, 2, 3, 4]),
    ("abcdef",           "xyz",     []),
    ("",                 "abc",     []),
    ("abc",              "",        []),
    ("GEEKS FOR GEEKS",  "GEEKS",   [0, 10]),
    ("aabaabaab",        "aab",     [0, 3, 6]),
    ("abcabdabc",        "abc",     [0, 6]),
]

PASS = "✅"
FAIL = "❌"
total = passed = 0

print("\n" + "═"*60)
print("  Busca por string | Conjunto de testes")
print("═"*60)

for strategy in STRATEGIES:
    print(f"\n── {strategy.name} ──────────────────────────────")
    for text, pat, expected in CASES:
        result = strategy.search(text, pat)
        ok = sorted(result.positions) == sorted(expected)
        status = PASS if ok else FAIL
        total += 1
        if ok:
            passed += 1
        label = f'"{text[:20]}{"…" if len(text)>20 else ""}" / "{pat}"'
        print(f"  {status}  {label:<38}  positions={result.positions}")
        if not ok:
            print(f"       Expected: {expected}")

print("\n" + "═"*60)
pct = int(passed / total * 100) if total else 0
print(f"  Resultado: {passed}/{total} testes passaram ({pct}%)")
print("═"*60 + "\n")
