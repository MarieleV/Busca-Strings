"""
controlador.py
==============
Camada de negócio entre o servidor Flask e os algoritmos de busca.

Responsabilidades:
  - Registrar os algoritmos disponíveis (Strategy registry)
  - Executar buscas e serializar os resultados para JSON
  - Instrumentar cada operação com traces, métricas e logs (OpenTelemetry)
  - Armazenar histórico em memória para a aba de Analytics do frontend
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Dict, List

from algoritmos import (
    BuscaBoyerMoore,
    BuscaKMP,
    BuscaNaive,
    BuscaRabinKarp,
    EstrategiaDeBusca,
    ResultadoBusca,
)
from observabilidade import log_erro, log_evento, registrar_metricas, tracer
from opentelemetry import trace


# ──────────────────────────────────────────────────────────────
#  REGISTRY — adicionar um algoritmo aqui é suficiente para que
#             apareça automaticamente na interface e nas métricas
# ──────────────────────────────────────────────────────────────

ALGORITMOS: Dict[str, EstrategiaDeBusca] = {
    "naive":       BuscaNaive(),
    "rabin-karp":  BuscaRabinKarp(),
    "kmp":         BuscaKMP(),
    "boyer-moore": BuscaBoyerMoore(),
}

# ──────────────────────────────────────────────────────────────
#  HISTÓRICO EM MEMÓRIA  (para Analytics)
# ──────────────────────────────────────────────────────────────

# Estrutura: { algoritmo_key: [{"tempo_ms": float, "comparacoes": int, ...}, ...] }
_historico: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
_MAX_HISTORICO = 200  # mantém os últimos N registros por algoritmo


def _registrar_historico(chave: str, resultado: ResultadoBusca) -> None:
    entrada = {
        "timestamp": time.time(),
        "tempo_ms": round(resultado.tempo_ms, 4),
        "comparacoes": resultado.comparacoes,
        "ocorrencias": len(resultado.posicoes),
        "tamanho_texto": len(resultado.texto),
        "tamanho_padrao": len(resultado.padrao),
    }
    hist = _historico[chave]
    hist.append(entrada)
    if len(hist) > _MAX_HISTORICO:
        hist.pop(0)


# ──────────────────────────────────────────────────────────────
#  FUNÇÕES PÚBLICAS
# ──────────────────────────────────────────────────────────────

def executar_busca(algoritmo: str, texto: str, padrao: str) -> Dict[str, Any]:
    """
    Executa um único algoritmo e devolve o resultado serializado.
    Chamado pelo endpoint  POST /api/buscar.
    """
    with tracer.start_as_current_span("executar_busca") as span:
        span.set_attribute("algoritmo", algoritmo)
        span.set_attribute("tamanho_texto", len(texto))
        span.set_attribute("tamanho_padrao", len(padrao))

        estrategia = ALGORITMOS.get(algoritmo)
        if estrategia is None:
            erro = f"Algoritmo desconhecido: '{algoritmo}'"
            log_erro(erro, algoritmo=algoritmo)
            span.set_status(trace.StatusCode.ERROR, erro)
            return {"erro": erro}

        try:
            with tracer.start_as_current_span(f"algoritmo.{algoritmo}"):
                resultado = estrategia.buscar(texto, padrao)

            span.set_attribute("ocorrencias", len(resultado.posicoes))
            span.set_attribute("comparacoes", resultado.comparacoes)
            span.set_attribute("tempo_ms", resultado.tempo_ms)

            registrar_metricas(resultado, algoritmo)
            _registrar_historico(algoritmo, resultado)
            log_evento(
                "busca_concluida",
                algoritmo,
                resultado.tempo_ms,
                ocorrencias=len(resultado.posicoes),
                comparacoes=resultado.comparacoes,
            )

            return _para_dict(resultado)

        except Exception as exc:  # noqa: BLE001
            log_erro(str(exc), algoritmo=algoritmo)
            span.record_exception(exc)
            span.set_status(trace.StatusCode.ERROR, str(exc))
            return {"erro": f"Erro interno ao executar '{algoritmo}': {exc}"}


def executar_todos(texto: str, padrao: str) -> List[Dict[str, Any]]:
    """
    Executa todos os algoritmos sobre o mesmo texto/padrão.
    Chamado pelo endpoint  POST /api/comparar.
    """
    with tracer.start_as_current_span("executar_todos") as span:
        span.set_attribute("tamanho_texto", len(texto))
        span.set_attribute("tamanho_padrao", len(padrao))
        span.set_attribute("total_algoritmos", len(ALGORITMOS))

        resultados = []
        for chave, estrategia in ALGORITMOS.items():
            with tracer.start_as_current_span(f"algoritmo.{chave}"):
                resultado = estrategia.buscar(texto, padrao)
            registrar_metricas(resultado, chave)
            _registrar_historico(chave, resultado)
            log_evento(
                "comparacao_algoritmo",
                chave,
                resultado.tempo_ms,
                ocorrencias=len(resultado.posicoes),
            )
            resultados.append(_para_dict(resultado))

        return resultados


def listar_algoritmos() -> List[Dict[str, str]]:
    """
    Devolve os metadados de todos os algoritmos disponíveis.
    Chamado pelo endpoint  GET /api/algoritmos.
    """
    return [
        {
            "id":     chave,
            "nome":   estrategia.nome,
            "melhor": estrategia.complexidade_melhor,
            "medio":  estrategia.complexidade_media,
            "pior":   estrategia.complexidade_pior,
        }
        for chave, estrategia in ALGORITMOS.items()
    ]


def obter_analytics() -> Dict[str, Any]:
    """
    Devolve dados agregados do histórico de execuções para a
    aba de Analytics do frontend.
    Chamado pelo endpoint  GET /api/analytics.
    """
    with tracer.start_as_current_span("obter_analytics"):
        resumo: Dict[str, Any] = {}

        for chave, entradas in _historico.items():
            if not entradas:
                continue

            tempos = [e["tempo_ms"] for e in entradas]
            comparacoes = [e["comparacoes"] for e in entradas]
            ocorrencias = [e["ocorrencias"] for e in entradas]

            resumo[chave] = {
                "nome": ALGORITMOS[chave].nome if chave in ALGORITMOS else chave,
                "total_execucoes": len(entradas),
                "tempo": {
                    "min":   round(min(tempos), 4),
                    "max":   round(max(tempos), 4),
                    "media": round(sum(tempos) / len(tempos), 4),
                    "total": round(sum(tempos), 4),
                },
                "comparacoes": {
                    "min":   min(comparacoes),
                    "max":   max(comparacoes),
                    "media": round(sum(comparacoes) / len(comparacoes), 1),
                },
                "ocorrencias_total": sum(ocorrencias),
                # últimas 50 execuções para sparklines
                "historico_recente": entradas[-50:],
            }

        return resumo


# ──────────────────────────────────────────────────────────────
#  SERIALIZAÇÃO
# ──────────────────────────────────────────────────────────────

def _para_dict(resultado: ResultadoBusca) -> Dict[str, Any]:
    """Converte ResultadoBusca em dicionário JSON-serializável."""
    return {
        "algoritmo":      resultado.algoritmo,
        "posicoes":       resultado.posicoes,
        "comparacoes":    resultado.comparacoes,
        "tempo_ms":       round(resultado.tempo_ms, 4),
        "tamanho_texto":  len(resultado.texto),
        "tamanho_padrao": len(resultado.padrao),
        "complexidade": {
            "melhor": resultado.complexidade_melhor,
            "medio":  resultado.complexidade_media,
            "pior":   resultado.complexidade_pior,
        },
        "tabelas_extras": resultado.tabelas_extras,
        "passos": [
            {
                "numero":          p.numero_passo,
                "posicao_texto":   p.posicao_texto,
                "posicao_padrao":  p.posicao_padrao,
                "descricao":       p.descricao,
                "houve_match":     p.houve_match,
                "destaque_texto":  p.destaque_texto,
                "destaque_padrao": p.destaque_padrao,
                "dados_extras":    p.dados_extras,
            }
            for p in resultado.passos
        ],
    }
