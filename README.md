# S003 — Envelhecimento Populacional no Brasil e Estado Nutricional

## Construção, ampliação, organização e análise de um corpus para PLN

Este projeto constrói e analisa um corpus relacionado ao **envelhecimento populacional no Brasil** e ao **estado nutricional da população com 60 anos ou mais**.

O trabalho integra dados públicos, informações institucionais e literatura científica, utilizando fontes como **IBGE/SIDRA, SISVAN/Ministério da Saúde, DATASUS, PubMed e Crossref**.

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
│   └── s003_envelhecimento_populacional_estado_nutricional.py
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

O arquivo principal está em:

```text
src/s003_envelhecimento_populacional_estado_nutricional.py
```

O projeto original foi desenvolvido para execução em ambiente Colab e contém células de instalação/importação, coleta, processamento e análise.

> Recomenda-se executar as etapas na ordem apresentada no arquivo, pois as etapas posteriores dependem das variáveis e arquivos produzidos anteriormente.

## Pipeline

```text
Fontes públicas
      ↓
Coleta por APIs
      ↓
Web scraping
      ↓
Dados brutos
      ↓
Limpeza e validação
      ↓
Deduplicação
      ↓
Metadados
      ↓
Corpus processado
      ↓
Pré-processamento de PLN
      ↓
TF-IDF
      ↓
Similaridade do cosseno
      ↓
Baseline lexical
      ↓
Precision@1 / Precision@3 / Recall@3 / MRR
      ↓
Análise de erros
```

## Fontes utilizadas

- IBGE / SIDRA
- Censo Demográfico 2022
- SISVAN / Ministério da Saúde
- DATASUS
- NCBI PubMed
- Crossref
- páginas institucionais relacionadas à pessoa idosa e nutrição

## Metodologia

O corpus é organizado por categorias e recebe metadados de origem, arquivo, codificação, status, tamanho e hash SHA-256.

A busca textual utiliza:

**TF-IDF + similaridade de cosseno**

Como comparação, é utilizado um:

**baseline por sobreposição lexical de palavras**

A avaliação considera:

- Precision@1
- Precision@3
- Recall@3
- MRR

A análise também registra falsos positivos e falsos negativos no Top-3.

## Limitações

O próprio projeto registra que um corpus pequeno limita a capacidade de generalização. A categorização por origem não equivale a uma anotação humana independente, e frequência lexical não deve ser interpretada automaticamente como importância temática.

Por isso, a classificação supervisionada não é apresentada como resultado principal quando não existem exemplos suficientes por classe.

## Reprodutibilidade

Os dados coletados por APIs e scraping podem variar conforme disponibilidade das fontes, alterações nos endpoints e conteúdo publicado. Por isso, o repositório mantém o código e a metodologia, enquanto dados gerados automaticamente são tratados como artefatos de execução.

## Autoria

Projeto acadêmico — S003.

## Licença

MIT License.
