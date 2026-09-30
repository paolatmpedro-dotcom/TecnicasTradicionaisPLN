from __future__ import annotations

import json
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "dados_brutos"
PROCESSED_DIR = ROOT / "dados_processados"
METADATA_DIR = ROOT / "metadados"
LOG_DIR = ROOT / "logs"
RESULTS_DIR = ROOT / "resultados"

HEADERS = {
    "User-Agent": (
        "EnvelhecimentoPopulacionalBrasil/1.0 "
        "(projeto acadêmico de PLN; contato: projeto local)"
    )
}
EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
MAX_ARTIGOS_POR_TEMA = 25
TIMEOUT = 30
TOP_K = 3
PAUSA_ENTRE_REQUISICOES = 0.4

TEMAS = {
    "envelhecimento": {
        "rotulo": "Envelhecimento",
        "consulta_pubmed": (
            '(elderly[Title/Abstract] OR aged[Title/Abstract] OR '
            '"older adults"[Title/Abstract]) AND '
            '(Brazil[Title/Abstract] OR Brazilian[Title/Abstract])'
        ),
        "consulta_avaliacao": "demographic transition longevity Brazil older populations",
    },
    "estado_nutricional": {
        "rotulo": "Estado nutricional",
        "consulta_pubmed": (
            '(nutrition[Title/Abstract] OR nutritional[Title/Abstract] OR '
            'malnutrition[Title/Abstract]) AND '
            '(elderly[Title/Abstract] OR aged[Title/Abstract]) AND '
            '(Brazil[Title/Abstract] OR Brazilian[Title/Abstract])'
        ),
        "consulta_avaliacao": "diet quality body composition Brazil seniors",
    },
    "sarcopenia": {
        "rotulo": "Sarcopenia e fragilidade",
        "consulta_pubmed": (
            '(sarcopenia[Title/Abstract] OR frailty[Title/Abstract]) AND '
            '(elderly[Title/Abstract] OR aged[Title/Abstract]) AND '
            '(Brazil[Title/Abstract] OR Brazilian[Title/Abstract])'
        ),
        "consulta_avaliacao": "muscle strength decline physical vulnerability Brazil",
    },
}
REGRAS_CATEGORIA = {
    "envelhecimento": r"\b(?:population aging|population ageing|aging population|ageing population|demographic transition|envelhecimento populacional)\b",
    "estado_nutricional": r"\b(?:nutritional status|malnutrition|undernutrition|dietary assessment|diet quality|nutrition assessment|food intake|estado nutricional|desnutrição)\b",
    "sarcopenia": r"\b(?:sarcopenia|muscle strength|muscle mass|grip strength|physical frailty|fragilidade física|força muscular)\b",
}

PORTUGUESE_STOPWORDS = set(
    "a ao aos aquela aquelas aquele aqueles aquilo as ate com como da das de "
    "dela delas dele deles depois do dos e ela elas ele eles em entre era eram "
    "essa essas esse esses esta estamos estao estas estava estavam este estes "
    "eu foi foram isso isto ja lhe lhes mais mas me mesmo meu meus minha minhas "
    "muito na nas nao nem no nos nossa nossas nosso nossos num numa o os ou para "
    "pela pelas pelo pelos por qual quando que quem se seja sem ser seu seus "
    "sua suas tambem te tem tendo tenho ter teu teus tua tuas um uma umas uns voce voces"
    .split()
)
STOPWORDS = {
    "por": PORTUGUESE_STOPWORDS,
    "eng": set(ENGLISH_STOP_WORDS),
}
STEMMERS = {
    "por": SnowballStemmer("portuguese"),
    "eng": SnowballStemmer("english"),
}


def ensure_dirs() -> None:
    for directory in [DATA_DIR, PROCESSED_DIR, METADATA_DIR, LOG_DIR, RESULTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "pubmed").mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    line = f"{timestamp} {message}"
    print(line)
    with (LOG_DIR / "execucao.log").open("a", encoding="utf-8") as log_file:
        log_file.write(line + "\n")


def request_text(url: str, params: dict[str, Any]) -> str:
    response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    time.sleep(PAUSA_ENTRE_REQUISICOES)
    return response.text


def element_text(parent: ET.Element, path: str) -> str:
    element = parent.find(path)
    if element is None:
        return ""
    return " ".join(part.strip() for part in element.itertext() if part.strip())


