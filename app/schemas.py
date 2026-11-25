"""Modelos de dados (equivalentes a DTOs em Java) com validação via Pydantic."""
from enum import Enum

from pydantic import BaseModel, Field


class Categoria(str, Enum):
    DUVIDA = "duvida"
    RECLAMACAO = "reclamacao"
    SOLICITACAO = "solicitacao"
    ELOGIO = "elogio"
    OUTRO = "outro"


class Prioridade(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


class Sentimento(str, Enum):
    POSITIVO = "positivo"
    NEUTRO = "neutro"
    NEGATIVO = "negativo"


class MensagemEntrada(BaseModel):
    """Corpo da requisição que o Make envia para a API."""

    mensagem: str = Field(..., min_length=3, max_length=4000)
    remetente: str | None = Field(default=None, max_length=200)
    canal: str | None = Field(default=None, max_length=50)  # ex.: email, whatsapp, site


class ClassificacaoIA(BaseModel):
    """O que esperamos que a IA devolva. Se vier fora disso, a validação falha."""

    categoria: Categoria
    prioridade: Prioridade
    sentimento: Sentimento
    resumo: str = Field(..., min_length=1, max_length=300)
    confianca: float = Field(..., ge=0.0, le=1.0)


class ClassificacaoSaida(ClassificacaoIA):
    """Resposta final da API: resultado da IA + decisões de roteamento."""

    setor_destino: str
    requer_revisao_humana: bool
    remetente: str | None = None
    canal: str | None = None
    mensagem_original: str
