from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time


#  Estrutura de dados

@dataclass
class SearchStep:
    step_number: int
    text_index: int          # posição atual no texto
    pattern_index: int       # posição atual no pattern
    comparison: str          # descrição comparativa legível
    match: bool              # essa comparação foi pertinente?
    highlight_text: List[int] = field(default_factory=list)    # índices destacados no texto
    highlight_pattern: List[int] = field(default_factory=list) # índices destacados no pattern
    extra: Dict[str, Any] = field(default_factory=dict)        # estado específico do algoritmo


@dataclass
class SearchResult:
    """Resultado completo da execução de uma pesquisa."""
    algorithm: str
    text: str
    pattern: str
    positions: List[int]         # todas as posições de partida encontradas
    comparisons: int             # total de comparações realizadas
    steps: List[SearchStep]      # step-by-step
    elapsed_ms: float            # tempo real em milissegundos
    extra_tables: Dict[str, Any] = field(default_factory=dict)  # e.g. LPS, tabela de caracteres inválidos
    complexity_best: str = ""
    complexity_avg: str = ""
    complexity_worst: str = ""


#  pattern Strategy

class SearchStrategy(ABC):
    """
    Por ser abstrata, todo algoritmo concreto deve implementar a função `search`.
    Ela retorna um `SearchResult` contendo posições, métricas e registros de passos.
    """
    name: str = "Abstract"
    complexity_best: str = ""
    complexity_avg: str = ""
    complexity_worst: str = ""

    @abstractmethod
    def search(self, text: str, pattern: str) -> SearchResult:
        ...

    def _make_result(self, text, pattern, positions, comparisons, steps, elapsed_ms, extra_tables=None):
        return SearchResult(
            algorithm=self.name,
            text=text,
            pattern=pattern,
            positions=positions,
            comparisons=comparisons,
            steps=steps,
            elapsed_ms=elapsed_ms,
            extra_tables=extra_tables or {},
            complexity_best=self.complexity_best,
            complexity_avg=self.complexity_avg,
            complexity_worst=self.complexity_worst,
        )


#  1. Naive (Brute Force)

class NaiveSearch(SearchStrategy):
    """
    Naive / Brute-Force Algorithm
    Anda uma posição por vez e compara caractere por caractere.
    """
    name = "Naive"
    complexity_best = "O(n)"
    complexity_avg = "O(n·m)"
    complexity_worst = "O(n·m)"

    def search(self, text: str, pattern: str) -> SearchResult:
        n, m = len(text), len(pattern)
        positions, steps, comparisons = [], [], 0
        step_num = 0

        t0 = time.perf_counter()

        if m == 0 or n == 0:
            elapsed = (time.perf_counter() - t0) * 1000
            return self._make_result(text, pattern, [], 0, [], elapsed)

        for i in range(n - m + 1):
            j = 0
            while j < m:
                comparisons += 1
                match = text[i + j] == pattern[j]
                steps.append(SearchStep(
                    step_number=step_num,
                    text_index=i + j,
                    pattern_index=j,
                    comparison=f"text[{i+j}]='{text[i+j]}' vs pattern[{j}]='{pattern[j]}'",
                    match=match,
                    highlight_text=list(range(i, i + m)),
                    highlight_pattern=list(range(j + 1)),
                    extra={"window_start": i, "window_end": i + m - 1},
                ))
                step_num += 1
                if not match:
                    break
                j += 1

            if j == m:
                positions.append(i)

        elapsed = (time.perf_counter() - t0) * 1000
        return self._make_result(text, pattern, positions, comparisons, steps, elapsed)


#  2. Rabin-Karp

