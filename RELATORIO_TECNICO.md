# Relatório Técnico — S003

## 1. Identificação

**Projeto:** Envelhecimento Populacional no Brasil e Estado Nutricional  
**Área:** Processamento de Linguagem Natural (PLN)  
**Tipo:** Construção, ampliação, organização e análise de corpus.

## 2. Problema

O projeto busca organizar informações de diferentes fontes públicas sobre envelhecimento populacional, população com 60 anos ou mais e estado nutricional, transformando essas informações em um corpus utilizável em um fluxo de PLN.

## 3. Objetivo geral

Construir e analisar um corpus relacionado ao envelhecimento populacional e ao estado nutricional da população idosa no Brasil, integrando diferentes fontes públicas e aplicando técnicas de PLN para organização, representação e recuperação de informações.

## 4. Fontes

As fontes previstas no projeto incluem:

- IBGE/SIDRA;
- Censo Demográfico;
- SISVAN/Ministério da Saúde;
- DATASUS;
- NCBI PubMed;
- Crossref;
- páginas institucionais.

## 5. Construção do corpus

O pipeline realiza:

1. preparação do ambiente;
2. organização das pastas;
3. coleta por APIs;
4. coleta por web scraping;
5. armazenamento dos dados brutos;
6. leitura e tratamento de codificação;
7. validação dos documentos;
8. cálculo de hash SHA-256;
9. deduplicação;
10. geração de metadados;
11. consolidação do corpus;
12. pré-processamento;
13. representação TF-IDF;
14. busca por similaridade;
15. avaliação;
16. análise dos erros.

## 6. Pré-processamento

O projeto trabalha com texto em português e contempla tokenização, stopwords, normalização, tratamento de ruídos e stemming/lematização conforme as etapas implementadas.

A representação principal utilizada na recuperação textual é TF-IDF.

## 7. Busca textual

A abordagem principal é a recuperação de documentos por:

**TF-IDF + similaridade de cosseno.**

As consultas de avaliação são relacionadas a:

- população e envelhecimento;
- estado nutricional e alimentação;
- sarcopenia, envelhecimento e literatura científica.

## 8. Baseline

O baseline utiliza sobreposição de palavras entre a consulta e o documento.

Essa comparação permite observar o comportamento da representação TF-IDF em relação a uma estratégia lexical simples.

## 9. Avaliação

São utilizadas:

### Precision@1

Verifica se o primeiro documento recuperado pertence à categoria considerada relevante.

### Precision@3

Mede a proporção de documentos relevantes entre os três primeiros resultados.

### Recall@3

Mede quanto dos documentos relevantes disponíveis foram recuperados no Top-3.

### MRR

Considera a posição do primeiro documento relevante.

## 10. Análise de erros

São registrados:

- falsos positivos;
- falsos negativos fora do Top-3.

A análise considera que termos genéricos como “envelhecimento”, “saúde”, “população” e “idosos” podem favorecer documentos lexicalmente semelhantes.

## 11. Limitações

O corpus pode ser pequeno em determinadas etapas do projeto. Isso limita a generalização dos resultados e torna inadequada uma avaliação supervisionada robusta quando não há quantidade suficiente de exemplos por classe.

Além disso:

- páginas públicas podem sofrer alterações;
- APIs podem mudar seus endpoints;
- disponibilidade dos dados pode variar;
- categorias derivadas da origem não substituem anotação humana;
- frequência de palavras não representa automaticamente relevância temática.

## 12. Reprodutibilidade

O código registra as fontes utilizadas e organiza os resultados em pastas específicas. As coletas são realizadas em tempo de execução, portanto os resultados podem mudar quando as fontes externas forem atualizadas.

## 13. Entregáveis

O repositório GitHub contém:

- código principal;
- documentação;
- requisitos de instalação;
- estrutura do corpus;
- pasta para dados brutos;
- pasta para dados processados;
- metadados;
- resultados;
- logs;
- relatório técnico.

## 14. Conclusão

O projeto apresenta um fluxo completo de construção e análise de corpus, desde a coleta de dados públicos até a recuperação de documentos por TF-IDF e avaliação por métricas de busca.

O pipeline permite documentar as etapas de coleta, organização, processamento, representação e avaliação, mantendo explícitas as limitações relacionadas ao tamanho e à composição do corpus.
