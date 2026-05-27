"""
testes.py
=========
Suite de testes automatizados para todos os algoritmos de busca.

Como rodar:
  python testes.py

Cada algoritmo é testado com os mesmos casos, garantindo que todos
retornam exatamente as mesmas posições (padrão Strategy em ação).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from algoritmos import BuscaBoyerMoore, BuscaIngenua, BuscaKMP, BuscaNaive, BuscaRabinKarp

# ──────────────────────────────────────────────────────────────
#  ALGORITMOS A TESTAR
# ──────────────────────────────────────────────────────────────

ALGORITMOS = [
    BuscaNaive(),
    BuscaIngenua(),   # alias de BuscaNaive — deve ter o mesmo comportamento
    BuscaRabinKarp(),
    BuscaKMP(),
    BuscaBoyerMoore(),
]

# ──────────────────────────────────────────────────────────────
#  CASOS DE TESTE: (texto, padrão, posições_esperadas)
# ──────────────────────────────────────────────────────────────

CASOS_DE_TESTE = [
    # casos básicos
    ("AABAACAADAABAABA", "AABA",   [0, 9, 12]),
    ("abcabcabc",        "abc",    [0, 3, 6]),
    ("hello mundo",      "mundo",  [6]),

    # padrão no fim
    ("abcdef",           "ef",     [4]),

    # muitas ocorrências sobrepostas
    ("aaaaaaa",          "aaa",    [0, 1, 2, 3, 4]),

    # sem ocorrência
    ("abcdef",           "xyz",    []),

    # entradas vazias
    ("",                 "abc",    []),
    ("abc",              "",       []),

    # padrão igual ao texto
    ("abc",              "abc",    [0]),

    # clássico de algoritmos
    ("GEEKS FOR GEEKS",  "GEEKS",  [0, 10]),

    # sobreposição parcial
    ("aabaabaab",        "aab",    [0, 3, 6]),

    # padrão quase certo mas falha no fim
    ("abcabdabc",        "abc",    [0, 6]),
]


# ──────────────────────────────────────────────────────────────
#  RUNNER
# ──────────────────────────────────────────────────────────────

def executar_testes() -> None:
    total = passou = 0

    print("\n" + "═" * 68)
    print("  String Search Lab v2.0 — Suite de Testes")
    print("═" * 68)

    for algoritmo in ALGORITMOS:
        print(f"\n── {algoritmo.nome} " + "─" * (52 - len(algoritmo.nome)))

        for texto, padrao, esperado in CASOS_DE_TESTE:
            resultado   = algoritmo.buscar(texto, padrao)
            encontrado  = sorted(resultado.posicoes)
            correto     = encontrado == sorted(esperado)

            total  += 1
            if correto:
                passou += 1

            simbolo      = "✅" if correto else "❌"
            texto_curto  = f'"{texto[:22]}{"…" if len(texto) > 22 else ""}"'
            padrao_curto = f'"{padrao}"'
            label        = f"{texto_curto} / {padrao_curto}"

            print(f"  {simbolo}  {label:<42}  pos={encontrado}")

            if not correto:
                print(f"       Esperado: {esperado}")

    percentual = int(passou / total * 100) if total else 0
    print("\n" + "═" * 68)
    if passou == total:
        print(f"  ✅ Todos os testes passaram! {passou}/{total} (100%)")
    else:
        print(f"  ⚠️  {passou}/{total} testes passaram ({percentual}%)")
    print("═" * 68 + "\n")


if __name__ == "__main__":
    executar_testes()
