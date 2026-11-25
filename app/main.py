"""API FastAPI: recebe a mensagem do Make, classifica com IA e devolve JSON."""
import logging
import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException

from app.classifier import ClassificadorErro, ConfiguracaoErro, classificar_mensagem
from app.routing import montar_saida
from app.schemas import ClassificacaoSaida, MensagemEntrada

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Triagem Inteligente de Mensagens",
    description="Classifica mensagens de clientes com IA e indica o setor de destino.",
    version="1.0.0",
)


def verificar_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Se API_KEY estiver definida, exige o header X-API-Key."""
    esperada = os.getenv("API_KEY")
    if not esperada:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, esperada):
        raise HTTPException(status_code=401, detail="API key inválida ou ausente.")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post(
    "/classificar",
    response_model=ClassificacaoSaida,
    dependencies=[Depends(verificar_api_key)],
)
def classificar(entrada: MensagemEntrada) -> ClassificacaoSaida:
    try:
        resultado_ia = classificar_mensagem(entrada.mensagem)
    except ConfiguracaoErro as erro:
        logger.error("Configuração ausente: %s", erro)
        raise HTTPException(status_code=500, detail="Servidor sem chave de IA configurada.")
    except ClassificadorErro as erro:
        logger.error("Falha na classificação: %s", erro)
        raise HTTPException(status_code=502, detail="A IA não retornou uma resposta válida.")

    return montar_saida(entrada, resultado_ia)
