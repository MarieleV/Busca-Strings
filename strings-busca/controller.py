import json
from typing import List, Optional, Dict, Any
from algoritmos import (
    SearchStrategy, SearchResult,
    NaiveSearch, RabinKarpSearch, KMPSearch, BoyerMooreSearch,
)

# Registro de todas as estratégias disponíveis
STRATEGIES: Dict[str, SearchStrategy] = {
    "naive":       NaiveSearch(),
    "rabin-karp":  RabinKarpSearch(),
    "kmp":         KMPSearch(),
    "boyer-moore": BoyerMooreSearch(),
}


def run_search(algorithm: str, text: str, pattern: str) -> Dict[str, Any]:
    """
    Execute o algoritmo selecionado e retorne um dicionário de resultados serializável em JSON.
    """
    strategy = STRATEGIES.get(algorithm)
    if strategy is None:
        return {"error": f"Unknown algorithm: {algorithm}"}

    result = strategy.search(text, pattern)
    return _serialise(result)


def run_all(text: str, pattern: str) -> List[Dict[str, Any]]:
    """
    Executa todos os algoritmos disponíveis na mesma entrada para comparação.
    Retorna uma lista de resultados serializados.
    """
    return [_serialise(s.search(text, pattern)) for s in STRATEGIES.values()]


def _serialise(r: SearchResult) -> Dict[str, Any]:
    return {
        "algorithm": r.algorithm,
        "positions": r.positions,
        "comparisons": r.comparisons,
        "elapsed_ms": round(r.elapsed_ms, 4),
        "text_length": len(r.text),
        "pattern_length": len(r.pattern),
        "complexity": {
            "best":  r.complexity_best,
            "avg":   r.complexity_avg,
            "worst": r.complexity_worst,
        },
        "extra_tables": r.extra_tables,
        "steps": [
            {
                "step_number":        s.step_number,
                "text_index":         s.text_index,
                "pattern_index":      s.pattern_index,
                "comparison":         s.comparison,
                "match":              s.match,
                "highlight_text":     s.highlight_text,
                "highlight_pattern":  s.highlight_pattern,
                "extra":              s.extra,
            }
            for s in r.steps
        ],
    }


def get_algorithm_info() -> List[Dict[str, str]]:
    return [
        {
            "id": key,
            "name": s.name,
            "best": s.complexity_best,
            "avg":  s.complexity_avg,
            "worst": s.complexity_worst,
        }
        for key, s in STRATEGIES.items()
    ]
