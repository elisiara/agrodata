CONTEXTO
Estou construindo um pipeline de dados em Python sobre o dataset público do IBGE sobre Pesquisa Agrícola Municipal (PAM), tabela SIDRA 5457(2000-2025) e tabela de muncipios do GOV.BR. Trabalho com spec-driven development:
a spec abaixo é a fonte da verdade e o código é consequência dela. Não
acrescente requisito que não esteja escrito aqui. Se algo estiver ambíguo,
pergunte antes de escrever código.

STACK
- Python 3.13, dependências gerenciadas com uv
- DuckDB, arquivo agrodata.duckdb na raiz do projeto
- Nenhum orquestrador. Script executável pela linha de comando.

O QUE JÁ EXISTE (use, não reimplemente)
pipeline/db.py expõe:
  conectar()                 abre o agrodata.duckdb, criando se faltar
  criar_schema(con, nome)    CREATE SCHEMA IF NOT EXISTS
O schema raw, criado pela etapa 1: seis tabelas, todas as colunas VARCHAR,
campo vazio como NULL.

ARTEFATO A PRODUZIR
pipeline/transformacao.py, executável com:
  uv run python -m pipeline.transformacao

SPEC

1. ESCOPO
Schema refined
   Lê de raw, escreve no schema refined. Nunca escreve em raw.
   Entram seis tabelas: municipio, area_colhida, area_plantada_ou_destinada_a_colheita, quantidade_produzida, rendimento_medio_da_producao, valor_da_producao

2. NOMES
   Colunas renomeadas(snake_case) e tipos de dados ajustados, com o mapa abaixo, completo e literal. Nenhuma coluna fora do mapa; nenhuma descartada.
   Motivo: é o vocabulário que vou digitar de memória nos futuros JOINs.

   area_colhida
     "Nível"-> nivel -> VARCHAR
     "Cód."-> codigo_municipio_ibge -> VARCHAR
     "Brasil e Município" -> brasil_e_municipio -> VARCHAR
     Ano -> ano -> SMALLINT
     "Algodão herbáceo (em caroço)" -> algodao_herbaceo_em_caroco -> BIGINT
     "Arroz (em casca)" -> arroz_em_casca -> BIGINT
     "Café (em grão) Total" -> cafe_em_grao_total -> BIGINT
     "Feijão (em grão)" -> feijao_em_grao_total -> BIGINT
     "Milho (em grão)" -> milho_em_grao_total -> BIGINT
     "Soja (em grão)" -> soja_em_grao_total -> BIGINT
     "Trigo (em grão)" -> trigo_em_grao_total -> BIGINT
   area_plantada_ou_destinada_a_colheita
     "Nível"-> nivel -> VARCHAR
     "Cód."-> codigo_municipio_ibge -> VARCHAR
     "Brasil e Município" -> brasil_e_municipio -> VARCHAR
     Ano -> ano -> SMALLINT
     "Algodão herbáceo (em caroço)" -> algodao_herbaceo_em_caroco -> BIGINT
     "Arroz (em casca)" -> arroz_em_casca -> BIGINT
     "Café (em grão) Total" -> cafe_em_grao_total -> BIGINT
     "Feijão (em grão)" -> feijao_em_grao_total -> BIGINT
     "Milho (em grão)" -> milho_em_grao_total -> BIGINT
     "Soja (em grão)" -> soja_em_grao_total -> BIGINT
     "Trigo (em grão)" -> trigo_em_grao_total -> BIGINT
   municipio
     "CÓDIGO DO MUNICÍPIO - TOM" -> codigo_municipio_tom -> VARCHAR
     "CÓDIGO DO MUNICÍPIO - IBGE" -> codigo_municipio_ibge -> VARCHAR
     "MUNICÍPIO - TOM" -> municipio_tom -> VARCHAR
     "MUNICÍPIO - IBGE" -> municipio_ibge -> VARCHAR
     UF -> uf -> VARCHAR
   quantidade_produzida
     "Nível"-> nivel -> VARCHAR
     "Cód."-> codigo_municipio_ibge -> VARCHAR
     "Brasil e Município" -> brasil_e_municipio -> VARCHAR
     Ano -> ano -> SMALLINT
     "Algodão herbáceo (em caroço)" -> algodao_herbaceo_em_caroco -> BIGINT
     "Arroz (em casca)" -> arroz_em_casca -> BIGINT
     "Café (em grão) Total" -> cafe_em_grao_total -> BIGINT
     "Feijão (em grão)" -> feijao_em_grao_total -> BIGINT
     "Milho (em grão)" -> milho_em_grao_total -> BIGINT
     "Soja (em grão)" -> soja_em_grao_total -> BIGINT
     "Trigo (em grão)" -> trigo_em_grao_total -> BIGINT
   rendimento_medio_da_producao
     "Nível"-> nivel -> VARCHAR
     "Cód."-> codigo_municipio_ibge -> VARCHAR
     "Brasil e Município" -> brasil_e_municipio -> VARCHAR
     Ano -> ano -> SMALLINT
     "Algodão herbáceo (em caroço)" -> algodao_herbaceo_em_caroco -> BIGINT
     "Arroz (em casca)" -> arroz_em_casca -> BIGINT
     "Café (em grão) Total" -> cafe_em_grao_total -> BIGINT
     "Feijão (em grão)" -> feijao_em_grao_total -> BIGINT
     "Milho (em grão)" -> milho_em_grao_total -> BIGINT
     "Soja (em grão)" -> soja_em_grao_total -> BIGINT
     "Trigo (em grão)" -> trigo_em_grao_total -> BIGINT
   valor_da_producao
     "Nível"-> nivel -> VARCHAR
     "Cód."-> codigo_municipio_ibge -> VARCHAR
     "Brasil e Município" -> brasil_e_municipio -> VARCHAR
     Ano -> ano -> SMALLINT
     "Algodão herbáceo (em caroço)" -> algodao_herbaceo_em_caroco -> DECIMAL(20,2)
     "Arroz (em casca)" -> arroz_em_casca -> DECIMAL(20,2)
     "Café (em grão) Total" -> cafe_em_grao_total -> DECIMAL(20,2)
     "Feijão (em grão)" -> feijao_em_grao_total -> DECIMAL(20,2)
     "Milho (em grão)" -> milho_em_grao_total -> DECIMAL(20,2)
     "Soja (em grão)" -> soja_em_grao_total -> DECIMAL(20,2)
     "Trigo (em grão)" -> trigo_em_grao_total -> DECIMAL(20,2)



