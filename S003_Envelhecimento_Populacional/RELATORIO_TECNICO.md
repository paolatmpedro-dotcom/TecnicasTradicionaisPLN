# Relatório Técnico — S003

## 1. Identificação

**Projeto:** Envelhecimento Populacional no Brasil e Estado Nutricional  
**Área:** Processamento de Linguagem Natural (PLN)  
**Tipo:** Construção, ampliação, organização e análise de corpus.

## 2. Problema

O projeto demonstra a construção de um corpus bibliográfico sobre envelhecimento, estado nutricional e sarcopenia em estudos relacionados ao Brasil. Nesta versão, a coleta implementada consulta títulos, resumos e metadados do PubMed; as demais fontes listadas no planejamento ainda não são integradas ao pipeline executável.

## 3. Objetivo geral

Construir e analisar um corpus bibliográfico reproduzível e aplicar técnicas de PLN para recuperar documentos relacionados ao envelhecimento e ao estado nutricional da população idosa no Brasil.

## 4. Fontes

### Fonte efetivamente consultada

- **NCBI PubMed E-utilities:** consultas por tema e recuperação de registros bibliográficos (PMID, título, resumo, periódico, ano, idioma e DOI quando disponível).

IBGE/SIDRA, Censo, SISVAN, DATASUS, Crossref e páginas institucionais permanecem como fontes planejadas, mas não são coletadas pelo script desta versão.

## 5. Construção do corpus

O script consulta até 25 registros por tema em três consultas PubMed: envelhecimento, estado nutricional e sarcopenia/fragilidade. Os registros são deduplicados por PMID e as consultas de origem são preservadas. Títulos e resumos são consolidados em um corpus; o manifesto em `metadados/corpus_manifest.csv` registra identificadores e metadados bibliográficos sem incluir o texto dos resumos.

O corpus textual bruto é salvo em `dados_brutos/pubmed/pubmed_corpus.json`, e a versão processada em `dados_processados/corpus_processado.csv`. Esses arquivos são gerados localmente e ignorados pelo Git; execute novamente o script para reconstruí-los.

## 6. Pré-processamento

O pré-processamento usa o idioma informado pelo PubMed para selecionar stopwords e o stemmer Snowball em português ou inglês. As etapas são normalização Unicode, conversão para minúsculas, remoção de acentos e pontuação, tokenização por expressão regular, remoção de stopwords e stemming. A língua predominante dos registros é variável e pode ser inglês; não se traduzem documentos.

A representação textual é TF-IDF com unigramas e bigramas, usando frequência de termo sublinear.

## 7. Busca textual

A abordagem principal é a recuperação de documentos por:

**TF-IDF + similaridade de cosseno.**

As consultas de avaliação exploram três temas: transição demográfica, qualidade da dieta/composição corporal e força muscular/fragilidade física. Elas são comparadas com documentos do corpus por similaridade do cosseno.

## 8. Baseline

O baseline utiliza a proporção de termos da consulta que também aparecem no documento pré-processado.

Essa comparação permite observar o comportamento da representação TF-IDF em relação a uma estratégia lexical simples.

## 9. Avaliação

São utilizadas Precision@1, Precision@3, Recall@3 e Mean Reciprocal Rank (MRR). Os rótulos de relevância são inferidos por regras de palavras-chave no título e resumo, independentemente da consulta de coleta. São **rótulos heurísticos**, não uma anotação humana independente; portanto, as métricas são exploratórias e podem favorecer métodos lexicais. Para uma avaliação conclusiva, é necessário revisar e anotar manualmente um conjunto de julgamentos.

### Precision@1

Verifica se o primeiro documento recuperado pertence à categoria considerada relevante.

### Precision@3

Mede a proporção de documentos relevantes entre os três primeiros resultados.

### Recall@3

Mede quanto dos documentos relevantes disponíveis foram recuperados no Top-3.

### MRR

Considera a posição do primeiro documento relevante.

## 10. Resultados e análise de erros

Na execução de 30/09/2026, o script coletou 74 registros únicos. O resultado é dinâmico e pode variar conforme a atualização do PubMed. Métricas do snapshot gerado:

| Tema | Método | P@1 | P@3 | Recall@3 | MRR |
|---|---|---:|---:|---:|---:|
| Envelhecimento | TF-IDF | 1,000 | 0,333 | 1,000 | 1,000 |
| Envelhecimento | Baseline lexical | 0,000 | 0,333 | 1,000 | 0,500 |
| Estado nutricional | TF-IDF | 1,000 | 0,333 | 0,056 | 1,000 |
| Estado nutricional | Baseline lexical | 1,000 | 0,333 | 0,056 | 1,000 |
| Sarcopenia | TF-IDF | 1,000 | 1,000 | 0,375 | 1,000 |
| Sarcopenia | Baseline lexical | 1,000 | 1,000 | 0,375 | 1,000 |

Os resultados não devem ser generalizados: os rótulos heurísticos identificaram 1 documento de envelhecimento, 18 de estado nutricional e 8 de sarcopenia no snapshot. Os CSVs em `resultados/` registram métricas, ranking Top-3, falsos positivos e documentos relevantes heurísticos não recuperados no Top-3.

A matriz de confusão não é aplicada porque a tarefa implementada é ranqueamento de busca, não classificação binária por documento.

## 11. Limitações

O corpus é uma amostra de até 25 registros por consulta, ordenada por relevância pelo PubMed; não é uma amostra probabilística. A coleta depende da disponibilidade da API, da formulação das consultas e do idioma dos resumos. O corpus pode conter artigos duplicados entre temas, resolvidos por PMID.

Além disso:

- as categorias heurísticas não substituem julgamento humano e podem introduzir viés lexical;
- o baseline e os rótulos usam sinais de palavras, o que pode inflar ou distorcer a comparação;
- sinônimos e diferenças entre português e inglês podem reduzir a recuperação;
- os resultados mudam quando o PubMed atualiza registros ou a ordem de relevância;
- frequência lexical e similaridade não equivalem a importância clínica;
- uma amostra maior e julgamentos humanos independentes são necessários para conclusões robustas.

## 12. Visualizações

O pipeline gera quatro arquivos PNG: documentos por tema, termos com maior TF-IDF médio, comparação das métricas entre métodos e relevância heurística dos resultados TF-IDF no Top-3.

## 13. Reprodutibilidade

Na raiz do projeto, execute `python -m pip install -r requirements.txt` e depois `python src/s003_envelhecimento_populacional_estado_nutricional_final.py`. A coleta e os resultados são atualizados em tempo de execução. O corpus textual bruto e processado fica local; o manifesto bibliográfico, as métricas agregadas e os quatro gráficos podem ser versionados.

## 14. Entregáveis

O repositório GitHub contém:

- código principal;
- documentação;
- requisitos de instalação;
- notebook executável e código de coleta/análise;
- manifesto de identificadores do corpus;
- métricas agregadas e quatro gráficos;
- pastas de dados processados, logs e resultados gerados localmente;
- relatório técnico.

## 15. Conclusão

O projeto implementa um fluxo reproduzível de coleta bibliográfica, pré-processamento, busca TF-IDF, comparação com baseline, avaliação exploratória, análise de erros e visualização. A avaliação ainda depende de rótulos heurísticos; a próxima melhoria metodológica é criar julgamentos humanos independentes e ampliar as fontes do corpus.