class RabinKarpSearch(SearchStrategy):
    """
    Usa hashing polinomial rolante para detectar posições candidatas em O(1)
    por deslocamento, então verifica com comparação de caracteres para evitar acertos espúrios.
    """
    name = "Rabin-Karp"
    complexity_best = "O(n+m)"
    complexity_avg = "O(n+m)"
    complexity_worst = "O(n·m)"

    BASE = 256
    MOD = 101

    def search(self, text: str, pattern: str) -> SearchResult:
        n, m = len(text), len(pattern)
        positions, steps, comparisons = [], [], 0
        hashes: List[Dict] = []
        step_num = 0

        t0 = time.perf_counter()

        if m == 0 or n == 0 or m > n:
            elapsed = (time.perf_counter() - t0) * 1000
            return self._make_result(text, pattern, [], 0, [], elapsed)

        B, MOD = self.BASE, self.MOD
        h = pow(B, m - 1, MOD)          # B^(m-1) mod MOD

        pat_hash = 0
        txt_hash = 0
        for i in range(m):
            pat_hash = (B * pat_hash + ord(pattern[i])) % MOD
            txt_hash = (B * txt_hash + ord(text[i])) % MOD

        hashes.append({"window": 0, "text_hash": txt_hash, "pattern_hash": pat_hash})

        for i in range(n - m + 1):
            hash_match = txt_hash == pat_hash
            extra = {
                "text_hash": txt_hash,
                "pattern_hash": pat_hash,
                "hash_match": hash_match,
                "window_start": i,
            }
            if hash_match:
                # Verificação de caractere por caractere
                for j in range(m):
                    comparisons += 1
                    match = text[i + j] == pattern[j]
                    steps.append(SearchStep(
                        step_number=step_num,
                        text_index=i + j,
                        pattern_index=j,
                        comparison=f"[Hash match] Verify text[{i+j}]='{text[i+j]}' vs pattern[{j}]='{pattern[j]}'",
                        match=match,
                        highlight_text=list(range(i, i + m)),
                        highlight_pattern=list(range(j + 1)),
                        extra=extra,
                    ))
                    step_num += 1
                    if not match:
                        break
                else:
                    positions.append(i)
            else:
                steps.append(SearchStep(
                    step_number=step_num,
                    text_index=i,
                    pattern_index=0,
                    comparison=f"Hash mismatch at window {i}: txt_hash={txt_hash} ≠ pat_hash={pat_hash}",
                    match=False,
                    highlight_text=list(range(i, i + m)),
                    highlight_pattern=[],
                    extra=extra,
                ))
                step_num += 1

            # Rola o hash
            if i < n - m:
                txt_hash = (B * (txt_hash - ord(text[i]) * h) + ord(text[i + m])) % MOD
                if txt_hash < 0:
                    txt_hash += MOD
                hashes.append({"window": i + 1, "text_hash": txt_hash, "pattern_hash": pat_hash})

        elapsed = (time.perf_counter() - t0) * 1000
        extra_tables = {
            "hashes": hashes,
            "base": B,
            "mod": MOD,
            "pattern_hash": pat_hash,
        }
        return self._make_result(text, pattern, positions, comparisons, steps, elapsed, extra_tables)


#  3. Knuth-Morris-Pratt (KMP)

