"""Testes sem chamar a IA de verdade: a função de classificação é substituída (mock)."""
import pytest
from fastapi.testclient import TestClient

from app import main
from app.classifier import ClassificadorErro, extrair_json
from app.schemas import Categoria, ClassificacaoIA, Prioridade, Sentimento

client = TestClient(main.app)


def _ia(categoria=Categoria.RECLAMACAO, confianca=0.95) -> ClassificacaoIA:
    return ClassificacaoIA(
        categoria=categoria,
        prioridade=Prioridade.ALTA,
        sentimento=Sentimento.NEGATIVO,
        resumo="Resumo de teste.",
        confianca=confianca,
    )


@pytest.fixture(autouse=True)
def sem_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_reclamacao_vai_para_sac(monkeypatch):
    monkeypatch.setattr(main, "classificar_mensagem", lambda m: _ia())
    r = client.post("/classificar", json={"mensagem": "Fui cobrado duas vezes!", "canal": "email"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["categoria"] == "reclamacao"
    assert corpo["setor_destino"] == "SAC"
    assert corpo["requer_revisao_humana"] is False
    assert corpo["canal"] == "email"


def test_baixa_confianca_vai_para_revisao(monkeypatch):
    monkeypatch.setattr(main, "classificar_mensagem", lambda m: _ia(Categoria.DUVIDA, 0.3))
    corpo = client.post("/classificar", json={"mensagem": "hmm talvez isso?"}).json()
    assert corpo["requer_revisao_humana"] is True
    assert corpo["setor_destino"] == "Triagem manual"


def test_categoria_outro_vai_para_revisao(monkeypatch):
    monkeypatch.setattr(main, "classificar_mensagem", lambda m: _ia(Categoria.OUTRO, 0.99))
    corpo = client.post("/classificar", json={"mensagem": "compre seguidores agora"}).json()
    assert corpo["requer_revisao_humana"] is True


def test_mensagem_vazia_retorna_422():
    assert client.post("/classificar", json={"mensagem": ""}).status_code == 422


def test_api_key_obrigatoria(monkeypatch):
    monkeypatch.setenv("API_KEY", "segredo")
    monkeypatch.setattr(main, "classificar_mensagem", lambda m: _ia())
    assert client.post("/classificar", json={"mensagem": "olá, tudo bem?"}).status_code == 401
    ok = client.post("/classificar", json={"mensagem": "olá, tudo bem?"}, headers={"X-API-Key": "segredo"})
    assert ok.status_code == 200


def test_falha_da_ia_retorna_502(monkeypatch):
    def falha(_):
        raise ClassificadorErro("boom")

    monkeypatch.setattr(main, "classificar_mensagem", falha)
    assert client.post("/classificar", json={"mensagem": "preciso de ajuda"}).status_code == 502


def test_extrair_json_com_markdown():
    texto = 'Aqui está:\n```json\n{"a": 1}\n```'
    assert extrair_json(texto) == {"a": 1}


def test_extrair_json_invalido():
    with pytest.raises(ValueError):
        extrair_json("sem json aqui")
