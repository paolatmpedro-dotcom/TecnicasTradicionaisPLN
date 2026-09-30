# S003 — Envelhecimento Populacional no Brasil e Estado Nutricional

## Construção, ampliação, organização e análise de um corpus para PLN

Este projeto constrói e analisa um corpus relacionado ao **envelhecimento populacional no Brasil** e ao **estado nutricional da população com 60 anos ou mais**.

O pipeline atualmente executável coleta literatura científica do **NCBI PubMed**. IBGE/SIDRA, SISVAN/Ministério da Saúde, DATASUS, Crossref e páginas institucionais são fontes planejadas para ampliações futuras, ainda não integradas ao script.

## Objetivo

Construir e analisar um corpus temático, aplicando técnicas de Processamento de Linguagem Natural (PLN) para:

- coleta e organização dos dados;
- limpeza e validação textual;
- deduplicação;
- geração de metadados;
- pré-processamento em português;
- representação TF-IDF;
- busca por similaridade;
- comparação com baseline lexical;
- avaliação por Precision@1, Precision@3, Recall@3 e MRR;
- análise de erros de recuperação.

## Estrutura

```text
S003_Envelhecimento_Populacional_GitHub/
├── README.md
├── requirements.txt
├── LICENSE
├── .gitignore
├── RELATORIO_TECNICO.md
├── notebooks/
│   └── README.md
├── src/
│   ├── s003_envelhecimento_populacional_estado_nutricional.py
│   └── s003_envelhecimento_populacional_estado_nutricional_final.py
├── dados_brutos/
│   ├── ibge/
│   ├── sisvan/
│   ├── datasus/
│   ├── pubmed/
│   ├── crossref/
│   └── web_scraping/
├── dados_processados/
├── metadados/
├── resultados/
└── logs/
```

## Como executar

### 1. Clonar o repositório

```bash
git clone URL_DO_SEU_REPOSITORIO
cd S003_Envelhecimento_Populacional_GitHub
```

### 2. Criar ambiente virtual

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Executar

O script executável usado pelo notebook está em:

```text
src/s003_envelhecimento_populacional_estado_nutricional_final.py
```

O notebook em `notebooks/` executa esse script, que coleta até 25 artigos por tema do PubMed, deduplica por PMID, gera o corpus, aplica pré-processamento, compara busca TF-IDF com baseline lexical, avalia resultados e cria quatro gráficos. Os rótulos de relevância são heurísticos e não substituem anotação humana.

Para executar diretamente pelo terminal, use `python src/s003_envelhecimento_populacional_estado_nutricional_final.py` na raiz do projeto.

## Pipeline

```text
PubMed E-utilities
      ↓
Coleta por temas e deduplicação por PMID
      ↓
Corpus bibliográfico bruto
      ↓
Normalização, stopwords e stemming
      ↓
Corpus processado e TF-IDF
      ↓
Busca por cosseno e baseline lexical
      ↓
Baseline lexical
      ↓
Precision@1 / Precision@3 / Recall@3 / MRR
      ↓
Análise de erros
```

## Fonte implementada

- **NCBI PubMed E-utilities**, para títulos, resumos e metadados bibliográficos.

IBGE/SIDRA, Censo, SISVAN, DATASUS, Crossref e páginas institucionais são fontes planejadas, mas ainda não são consultadas pelo script.

## Metodologia

O corpus combina título e resumo, remove duplicatas por PMID e mantém metadados bibliográficos. O pré-processamento é bilíngue (português/inglês), com normalização, tokenização, stopwords e stemming Snowball. A representação usa TF-IDF com unigramas e bigramas.

A busca textual compara:

**TF-IDF + similaridade de cosseno**

Como comparação, é utilizado um:

**baseline por sobreposição lexical de palavras**

As métricas são Precision@1, Precision@3, Recall@3 e MRR. A análise de erros registra falsos positivos e documentos relevantes heurísticos que ficaram fora do Top-3. Como a tarefa é ranqueamento, não se usa matriz de confusão.

As categorias são inferidas por regras de palavras-chave em títulos e resumos; os rótulos não são revisados por anotadores. Portanto, a avaliação é exploratória. Os registros brutos e o corpus processado são gerados localmente; o manifesto bibliográfico, as métricas agregadas e os quatro gráficos ficam disponíveis como entregáveis versionáveis.

O pipeline gera:

- `resultados/01_documentos_por_tema.png`
- `resultados/02_termos_tfidf.png`
- `resultados/03_comparacao_metricas.png`
- `resultados/04_relevancia_top3.png`

## Limitações

O próprio projeto registra que um corpus pequeno limita a capacidade de generalização. A categorização por origem não equivale a uma anotação humana independente, e frequência lexical não deve ser interpretada automaticamente como importância temática.

Por isso, a classificação supervisionada não é apresentada como resultado principal quando não existem exemplos suficientes por classe.

## Reprodutibilidade

Os dados coletados por APIs e scraping podem variar conforme disponibilidade das fontes, alterações nos endpoints e conteúdo publicado. Por isso, o repositório mantém o código e a metodologia, enquanto dados gerados automaticamente são tratados como artefatos de execução.

## Autoria

Projeto acadêmico — https://colab.research.google.com/drive/10qaQpMrsqJ_dweSAPRB_1g5E_1KuBIta?authuser=3

## Licença

MIT License.
