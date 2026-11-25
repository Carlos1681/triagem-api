"""Integração com a IA (Anthropic) e validação da resposta."""
import json
import logging
import os
import re
from functools import lru_cache

from anthropic import Anthropic, APIError
from pydantic import ValidationError

from app.config import ANTHROPIC_MODEL, MAX_TENTATIVAS_IA
from app.prompts import SYSTEM_PROMPT, montar_mensagem_usuario
from app.schemas import ClassificacaoIA

logger = logging.getLogger(__name__)


class ConfiguracaoErro(Exception):
    """Falta alguma configuração (ex.: chave da API)."""


class ClassificadorErro(Exception):
    """A IA falhou ou devolveu algo inválido mesmo após as tentativas."""


@lru_cache(maxsize=1)
def _cliente() -> Anthropic:
    # O SDK lê ANTHROPIC_API_KEY do ambiente; checamos antes para dar um erro claro.
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ConfiguracaoErro("ANTHROPIC_API_KEY não configurada.")
    return Anthropic()


def extrair_json(texto: str) -> dict:
    """Extrai o objeto JSON do texto, mesmo se o modelo envolver em ```json ... ```."""
    texto = re.sub(r"```(?:json)?", "", texto).strip()
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1 or fim < inicio:
        raise ValueError("Nenhum objeto JSON encontrado na resposta da IA.")
    return json.loads(texto[inicio : fim + 1])


def classificar_mensagem(mensagem: str) -> ClassificacaoIA:
    """Envia a mensagem para a IA e devolve a classificação já validada."""
    cliente = _cliente()
    ultimo_erro: Exception | None = None

    for tentativa in range(1, MAX_TENTATIVAS_IA + 1):
        try:
            resposta = cliente.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=400,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": montar_mensagem_usuario(mensagem)}],
            )
        except APIError as erro:
            logger.error("Erro na API da IA (tentativa %s): %s", tentativa, erro)
            ultimo_erro = erro
            continue

        texto = "".join(b.text for b in resposta.content if b.type == "text")
        try:
            return ClassificacaoIA.model_validate(extrair_json(texto))
        except (ValueError, ValidationError) as erro:
            logger.warning("Resposta inválida da IA (tentativa %s): %s", tentativa, erro)
            ultimo_erro = erro

    raise ClassificadorErro(f"Não foi possível obter uma classificação válida: {ultimo_erro}")
