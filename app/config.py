"""Configurações lidas de variáveis de ambiente (.env)."""
import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
MAX_TENTATIVAS_IA = 2


def limiar_confianca() -> float:
    """Lido a cada chamada para facilitar testes e ajustes sem reiniciar."""
    try:
        return float(os.getenv("LIMIAR_CONFIANCA", "0.6"))
    except ValueError:
        return 0.6
