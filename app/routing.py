"""Regras de negócio determinísticas: para qual setor enviar e quando pedir revisão humana.

A IA só interpreta a mensagem. A decisão de roteamento fica no código, onde é
previsível e fácil de testar.
"""
from app.config import limiar_confianca
from app.schemas import Categoria, ClassificacaoIA, ClassificacaoSaida, MensagemEntrada

SETOR_POR_CATEGORIA: dict[Categoria, str] = {
    Categoria.DUVIDA: "Atendimento",
    Categoria.RECLAMACAO: "SAC",
    Categoria.SOLICITACAO: "Operações",
    Categoria.ELOGIO: "Marketing",
    Categoria.OUTRO: "Triagem manual",
}


def montar_saida(entrada: MensagemEntrada, ia: ClassificacaoIA) -> ClassificacaoSaida:
    revisao = ia.confianca < limiar_confianca() or ia.categoria == Categoria.OUTRO
    return ClassificacaoSaida(
        **ia.model_dump(),
        setor_destino="Triagem manual" if revisao else SETOR_POR_CATEGORIA[ia.categoria],
        requer_revisao_humana=revisao,
        remetente=entrada.remetente,
        canal=entrada.canal,
        mensagem_original=entrada.mensagem,
    )
