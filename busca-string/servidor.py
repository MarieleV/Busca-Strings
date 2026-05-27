"""
servidor.py
===========
Servidor Flask que conecta o frontend (index.html) aos algoritmos de busca.

Endpoints:
  GET  /                  → Serve o index.html
  GET  /api/algoritmos    → Lista algoritmos disponíveis
  POST /api/buscar        → Executa um algoritmo específico
  POST /api/comparar      → Executa todos os algoritmos
  GET  /api/analytics     → Retorna histórico e métricas agregadas

Como usar:
  pip install flask flask-cors opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-flask
  python servidor.py
  Abrir http://127.0.0.1:5000
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from controlador import executar_busca, executar_todos, listar_algoritmos, obter_analytics
from observabilidade import log_erro, log_evento, tracer

# ──────────────────────────────────────────────────────────────
#  APLICAÇÃO
# ──────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder=".")
CORS(app)  # permite que o frontend (mesmo em outra porta) consuma a API


# ──────────────────────────────────────────────────────────────
#  MIDDLEWARE — trace por requisição
# ──────────────────────────────────────────────────────────────

@app.before_request
def _iniciar_trace():
    """Abre um span raiz para cada requisição HTTP."""
    span_name = f"{request.method} {request.path}"
    # Guardamos o span no contexto do request para fechar no after_request
    request._otel_span = tracer.start_span(span_name)
    request._otel_span.__enter__()
    request._otel_span.set_attribute("http.method", request.method)
    request._otel_span.set_attribute("http.url", request.url)


@app.after_request
def _finalizar_trace(response):
    span = getattr(request, "_otel_span", None)
    if span:
        span.set_attribute("http.status_code", response.status_code)
        span.__exit__(None, None, None)
    return response


# ──────────────────────────────────────────────────────────────
#  ROTAS
# ──────────────────────────────────────────────────────────────

@app.route("/")
def pagina_inicial():
    """Serve o arquivo index.html."""
    log_evento("pagina_acessada", "—", 0.0)
    return send_from_directory(".", "index.html")


@app.route("/api/algoritmos")
def rota_algoritmos():
    """Retorna a lista de algoritmos com metadados de complexidade."""
    return jsonify(listar_algoritmos())


@app.route("/api/buscar", methods=["POST"])
def rota_buscar():
    """
    Executa um algoritmo de busca.

    Body JSON:
      { "texto": "...", "padrao": "...", "algoritmo": "kmp" }
    """
    dados = request.get_json(force=True, silent=True) or {}
    texto     = dados.get("texto", "")
    padrao    = dados.get("padrao", "")
    algoritmo = dados.get("algoritmo", "naive")

    if not isinstance(texto, str) or not isinstance(padrao, str):
        return jsonify({"erro": "Campos 'texto' e 'padrao' devem ser strings."}), 400

    resultado = executar_busca(algoritmo, texto, padrao)

    if "erro" in resultado:
        return jsonify(resultado), 400

    return jsonify(resultado)


@app.route("/api/comparar", methods=["POST"])
def rota_comparar():
    """
    Executa todos os algoritmos sobre o mesmo texto/padrão.

    Body JSON:
      { "texto": "...", "padrao": "..." }
    """
    dados  = request.get_json(force=True, silent=True) or {}
    texto  = dados.get("texto", "")
    padrao = dados.get("padrao", "")

    if not isinstance(texto, str) or not isinstance(padrao, str):
        return jsonify({"erro": "Campos 'texto' e 'padrao' devem ser strings."}), 400

    resultados = executar_todos(texto, padrao)
    return jsonify(resultados)


@app.route("/api/analytics")
def rota_analytics():
    """Retorna histórico agregado de execuções para o painel de Analytics."""
    return jsonify(obter_analytics())


# ──────────────────────────────────────────────────────────────
#  TRATAMENTO DE ERROS GLOBAIS
# ──────────────────────────────────────────────────────────────

@app.errorhandler(404)
def nao_encontrado(e):
    log_erro("rota_nao_encontrada", path=request.path)
    return jsonify({"erro": "Rota não encontrada."}), 404


@app.errorhandler(500)
def erro_interno(e):
    log_erro("erro_interno_servidor", detalhe=str(e))
    return jsonify({"erro": "Erro interno do servidor."}), 500


# ──────────────────────────────────────────────────────────────
#  INICIALIZAÇÃO
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "═" * 52)
    print("  String Search Lab v2.0 — servidor iniciado")
    print("  Acesse: http://127.0.0.1:5000")
    print("  Endpoints:")
    print("    GET  /api/algoritmos")
    print("    POST /api/buscar")
    print("    POST /api/comparar")
    print("    GET  /api/analytics")
    print("═" * 52 + "\n")
    app.run(debug=True, port=5000)
