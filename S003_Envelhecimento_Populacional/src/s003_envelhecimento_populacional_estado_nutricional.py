from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "dados_brutos"
PROCESSED_DIR = ROOT / "dados_processados"
METADATA_DIR = ROOT / "metadados"
LOG_DIR = ROOT / "logs"
RESULTS_DIR = ROOT / "resultados"

HEADERS = {
    "User-Agent": (
        "EnvelhecimentoPopulacionalBrasil/1.0 "
        "(projeto acadêmico de PLN sobre envelhecimento e estado nutricional)"
    )
}

PAUSA_ENTRE_REQUISICOES = 1
TIMEOUT = 30

URL_IBGE_SIDRA = "https://apisidra.ibge.gov.br/values"
URL_IBGE_CENSO = "https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html"
URL_SISVAN_API = "https://apidadosabertos.saude.gov.br/sisvan/estado-nutricional"
URL_SISVAN_DADOS = "https://dadosabertos.saude.gov.br/dataset/sisvan-estado-nutricional"
URL_MS_NUTRICAO = "https://linhasdecuidado.saude.gov.br/portal/pessoa-idosa/unidade-de-atencao-primaria/avaliacao-antropometrica/"
URL_NCBI_PUBMED = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
URL_CROSSREF_API = "https://api.crossref.org/"

FONTES = {
    "IBGE SIDRA": URL_IBGE_SIDRA,
    "IBGE Censo 2022": URL_IBGE_CENSO,
    "SISVAN API": URL_SISVAN_API,
    "SISVAN Dados Abertos": URL_SISVAN_DADOS,
    "Ministério da Saúde - Nutrição da pessoa idosa": URL_MS_NUTRICAO,
    "NCBI PubMed": URL_NCBI_PUBMED,
    "Crossref API": URL_CROSSREF_API,
}


def ensure_dirs() -> None:
    for directory in [DATA_DIR, PROCESSED_DIR, METADATA_DIR, LOG_DIR, RESULTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    for subdir in [
        DATA_DIR / "ibge",
        DATA_DIR / "sisvan",
        DATA_DIR / "datasus",
        DATA_DIR / "pubmed",
        DATA_DIR / "crossref",
        DATA_DIR / "web_scraping",
    ]:
        subdir.mkdir(parents=True, exist_ok=True)


def fetch_json(url: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    time.sleep(PAUSA_ENTRE_REQUISICOES)
    return response.json()


def fetch_ibge_sample() -> list[dict[str, Any]]:
    url = f"{URL_IBGE_SIDRA}/t/9514/n1/1/p/2022/v/allxp"
    data = fetch_json(url)
    return data if isinstance(data, list) else []


def fetch_sisvan_sample() -> Any:
    return fetch_json(URL_SISVAN_API)


def main() -> None:
    print("Iniciando execução do projeto S003 — Envelhecimento Populacional")
    ensure_dirs()
    print(f"Estrutura criada em: {ROOT}")
    print(f"Fontes mapeadas: {len(FONTES)}")

    try:
        ibge_data = fetch_ibge_sample()
        print(f"IBGE: {len(ibge_data)} registros recebidos")
        if ibge_data:
            frame = pd.DataFrame(ibge_data)
            print(f"Colunas do IBGE: {list(frame.columns[:10])}")
    except Exception as exc:
        print(f"IBGE falhou: {exc}")

    try:
        sisvan_data = fetch_sisvan_sample()
        print(f"SISVAN: resposta recebida do tipo {type(sisvan_data).__name__}")
    except Exception as exc:
        print(f"SISVAN falhou: {exc}")

    meta = {
        "projeto": "S003_Envelhecimento_Populacional",
        "status": "execucao_ok",
        "fontes": list(FONTES.keys()),
    }
    (METADATA_DIR / "metadata_execucao.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Execução concluída com sucesso.")
    print("Arquivo de metadados salvo em:", METADATA_DIR / "metadata_execucao.json")


if __name__ == "__main__":
    main()