3. CONVERSÂO DOS VALORES, STATUS E TIPOS
   A conversão é feita em SQL pelo DuckDB (strptime, CAST), disparada pelo Python. Motivo: o dado já está no banco; não há por que trazê-lo para a memória só para converter tipo.
   Para todas as tabelas exceto raw.municipio, observar a conversão de valor de entrada original para valor_numerico de acordo com o que segue:
    | Entrada original | `valor_numerico` |
    |---|---|
    | `123` | 123 |
    | `0` | 0 |
    | `-` | 0 |
    | `...` | NULL |
    | `..` | NULL |
    | `X` | NULL |
    | vazio | NULL |
    Não criar nenhuma nova coluna, apenas observar os valores das colunas se coincidem com o valor representado por "Entrada original" este deve ser então convertido para o valor correspondente contido em "valor_numerico".
    Para símbolos de faixa `A`–`Z` (exceto `X`) ou qualquer valor não numérico inesperado: **não inventar valor**; interromper o processamento e emitir diagnóstico, ou tratar faixas apenas após regra explícita aprovada. O parser deve validar a convenção numérica dos arquivos antes da conversão; não assumir silenciosamente que `1.234` significa decimal ou milhar. Conservar `valor_original` sem sobrescrever. `NULL` não deve ser transformado em zero. Usar tipo decimal exato (ou justificar outro tipo), sem arredondamento de valores válidos.

4. CONVERSÃO QUE FALHA
   Para tudo. Use strptime e CAST, que estouram, e nunca try_strptime, TRY_CAST ou errors="coerce", que transformam falha em nulo.
   Ao falhar: diga tabela, coluna e um exemplo do valor que não converteu, e encerre com sys.exit(1).
   Motivo: um nulo fabricado pela conversão fica indistinguível de um nulo verdadeiro do dado, para sempre.

5. DUPLICATAS
   Chave de cada tabela:
    municipio(codigo_municipio_ibge)
    area_colhida,area_plantada_ou_destinada_a_colheita,quantidade_produzida,rendimento_medio_da_producao,valor_da_producao(codigo_municipio_ibge, ano)

   Linha inteira repetida: mantém uma, e conta quantas saíram.
   Chave repetida com conteúdo diferente: para, mostra a chave e as linhas conflitantes, sys.exit(1). Não escolhe uma por conta própria.
   Motivo: escolher em silêncio é decidir sem dizer que decidiu.

6. NULOS
   Nenhuma linha é apagada por ter nulo. Nenhum nulo é preenchido.
   nulos continuam nulos: avaliação sem texto é a regra, não a exceção.
   Anomalias de negócio também ficam. refined não corrige fato; quem decide o que fazer com ele é a pergunta que o mart responde.

7. SAÍDA NA TELA
   Uma linha por tabela, no formato:
     refined.area_colhida           144.690 -> 144.690 linhas  (0 duplicatas)
   Abaixo dela, indentadas, as colunas com nulo e a contagem:
       nulos mantidos: nome coluna (valor)
   As contagens vêm do banco, milhar separado por ponto. Linha final com o total. stdout reconfigurado para utf-8.

REEXECUÇÃO
   CREATE OR REPLACE TABLE, nunca acrescenta. Rodar dez vezes = rodar uma.

ERRO
   Antes de transformar, verifica se as seis tabelas de entrada existem em raw. Faltando qualquer uma: lista quais, diz para rodar
   "uv run python -m pipeline.ingestao" e encerra com sys.exit(1).

CRITÉRIOS DE ACEITE
- Seis tabelas em refined; em cada uma, linhas que saem = linhas que entram (com este dado, 0 duplicatas em todas). Total: 729.021.
- DESCRIBE refined.rendimento_medio_da_producao mostra BIGINT nas sete colunas de cultura(algodao_herbaceo_em_caroco,arroz_em_casca,cafe_em_grao_total,feijao_em_grao_total,milho_em_grao_total,soja_em_grao_total,trigo_em_grao_total).
- sum(trigo_em_grao_total) em refined.valor_da_producao bate com
SUM(
    CAST(
        CASE
            WHEN TRIM("Trigo (em grão)") = '-' THEN '0'
            WHEN TRIM("Trigo (em grão)") IN ('...', '..', 'X') THEN NULL
            ELSE TRIM("Trigo (em grão)")
        END
        AS DECIMAL(20,2)
    )
)  em raw.valor_da_producao, centavo por centavo.
- '-' agora vale 0(zero).
- '..', '...' e 'X' agora valem NULL.
- Rodar duas vezes seguidas imprime exatamente a mesma coisa.

ENTREGA, nesta ordem
1. A spec como docstring no topo do arquivo, dizendo por que cada regra
   existe — não só o que ela manda fazer.
2. O código, com comentários apenas onde a decisão não é óbvia pelo código.
3. Uma lista final do que você assumiu e que não estava na spec. Se a lista não estiver vazia, é a minha spec que precisa melhorar.