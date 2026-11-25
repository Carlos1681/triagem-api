"""Envia mensagens de exemplo ao webhook do Make para testar o fluxo completo.

Uso:
    python scripts/enviar_exemplos.py                 # envia todas as mensagens
    python scripts/enviar_exemplos.py --indice 1      # envia só a 2ª mensagem (começa em 0)
    python scripts/enviar_exemplos.py --dry-run       # só mostra o que seria enviado

A URL do webhook vem da variável MAKE_WEBHOOK_URL (arquivo .env).
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")


def mascarar(url: str) -> str:
    """Mostra só o começo da URL para não vazar o ID do webhook em prints/logs."""
    return url[:30] + "..." if len(url) > 30 else url


def enviar(url: str, payload: dict) -> tuple[int, str]:
    requisicao = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(requisicao, timeout=30) as resposta:
        return resposta.status, resposta.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispara mensagens de exemplo no webhook do Make.")
    parser.add_argument("--arquivo", default=str(RAIZ / "exemplos" / "mensagens.json"))
    parser.add_argument("--indice", type=int, default=None, help="envia apenas a mensagem deste índice")
    parser.add_argument("--intervalo", type=float, default=2.0, help="segundos entre envios")
    parser.add_argument("--dry-run", action="store_true", help="não envia, só mostra")
    args = parser.parse_args()

    url = os.getenv("MAKE_WEBHOOK_URL", "").strip()
    if not url or "COLE_AQUI" in url:
        print("Defina MAKE_WEBHOOK_URL no arquivo .env.", file=sys.stderr)
        return 1

    mensagens = json.loads(Path(args.arquivo).read_text(encoding="utf-8"))
    if args.indice is not None:
        if not 0 <= args.indice < len(mensagens):
            print(f"Índice inválido. Use de 0 a {len(mensagens) - 1}.", file=sys.stderr)
            return 1
        mensagens = [mensagens[args.indice]]

    print(f"Webhook: {mascarar(url)} | {len(mensagens)} mensagem(ns)\n")
    falhas = 0
    for i, payload in enumerate(mensagens, start=1):
        trecho = payload["mensagem"][:60]
        if args.dry_run:
            print(f"[dry-run] {i}: {trecho}")
            continue
        try:
            status, corpo = enviar(url, payload)
            print(f"[{status}] {i}: {trecho} -> {corpo[:80]}")
        except urllib.error.HTTPError as erro:
            falhas += 1
            print(f"[ERRO {erro.code}] {i}: {trecho}", file=sys.stderr)
        except urllib.error.URLError as erro:
            falhas += 1
            print(f"[ERRO] {i}: {erro.reason}", file=sys.stderr)
        if i < len(mensagens):
            time.sleep(args.intervalo)

    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