class KMPSearch(SearchStrategy):
    """
    Pré-processa o pattern para construir a tabela
    LPS(Longest Proper Prefix which is also Suffix.Prefixo Próprio Mais Longo que também é Sufixo),
    permitindo que o algoritmo ignore comparações redundantes.
    """
    name = "KMP"
    complexity_best = "O(n)"
    complexity_avg = "O(n+m)"
    complexity_worst = "O(n+m)"

    def _build_lps(self, pattern: str) -> List[int]:
        m = len(pattern)
        lps = [0] * m
        length = 0
        i = 1
        while i < m:
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            else:
                if length != 0:
                    length = lps[length - 1]
                else:
                    lps[i] = 0
                    i += 1
        return lps

    def search(self, text: str, pattern: str) -> SearchResult:
        n, m = len(text), len(pattern)
        positions, steps, comparisons = [], [], 0
        step_num = 0

        t0 = time.perf_counter()

        if m == 0 or n == 0:
            elapsed = (time.perf_counter() - t0) * 1000
            return self._make_result(text, pattern, [], 0, [], elapsed)

        lps = self._build_lps(pattern)

        i = 0  # índice no texto
        j = 0  # índice em pattern

        while i < n:
            comparisons += 1
            match = text[i] == pattern[j]
            steps.append(SearchStep(
                step_number=step_num,
                text_index=i,
                pattern_index=j,
                comparison=f"text[{i}]='{text[i]}' vs pattern[{j}]='{pattern[j]}' | lps[{j}]={lps[j]}",
                match=match,
                highlight_text=[i],
                highlight_pattern=[j],
                extra={"lps": lps[:], "i": i, "j": j, "lps_jump": lps[j - 1] if (not match and j > 0) else None},
            ))
            step_num += 1

            if match:
                i += 1
                j += 1
            else:
                if j != 0:
                    j = lps[j - 1]
                else:
                    i += 1

            if j == m:
                positions.append(i - j)
                j = lps[j - 1]

        elapsed = (time.perf_counter() - t0) * 1000
        extra_tables = {
            "lps": [{"index": idx, "char": pattern[idx], "lps_value": lps[idx]} for idx in range(m)],
        }
        return self._make_result(text, pattern, positions, comparisons, steps, elapsed, extra_tables)


#  4. Boyer-Moore (Bad Character heuristic)

class BoyerMooreSearch(SearchStrategy):
    """
    Analisa o pattern da direita para a esquerda e usa a heurística de Caractere Ruim para
    fazer grandes saltos, alcançando desempenho sublinear em entradas típicas.
    """
    name = "Boyer-Moore"
    complexity_best = "O(n/m)"
    complexity_avg = "O(n)"
    complexity_worst = "O(n·m)"

    def _bad_char_table(self, pattern: str) -> Dict[str, int]:
        table = {}
        for i, ch in enumerate(pattern):
            table[ch] = i
        return table

    def search(self, text: str, pattern: str) -> SearchResult:
        n, m = len(text), len(pattern)
        positions, steps, comparisons = [], [], 0
        step_num = 0

        t0 = time.perf_counter()

        if m == 0 or n == 0 or m > n:
            elapsed = (time.perf_counter() - t0) * 1000
            return self._make_result(text, pattern, [], 0, [], elapsed)

        bad_char = self._bad_char_table(pattern)
        s = 0  # mudança do pattern ao longo do texto

        while s <= n - m:
            j = m - 1  # começa a combinar da direita

            while j >= 0:
                comparisons += 1
                match = pattern[j] == text[s + j]
                bad_char_val = bad_char.get(text[s + j], -1)
                shift = max(1, j - bad_char_val) if not match else 0

                steps.append(SearchStep(
                    step_number=step_num,
                    text_index=s + j,
                    pattern_index=j,
                    comparison=f"text[{s+j}]='{text[s+j]}' vs pattern[{j}]='{pattern[j]}' (right-to-left)",
                    match=match,
                    highlight_text=list(range(s, s + m)),
                    highlight_pattern=[j],
                    extra={
                        "window_start": s,
                        "bad_char_val": bad_char_val,
                        "shift": shift,
                        "bad_char_char": text[s + j],
                    },
                ))
                step_num += 1

                if not match:
                    break
                j -= 1

            if j < 0:
                positions.append(s)
                s += (m - bad_char.get(text[s + m], -1)) if s + m < n else 1
            else:
                bad_char_val = bad_char.get(text[s + j], -1)
                s += max(1, j - bad_char_val)

        elapsed = (time.perf_counter() - t0) * 1000
        extra_tables = {
            "bad_char": [{"char": ch, "last_index": idx} for ch, idx in sorted(bad_char.items())],
        }
        return self._make_result(text, pattern, positions, comparisons, steps, elapsed, extra_tables)