def parse_pubmed_xml(xml_text: str, category: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    documents = []
    for article in root.findall(".//PubmedArticle"):
        citation = article.find("MedlineCitation")
        article_data = citation.find("Article") if citation is not None else None
        if article_data is None:
            continue

        pmid = element_text(article, ".//PMID")
        title = element_text(article_data, "ArticleTitle")
        abstract_parts = [
            " ".join(part.strip() for part in section.itertext() if part.strip())
            for section in article_data.findall("Abstract/AbstractText")
        ]
        abstract = " ".join(part for part in abstract_parts if part)
        if not pmid or not (title or abstract):
            continue

        year = element_text(article_data, "Journal/JournalIssue/PubDate/Year")
        if not year:
            date_text = element_text(article_data, "Journal/JournalIssue/PubDate/MedlineDate")
            year_match = re.search(r"\b(?:19|20)\d{2}\b", date_text)
            year = year_match.group(0) if year_match else ""
        doi = next(
            (
                item.text or ""
                for item in article.findall(".//ArticleId")
                if item.attrib.get("IdType") == "doi"
            ),
            "",
        )
        language = element_text(article_data, "Language") or "eng"
        documents.append(
            {
                "pmid": pmid,
                "titulo": title,
                "resumo": abstract,
                "ano": year,
                "periodico": element_text(article_data, "Journal/Title"),
                "doi": doi,
                "idioma": language.lower(),
                "consultas_coleta": [category],
                "fonte": "NCBI PubMed",
            }
        )
    return documents


def collect_pubmed_corpus() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    documents_by_id: dict[str, dict[str, Any]] = {}
    audit = []

    for category, config in TEMAS.items():
        try:
            search_json = request_text(
                f"{EUTILS_URL}/esearch.fcgi",
                {
                    "db": "pubmed",
                    "term": config["consulta_pubmed"],
                    "retmax": MAX_ARTIGOS_POR_TEMA,
                    "retmode": "json",
                    "sort": "relevance",
                },
            )
            search_result = json.loads(search_json)["esearchresult"]
            pmids = search_result.get("idlist", [])
            if not pmids:
                audit.append(
                    {"categoria": category, "total_encontrado": int(search_result.get("count", 0)), "coletado": 0}
                )
                continue

            xml_text = request_text(
                f"{EUTILS_URL}/efetch.fcgi",
                {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"},
            )
            topic_documents = parse_pubmed_xml(xml_text, category)
            for document in topic_documents:
                pmid = document["pmid"]
                if pmid in documents_by_id:
                    queries = set(documents_by_id[pmid]["consultas_coleta"])
                    queries.add(category)
                    documents_by_id[pmid]["consultas_coleta"] = sorted(queries)
                else:
                    documents_by_id[pmid] = document
            audit.append(
                {
                    "categoria": category,
                    "total_encontrado": int(search_result.get("count", 0)),
                    "coletado": len(topic_documents),
                }
            )
        except (requests.RequestException, KeyError, ValueError, ET.ParseError) as exc:
            audit.append({"categoria": category, "erro": str(exc), "coletado": 0})
            log(f"Falha na coleta da categoria {category}: {exc}")

    documents = list(documents_by_id.values())
    if not documents:
        raise RuntimeError(
            "Nenhum artigo foi coletado do PubMed. Verifique a conexão e tente novamente."
        )
    for document in documents:
        searchable_text = f"{document['titulo']} {document['resumo']}"
        document["categorias"] = [
            category
            for category, pattern in REGRAS_CATEGORIA.items()
            if re.search(pattern, searchable_text, flags=re.IGNORECASE)
        ]
    return documents, audit


def normalize_language(language: str) -> str:
    return "por" if language.lower().startswith(("por", "pt")) else "eng"


def preprocess_text(text: str, language: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = normalized.encode("ascii", "ignore").decode("ascii").lower()
    tokens = re.findall(r"[a-z]{2,}", normalized)
    language_key = normalize_language(language)
    stopwords = STOPWORDS[language_key]
    stemmer = STEMMERS[language_key]
    return " ".join(stemmer.stem(token) for token in tokens if token not in stopwords)


def build_processed_corpus(documents: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for document in documents:
        text = " ".join([document["titulo"], document["resumo"]]).strip()
        rows.append(
            {
                **document,
                "categorias": ";".join(document["categorias"]),
                "texto": text,
                "texto_processado": preprocess_text(text, document["idioma"]),
            }
        )
    corpus = pd.DataFrame(rows)
    corpus = corpus[corpus["texto_processado"].str.strip().ne("")].reset_index(drop=True)
    if corpus.empty:
        raise RuntimeError("Os registros coletados não contêm texto para análise.")
    return corpus


def lexical_overlap(query: str, documents: list[str]) -> np.ndarray:
    query_terms = set(query.split())
    if not query_terms:
        return np.zeros(len(documents))
    return np.array(
        [len(query_terms.intersection(set(text.split()))) / len(query_terms) for text in documents]
    )


def evaluate_retrieval(
    corpus: pd.DataFrame, matrix: Any, vectorizer: TfidfVectorizer
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows = []
    ranking_rows = []
    error_rows = []
    processed_documents = corpus["texto_processado"].tolist()
    methods = ["TF-IDF", "Baseline lexical"]

    for category, config in TEMAS.items():
        query = config["consulta_avaliacao"]
        processed_query = preprocess_text(query, "eng")
        tfidf_query = vectorizer.transform([processed_query])
        scores_by_method = {
            "TF-IDF": cosine_similarity(tfidf_query, matrix).ravel(),
            "Baseline lexical": lexical_overlap(processed_query, processed_documents),
        }
        relevant_indices = {
            index
            for index, categories in enumerate(corpus["categorias"].str.split(";"))
            if category in categories
        }

        for method in methods:
            scores = scores_by_method[method]
            ranking = np.argsort(scores)[::-1]
            top_indices = ranking[:TOP_K]
            relevant_hits = [index for index in top_indices if index in relevant_indices]
            first_relevant_rank = next(
                (rank for rank, index in enumerate(top_indices, start=1) if index in relevant_indices),
                None,
            )
            metric_rows.append(
                {
                    "categoria": category,
                    "consulta": query,
                    "metodo": method,
                    "precision_at_1": float(bool(top_indices.size and top_indices[0] in relevant_indices)),
                    "precision_at_3": len(relevant_hits) / max(1, len(top_indices)),
                    "recall_at_3": len(relevant_hits) / max(1, len(relevant_indices)),
                    "mrr": 1 / first_relevant_rank if first_relevant_rank else 0.0,
                    "documentos_relevantes_rotulo_heuristico": len(relevant_indices),
                }
            )

            for rank, index in enumerate(top_indices, start=1):
                is_relevant = index in relevant_indices
                document = corpus.iloc[index]
                ranking_rows.append(
                    {
                        "categoria_consulta": category,
                        "consulta": query,
                        "metodo": method,
                        "posicao": rank,
                        "pmid": document["pmid"],
                        "titulo": document["titulo"],
                        "pontuacao": float(scores[index]),
                        "relevante_rotulo_fraco": is_relevant,
                    }
                )
                if not is_relevant:
                    error_rows.append(
                        {
                            "categoria_consulta": category,
                            "metodo": method,
                            "tipo_erro": "falso_positivo",
                            "pmid": document["pmid"],
                            "titulo": document["titulo"],
                        }
                    )

            retrieved = set(top_indices.tolist())
            for index in sorted(relevant_indices - retrieved):
                error_rows.append(
                    {
                        "categoria_consulta": category,
                        "metodo": method,
                        "tipo_erro": "nao_recuperado_no_top_3",
                        "pmid": corpus.iloc[index]["pmid"],
                        "titulo": corpus.iloc[index]["titulo"],
                    }
                )

    return pd.DataFrame(metric_rows), pd.DataFrame(ranking_rows), pd.DataFrame(error_rows)


def save_visualizations(
    corpus: pd.DataFrame,
    matrix: Any,
    vectorizer: TfidfVectorizer,
    metrics: pd.DataFrame,
    rankings: pd.DataFrame,
) -> list[str]:
    sns.set_theme(style="whitegrid", palette="colorblind")
    figure_paths = []

    category_counts = Counter(
        category
        for categories in corpus["categorias"].str.split(";")
        for category in categories
        if category in TEMAS
    )
    category_frame = pd.DataFrame(
        [{"tema": TEMAS[key]["rotulo"], "documentos": count} for key, count in category_counts.items()]
    )
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.barplot(data=category_frame, x="tema", y="documentos", ax=ax, color="#287271")
    ax.set(title="Documentos coletados por tema", xlabel="Tema", ylabel="Documentos")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    path = RESULTS_DIR / "01_documentos_por_tema.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    figure_paths.append(path.name)

    mean_tfidf = np.asarray(matrix.mean(axis=0)).ravel()
    term_scores = pd.Series(mean_tfidf, index=vectorizer.get_feature_names_out()).nlargest(15)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(x=term_scores.values, y=term_scores.index, ax=ax, color="#d17a22")
    ax.set(title="15 termos com maior TF-IDF médio", xlabel="TF-IDF médio", ylabel="Termo")
    fig.tight_layout()
    path = RESULTS_DIR / "02_termos_tfidf.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    figure_paths.append(path.name)

    metric_columns = ["precision_at_1", "precision_at_3", "recall_at_3", "mrr"]
    mean_metrics = metrics.groupby("metodo", as_index=False)[metric_columns].mean()
    metric_long = mean_metrics.melt(id_vars="metodo", var_name="metrica", value_name="valor")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=metric_long, x="metrica", y="valor", hue="metodo", ax=ax)
    ax.set(title="Métricas médias da busca: TF-IDF e baseline", xlabel="Métrica", ylabel="Média")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    path = RESULTS_DIR / "03_comparacao_metricas.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    figure_paths.append(path.name)

    tfidf_rankings = rankings[rankings["metodo"].eq("TF-IDF")]
    hit_matrix = np.zeros((len(TEMAS), TOP_K), dtype=int)
    labels = []
    for row_index, (category, config) in enumerate(TEMAS.items()):
        labels.append(config["rotulo"])
        subset = tfidf_rankings[tfidf_rankings["categoria_consulta"].eq(category)]
        for _, result in subset.iterrows():
            hit_matrix[row_index, int(result["posicao"]) - 1] = int(result["relevante_rotulo_fraco"])
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.heatmap(
        hit_matrix,
        annot=True,
        fmt="d",
        cmap=sns.color_palette(["#d9e2e1", "#287271"], as_cmap=True),
        vmin=0,
        vmax=1,
        cbar=False,
        xticklabels=[f"Top {rank}" for rank in range(1, TOP_K + 1)],
        yticklabels=labels,
        ax=ax,
    )
    ax.set(title="Relevância dos resultados TF-IDF por posição", xlabel="Posição recuperada", ylabel="Consulta")
    fig.tight_layout()
    path = RESULTS_DIR / "04_relevancia_top3.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    figure_paths.append(path.name)
    return figure_paths


def main() -> None:
    ensure_dirs()
    (LOG_DIR / "execucao.log").write_text("", encoding="utf-8")
    log("Iniciando coleta e análise do corpus S003.")

    documents, collection_audit = collect_pubmed_corpus()
    raw_path = DATA_DIR / "pubmed" / "pubmed_corpus.json"
    raw_path.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    corpus = build_processed_corpus(documents)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    matrix = vectorizer.fit_transform(corpus["texto_processado"])
    metrics, rankings, errors = evaluate_retrieval(corpus, matrix, vectorizer)
    figures = save_visualizations(corpus, matrix, vectorizer, metrics, rankings)

    corpus_path = PROCESSED_DIR / "corpus_processado.csv"
    metrics_path = RESULTS_DIR / "metricas_busca.csv"
    rankings_path = RESULTS_DIR / "ranking_busca_top3.csv"
    errors_path = RESULTS_DIR / "analise_erros.csv"
    manifest_path = METADATA_DIR / "corpus_manifest.csv"
    corpus.to_csv(corpus_path, index=False, encoding="utf-8-sig")
    metrics.to_csv(metrics_path, index=False, encoding="utf-8-sig")
    rankings.to_csv(rankings_path, index=False, encoding="utf-8-sig")
    errors.to_csv(errors_path, index=False, encoding="utf-8-sig")
    manifest_columns = [
        "pmid",
        "doi",
        "ano",
        "periodico",
        "idioma",
        "categorias",
        "consultas_coleta",
        "fonte",
    ]
    corpus[manifest_columns].to_csv(
        manifest_path, index=False, encoding="utf-8-sig"
    )

    category_counts = {
        category: int(corpus["categorias"].str.split(";").apply(lambda values: category in values).sum())
        for category in TEMAS
    }
    metadata = {
        "projeto": "S003_Envelhecimento_Populacional",
        "status": "concluido",
        "executado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte_coletada": "NCBI PubMed E-utilities",
        "consultas": {key: value["consulta_pubmed"] for key, value in TEMAS.items()},
        "documentos_unicos": int(len(corpus)),
        "documentos_por_categoria": category_counts,
        "coleta_por_consulta": collection_audit,
        "pre_processamento": [
            "normalizacao Unicode e conversao para minusculas",
            "remocao de acentos e pontuacao",
            "tokenizacao por expressao regular",
            "remocao de stopwords em ingles e portugues",
            "stemming Snowball conforme idioma registrado no PubMed",
        ],
        "representacao": "TF-IDF com unigramas e bigramas",
        "avaliacao": {
            "metrica": ["Precision@1", "Precision@3", "Recall@3", "MRR"],
            "baseline": "sobreposicao lexical",
            "rotulos": "heuristicos, inferidos por palavras-chave no titulo e resumo; nao sao anotacao humana",
        },
        "visualizacoes": figures,
        "arquivos_gerados": [
            str(raw_path.relative_to(ROOT)),
            str(corpus_path.relative_to(ROOT)),
            str(metrics_path.relative_to(ROOT)),
            str(rankings_path.relative_to(ROOT)),
            str(errors_path.relative_to(ROOT)),
            str(manifest_path.relative_to(ROOT)),
        ],
    }
    (METADATA_DIR / "metadata_execucao.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    log(f"Corpus salvo: {len(corpus)} documentos unicos.")
    log(f"Metricas e rankings salvos em {RESULTS_DIR}.")
    log(f"Visualizacoes geradas: {len(figures)}.")
    log("Execucao concluida.")
    print("\nMétricas por consulta e método:")
    print(metrics.to_string(index=False))
    print(f"\nCorpus processado: {corpus_path}")
    print(f"Gráficos: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
