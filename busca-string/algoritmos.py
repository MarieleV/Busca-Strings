"""
algoritmos.py
=============
Implementações dos algoritmos de busca em strings.

Padrão de projeto: Strategy
    - EstrategiaDeBusca  → interface abstrata
    - BuscaNaive         → força bruta  O(n·m)
    - BuscaRabinKarp     → hashing       O(n+m) médio
    - BuscaKMP           → tabela LPS    O(n+m)
    - BuscaBoyerMoore    → mau caractere O(n/m) melhor caso

Cada algoritmo devolve um ResultadoBusca padronizado, contendo
posições, contagem de comparações, tempo de execução e rastreamento
passo a passo — usado pelo frontend para visualização didática.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


# ──────────────────────────────────────────────────────────────
#  ESTRUTURAS DE DADOS
# ──────────────────────────────────────────────────────────────

@dataclass
class PassoExecucao:
    """Representa um único passo de comparação do algoritmo."""

    numero_passo: int
    posicao_texto: int
    posicao_padrao: int
    descricao: str
    houve_match: bool
    destaque_texto: List[int] = field(default_factory=list)
    destaque_padrao: List[int] = field(default_factory=list)
    dados_extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResultadoBusca:
    """Resultado completo de uma execução de busca."""

    algoritmo: str
    texto: str
    padrao: str
    posicoes: List[int]
    comparacoes: int
    passos: List[PassoExecucao]
    tempo_ms: float
    tabelas_extras: Dict[str, Any] = field(default_factory=dict)
    complexidade_melhor: str = ""
    complexidade_media: str = ""
    complexidade_pior: str = ""


# ──────────────────────────────────────────────────────────────
#  INTERFACE (STRATEGY)
# ──────────────────────────────────────────────────────────────

class EstrategiaDeBusca(ABC):
    """Contrato que todo algoritmo de busca deve implementar."""

    nome: str = "Abstrato"
    complexidade_melhor: str = ""
    complexidade_media: str = ""
    complexidade_pior: str = ""

    @abstractmethod
    def buscar(self, texto: str, padrao: str) -> ResultadoBusca:
        """Executa a busca e retorna o resultado completo."""
        ...

    # ── helper compartilhado ──────────────────────────────────

    def _montar_resultado(
        self,
        texto: str,
        padrao: str,
        posicoes: List[int],
        comparacoes: int,
        passos: List[PassoExecucao],
        tempo_ms: float,
        tabelas_extras: Dict[str, Any] | None = None,
    ) -> ResultadoBusca:
        return ResultadoBusca(
            algoritmo=self.nome,
            texto=texto,
            padrao=padrao,
            posicoes=posicoes,
            comparacoes=comparacoes,
            passos=passos,
            tempo_ms=tempo_ms,
            tabelas_extras=tabelas_extras or {},
            complexidade_melhor=self.complexidade_melhor,
            complexidade_media=self.complexidade_media,
            complexidade_pior=self.complexidade_pior,
        )


# ──────────────────────────────────────────────────────────────
#  ALGORITMO 1 — NAIVE (FORÇA BRUTA)
# ──────────────────────────────────────────────────────────────

class BuscaNaive(EstrategiaDeBusca):
    """
    Busca ingênua: desliza o padrão sobre o texto comparando
    caractere a caractere sem nenhuma pré-computação.

    Complexidade:
        Melhor  O(n)    — primeiro char nunca casa
        Médio   O(n·m)
        Pior    O(n·m)  — padrão quase casando o tempo todo (ex: AAAA/AAB)
    """

    nome = "Naive"
    complexidade_melhor = "O(n)"
    complexidade_media = "O(n·m)"
    complexidade_pior = "O(n·m)"

    def buscar(self, texto: str, padrao: str) -> ResultadoBusca:
        n, m = len(texto), len(padrao)
        posicoes: List[int] = []
        passos: List[PassoExecucao] = []
        comparacoes = 0
        numero_passo = 0

        inicio = time.perf_counter()

        if m == 0 or n == 0:
            return self._montar_resultado(
                texto, padrao, [], 0, [], (time.perf_counter() - inicio) * 1000
            )

        for inicio_janela in range(n - m + 1):
            j = 0
            while j < m:
                comparacoes += 1
                char_texto = texto[inicio_janela + j]
                char_padrao = padrao[j]
                houve_match = char_texto == char_padrao

                passos.append(PassoExecucao(
                    numero_passo=numero_passo,
                    posicao_texto=inicio_janela + j,
                    posicao_padrao=j,
                    descricao=(
                        f"texto[{inicio_janela + j}]='{char_texto}' "
                        f"vs padrão[{j}]='{char_padrao}'"
                    ),
                    houve_match=houve_match,
                    destaque_texto=list(range(inicio_janela, inicio_janela + m)),
                    destaque_padrao=list(range(j + 1)),
                    dados_extras={"inicio_janela": inicio_janela},
                ))
                numero_passo += 1

                if not houve_match:
                    break
                j += 1

            if j == m:
                posicoes.append(inicio_janela)

        tempo_ms = (time.perf_counter() - inicio) * 1000
        return self._montar_resultado(
            texto, padrao, posicoes, comparacoes, passos, tempo_ms
        )


# Alias mantido para compatibilidade com testes.py legado
BuscaIngenua = BuscaNaive


# ──────────────────────────────────────────────────────────────
#  ALGORITMO 2 — RABIN-KARP
# ──────────────────────────────────────────────────────────────

class BuscaRabinKarp(EstrategiaDeBusca):
    """
    Rabin-Karp: compara hashes de janelas antes de verificar
    caractere a caractere. O rolling-hash atualiza em O(1).

    Complexidade:
        Melhor  O(n+m)
        Médio   O(n+m)
        Pior    O(n·m)  — muitas colisões de hash
    """

    nome = "Rabin-Karp"
    complexidade_melhor = "O(n+m)"
    complexidade_media = "O(n+m)"
    complexidade_pior = "O(n·m)"

    BASE = 256
    MOD = 101

    def buscar(self, texto: str, padrao: str) -> ResultadoBusca:
        n, m = len(texto), len(padrao)
        posicoes: List[int] = []
        passos: List[PassoExecucao] = []
        comparacoes = 0
        numero_passo = 0
        registro_hashes: List[Dict[str, Any]] = []

        inicio = time.perf_counter()

        if m == 0 or n == 0 or m > n:
            return self._montar_resultado(
                texto, padrao, [], 0, [], (time.perf_counter() - inicio) * 1000
            )

        B, MOD = self.BASE, self.MOD
        h = pow(B, m - 1, MOD)

        hash_padrao = hash_janela = 0
        for i in range(m):
            hash_padrao = (B * hash_padrao + ord(padrao[i])) % MOD
            hash_janela = (B * hash_janela + ord(texto[i])) % MOD

        registro_hashes.append(
            {"janela": 0, "hash_texto": hash_janela, "hash_padrao": hash_padrao}
        )

        for i in range(n - m + 1):
            hashes_iguais = hash_janela == hash_padrao
            info_extra = {
                "hash_texto": hash_janela,
                "hash_padrao": hash_padrao,
                "hashes_iguais": hashes_iguais,
                "inicio_janela": i,
            }

            if hashes_iguais:
                for j in range(m):
                    comparacoes += 1
                    char_texto = texto[i + j]
                    char_padrao = padrao[j]
                    houve_match = char_texto == char_padrao

                    passos.append(PassoExecucao(
                        numero_passo=numero_passo,
                        posicao_texto=i + j,
                        posicao_padrao=j,
                        descricao=(
                            f"[Hash igual!] Confirmando: "
                            f"texto[{i+j}]='{char_texto}' vs padrão[{j}]='{char_padrao}'"
                        ),
                        houve_match=houve_match,
                        destaque_texto=list(range(i, i + m)),
                        destaque_padrao=list(range(j + 1)),
                        dados_extras=info_extra,
                    ))
                    numero_passo += 1

                    if not houve_match:
                        break
                else:
                    posicoes.append(i)
            else:
                passos.append(PassoExecucao(
                    numero_passo=numero_passo,
                    posicao_texto=i,
                    posicao_padrao=0,
                    descricao=(
                        f"Hash diferente na janela {i}: "
                        f"texto={hash_janela} ≠ padrão={hash_padrao} → pula"
                    ),
                    houve_match=False,
                    destaque_texto=list(range(i, i + m)),
                    destaque_padrao=[],
                    dados_extras=info_extra,
                ))
                numero_passo += 1

            if i < n - m:
                hash_janela = (
                    B * (hash_janela - ord(texto[i]) * h) + ord(texto[i + m])
                ) % MOD
                if hash_janela < 0:
                    hash_janela += MOD
                registro_hashes.append(
                    {"janela": i + 1, "hash_texto": hash_janela, "hash_padrao": hash_padrao}
                )

        tempo_ms = (time.perf_counter() - inicio) * 1000
        tabelas = {
            "hashes": registro_hashes,
            "base": B,
            "mod": MOD,
            "hash_padrao": hash_padrao,
        }
        return self._montar_resultado(
            texto, padrao, posicoes, comparacoes, passos, tempo_ms, tabelas
        )


# ──────────────────────────────────────────────────────────────
#  ALGORITMO 3 — KNUTH-MORRIS-PRATT (KMP)
# ──────────────────────────────────────────────────────────────

class BuscaKMP(EstrategiaDeBusca):
    """
    KMP: pré-computa a tabela LPS para que o cursor do texto
    nunca retroceda — cada caractere é visitado exatamente uma vez.

    Complexidade:
        Melhor  O(n)
        Médio   O(n+m)
        Pior    O(n+m)
    """

    nome = "KMP"
    complexidade_melhor = "O(n)"
    complexidade_media = "O(n+m)"
    complexidade_pior = "O(n+m)"

    def _construir_tabela_lps(self, padrao: str) -> List[int]:
        """Longest Proper Prefix-Suffix em O(m)."""
        m = len(padrao)
        lps = [0] * m
        comprimento = 0
        i = 1

        while i < m:
            if padrao[i] == padrao[comprimento]:
                comprimento += 1
                lps[i] = comprimento
                i += 1
            else:
                if comprimento:
                    comprimento = lps[comprimento - 1]
                else:
                    lps[i] = 0
                    i += 1

        return lps

    def buscar(self, texto: str, padrao: str) -> ResultadoBusca:
        n, m = len(texto), len(padrao)
        posicoes: List[int] = []
        passos: List[PassoExecucao] = []
        comparacoes = 0
        numero_passo = 0

        inicio = time.perf_counter()

        if m == 0 or n == 0:
            return self._montar_resultado(
                texto, padrao, [], 0, [], (time.perf_counter() - inicio) * 1000
            )

        lps = self._construir_tabela_lps(padrao)
        i = j = 0

        while i < n:
            comparacoes += 1
            char_texto = texto[i]
            char_padrao = padrao[j]
            houve_match = char_texto == char_padrao
            salto_lps = lps[j - 1] if (not houve_match and j > 0) else None

            passos.append(PassoExecucao(
                numero_passo=numero_passo,
                posicao_texto=i,
                posicao_padrao=j,
                descricao=(
                    f"texto[{i}]='{char_texto}' vs padrão[{j}]='{char_padrao}'"
                    f" | LPS[{j}]={lps[j]}"
                ),
                houve_match=houve_match,
                destaque_texto=[i],
                destaque_padrao=[j],
                dados_extras={"lps": lps[:], "i": i, "j": j, "salto_lps": salto_lps},
            ))
            numero_passo += 1

            if houve_match:
                i += 1
                j += 1
            else:
                j = lps[j - 1] if j != 0 else 0
                if j == 0 and not houve_match:
                    i += 1

            if j == m:
                posicoes.append(i - j)
                j = lps[j - 1]

        tempo_ms = (time.perf_counter() - inicio) * 1000
        tabelas = {
            "lps": [
                {"indice": idx, "char": padrao[idx], "valor_lps": lps[idx]}
                for idx in range(m)
            ]
        }
        return self._montar_resultado(
            texto, padrao, posicoes, comparacoes, passos, tempo_ms, tabelas
        )


# ──────────────────────────────────────────────────────────────
#  ALGORITMO 4 — BOYER-MOORE
# ──────────────────────────────────────────────────────────────

class BuscaBoyerMoore(EstrategiaDeBusca):
    """
    Boyer-Moore: compara da direita para a esquerda e usa a
    heurística do mau caractere para pular grandes trechos.

    Complexidade:
        Melhor  O(n/m)  — pula o padrão inteiro a cada janela
        Médio   O(n)
        Pior    O(n·m)  — padrão com chars repetidos e texto uniforme
    """

    nome = "Boyer-Moore"
    complexidade_melhor = "O(n/m)"
    complexidade_media = "O(n)"
    complexidade_pior = "O(n·m)"

    def _construir_tabela_mau_caractere(self, padrao: str) -> Dict[str, int]:
        """Mapeia cada char ao seu último índice no padrão."""
        return {char: i for i, char in enumerate(padrao)}

    def buscar(self, texto: str, padrao: str) -> ResultadoBusca:
        n, m = len(texto), len(padrao)
        posicoes: List[int] = []
        passos: List[PassoExecucao] = []
        comparacoes = 0
        numero_passo = 0

        inicio = time.perf_counter()

        if m == 0 or n == 0 or m > n:
            return self._montar_resultado(
                texto, padrao, [], 0, [], (time.perf_counter() - inicio) * 1000
            )

        tabela_mc = self._construir_tabela_mau_caractere(padrao)
        deslocamento = 0

        while deslocamento <= n - m:
            j = m - 1

            while j >= 0:
                comparacoes += 1
                char_texto = texto[deslocamento + j]
                char_padrao = padrao[j]
                houve_match = char_padrao == char_texto
                indice_mc = tabela_mc.get(char_texto, -1)
                salto = max(1, j - indice_mc) if not houve_match else 0

                passos.append(PassoExecucao(
                    numero_passo=numero_passo,
                    posicao_texto=deslocamento + j,
                    posicao_padrao=j,
                    descricao=(
                        f"texto[{deslocamento+j}]='{char_texto}' "
                        f"vs padrão[{j}]='{char_padrao}' (direita→esquerda)"
                    ),
                    houve_match=houve_match,
                    destaque_texto=list(range(deslocamento, deslocamento + m)),
                    destaque_padrao=[j],
                    dados_extras={
                        "deslocamento": deslocamento,
                        "indice_mc": indice_mc,
                        "salto": salto,
                        "mau_caractere": char_texto,
                    },
                ))
                numero_passo += 1

                if not houve_match:
                    break
                j -= 1

            if j < 0:
                posicoes.append(deslocamento)
                prox = (
                    tabela_mc.get(texto[deslocamento + m], -1)
                    if deslocamento + m < n
                    else -1
                )
                deslocamento += m - prox
            else:
                deslocamento += max(1, j - tabela_mc.get(texto[deslocamento + j], -1))

        tempo_ms = (time.perf_counter() - inicio) * 1000
        tabelas = {
            "mau_caractere": [
                {"char": char, "ultimo_indice": idx}
                for char, idx in sorted(tabela_mc.items())
            ]
        }
        return self._montar_resultado(
            texto, padrao, posicoes, comparacoes, passos, tempo_ms, tabelas
        )
