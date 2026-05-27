"""
observabilidade.py
==================
Configura e expõe o stack de observabilidade baseado em OpenTelemetry.

O que é instrumentado:
  Traces  → rastreia cada requisição HTTP e cada chamada de algoritmo
  Métricas → contagens, histogramas de tempo e comparações por algoritmo
  Logs    → emite eventos estruturados correlacionados com o trace_id atual

Uso:
  from observabilidade import tracer, meter, log_evento, registrar_metricas

  with tracer.start_as_current_span("minha-operacao") as span:
      span.set_attribute("chave", "valor")
      resultado = faz_algo()
      registrar_metricas(resultado)
      log_evento("busca_concluida", resultado.algoritmo, resultado.tempo_ms)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# ──────────────────────────────────────────────────────────────
#  RESOURCE — identifica este serviço nos sistemas de observabilidade
# ──────────────────────────────────────────────────────────────

RESOURCE = Resource.create({
    "service.name":    "string-busca-lab",
    "service.version": "2.0.0",
    "deployment.environment": "development",
})

# ──────────────────────────────────────────────────────────────
#  TRACES
# ──────────────────────────────────────────────────────────────

_tracer_provider = TracerProvider(resource=RESOURCE)
_tracer_provider.add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)
trace.set_tracer_provider(_tracer_provider)

tracer = trace.get_tracer("string-busca-lab", "2.0.0")

# ──────────────────────────────────────────────────────────────
#  MÉTRICAS
# ──────────────────────────────────────────────────────────────

_metric_reader = PeriodicExportingMetricReader(
    ConsoleMetricExporter(),
    export_interval_millis=30_000,   # exporta a cada 30 s
)
_meter_provider = MeterProvider(resource=RESOURCE, metric_readers=[_metric_reader])
metrics.set_meter_provider(_meter_provider)

meter = metrics.get_meter("string-busca-lab", "2.0.0")

# Instrumentos de métricas
_contador_buscas = meter.create_counter(
    name="busca.execucoes.total",
    description="Número total de buscas executadas",
    unit="1",
)

_histograma_tempo = meter.create_histogram(
    name="busca.tempo_execucao",
    description="Tempo de execução em milissegundos por algoritmo",
    unit="ms",
)

_histograma_comparacoes = meter.create_histogram(
    name="busca.comparacoes",
    description="Número de comparações realizadas por algoritmo",
    unit="1",
)

_histograma_texto = meter.create_histogram(
    name="busca.tamanho_texto",
    description="Tamanho do texto de entrada",
    unit="chars",
)

_histograma_ocorrencias = meter.create_histogram(
    name="busca.ocorrencias",
    description="Número de ocorrências encontradas",
    unit="1",
)

# ──────────────────────────────────────────────────────────────
#  LOGS ESTRUTURADOS
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    format=(
        "%(asctime)s  %(levelname)-8s  "
        "[%(trace_id)s] "
        "%(name)s — %(message)s"
    ),
    level=logging.INFO,
)

_logger = logging.getLogger("string-busca-lab")


def _trace_id_hex() -> str:
    """Retorna o trace_id atual em hexadecimal (ou '0000' se não houver span ativo)."""
    ctx = trace.get_current_span().get_span_context()
    if ctx and ctx.is_valid:
        return format(ctx.trace_id, "032x")[:8]
    return "00000000"


class _TraceFilter(logging.Filter):
    """Injeta trace_id nos LogRecord para correlacionar log com trace."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = _trace_id_hex()
        return True


_logger.addFilter(_TraceFilter())


# ──────────────────────────────────────────────────────────────
#  API PÚBLICA
# ──────────────────────────────────────────────────────────────

def registrar_metricas(resultado: Any, algoritmo_key: str = "") -> None:
    """
    Registra todas as métricas relevantes de um ResultadoBusca.

    Parâmetros
    ----------
    resultado    : ResultadoBusca retornado por um algoritmo
    algoritmo_key: chave canônica do algoritmo (ex: 'kmp', 'naive')
    """
    labels: Dict[str, str] = {
        "algoritmo": resultado.algoritmo,
        "algoritmo_key": algoritmo_key or resultado.algoritmo.lower(),
    }

    _contador_buscas.add(1, labels)
    _histograma_tempo.record(resultado.tempo_ms, labels)
    _histograma_comparacoes.record(resultado.comparacoes, labels)
    _histograma_texto.record(len(resultado.texto), labels)
    _histograma_ocorrencias.record(len(resultado.posicoes), labels)


def log_evento(evento: str, algoritmo: str, tempo_ms: float, **extras: Any) -> None:
    """Emite um log estruturado correlacionado ao trace ativo."""
    campos = {"evento": evento, "algoritmo": algoritmo, "tempo_ms": round(tempo_ms, 4)}
    campos.update(extras)
    _logger.info("%s | %s", evento, campos)


def log_erro(msg: str, **extras: Any) -> None:
    """Emite um log de erro correlacionado ao trace ativo."""
    _logger.error("%s | %s", msg, extras)
