CONTEXTO
**Status:** especificação para implementação; ainda não implementada.
**Fontes:**
  =>IBGE, Pesquisa Agrícola Municipal (PAM), tabela SIDRA 5457. Área plantada ou destinada à colheita, área colhida, quantidade produzida, rendimento médio e valor da produção das lavouras temporárias e permanentes.
    Filtros aplicados:
        Intervalo: 2000 a 2025;
        Culturas : Algodão Herbáceo(em caroço), Arroz(em casca), Café em grão(Total),  Feijão(em grão), Milho(em grão), Soja(em grão), Trigo(em grão)
        Unidade Territorial: Brasil, Municipio(UF)
    Tabelas .:
      -Área plantada ou destinada à colheita (Hectares [1988 a 2025])
      -Área colhida (Hectares)
      -Quantidade produzida (Toneladas)
      -Rendimento médio da produção (Quilogramas por Hectare)
      -Valor da produção Mil Reais [1994 a 2025]
    Link .: https://sidra.ibge.gov.br/tabela/5457
  => Tabela de municipios GOV.BR. Arquivo de dados abertos da Receita Federal contendo o código TOM, código IBGE, nome do município e Unidade Federativa (UF) em formato .csv
    Link .: https://www.gov.br/receitafederal/dados/municipios.csv).

**Escopo:** somente ingestão, e criação de uma tabela por CSV no DuckDB.

Estou construindo um pipeline de dados em Python sobre o dataset público do IBGE, de Pesquisa Agrícola Municipal (PAM), tabela SIDRA 5457( perído 2000-2025). Para complementa-lo também usei a tabela de municipios do IBGE. Trabalho com spec-driven development:
a spec abaixo é a fonte da verdade e o código é consequência dela. Não acrescente requisito que não esteja escrito aqui. Se algo estiver ambíguo, pergunte antes de escrever código.

STACK
- Python 3.13, dependências gerenciadas com uv
- pandas para ler os arquivos
- DuckDB como banco, arquivo agrodata.duckdb na raiz do projeto
- Nenhum orquestrador. Script executável pela linha de comando.

O QUE JÁ EXISTE
Só a pasta raw/ com os seis .csv e o pyproject.toml. Nenhum código ainda.

ARTEFATOS A PRODUZIR, nesta ordem
1. pipeline/db.py, o módulo de conexão que as quatro etapas do curso vão
   importar (spec própria logo abaixo; é a primeira coisa a existir)
2. pipeline/ingestao.py, executável com:
     uv run python -m pipeline.ingestao
3. ui.py, na raiz do projeto, executável com:
     uv run python ui.py
   (spec própria no fim deste prompt; ui.py e ingestao.py não se importam)

# SPEC DO pipeline/db.py (primeiro artefato)
Expõe exatamente isto, com estes nomes:
  PASTA_RAW                          Path da pasta raw/ com os seis .csv
  conectar()                         abre o agrodata.duckdb, criando se faltar
  criar_schema(con, nome)            CREATE SCHEMA IF NOT EXISTS
  gravar(con, df, schema, tabela)    grava e devolve a contagem lida do banco

D1. CAMINHOS
    PASTA_RAW e o agrodata.duckdb são resolvidos a partir da localização do
    próprio db.py (a pasta acima de pipeline/), nunca do diretório corrente.
    Motivo: rodar o script de outra pasta não pode criar um agrodata.duckdb
    vazio no lugar errado, que parece ingestão quebrada.
D2. TRÊS FUNÇÕES E UMA CONSTANTE, NADA MAIS
    db.py não lê CSV, não conhece nome de tabela, não imprime nada e não
    converte tipo. Quem decide tudo isso é cada etapa. Regra de negócio
    escondida aqui vale para todas as etapas sem aparecer em nenhuma spec.
D3. gravar
    Recria a tabela (CREATE OR REPLACE TABLE schema.tabela) com as colunas
    e os tipos do DataFrame, sem alterar nada: coluna str vira VARCHAR,
    nulo continua NULL. Não deixa view ou tabela temporária para trás.
    Devolve SELECT count(*) da tabela recém-gravada, lido do banco.
    Motivo: a contagem que aparece na tela tem que ser a do que foi
    gravado, não a do que estava na memória.
D4. CONEXÃO
    conectar() devolve a conexão aberta; quem chama é quem fecha.
    db.py não guarda conexão global.

CRITÉRIOS DE ACEITE (db.py)
- Importar pipeline.db não abre banco nem cria arquivo nenhum.
- conectar() chamado de dentro de outra pasta cria o agrodata.duckdb na raiz
  do projeto, e não na pasta corrente.
- gravar() com um DataFrame de 3 linhas devolve 3, e rodar duas vezes
  continua devolvendo 3.

# SPEC DA INGESTÃO (segundo artefato)

## 1. Escopo e nomes
  Schema de destino: raw

  Entrada GOV.BR.:

  | Arquivo CSV | Tabela de saída |
  |---|---|---|
  | `municipios_gov.csv` | `raw.municipio` |


  Entradas IBGE.:

  | Arquivo CSV | Tabela de saída |
  |---|---|---|
  | `tabela5457_area_colhida.csv` | `raw.area_colhida` |
  | `tabela5457_area_plantada_ou_destinada_a_colheita.csv` | `raw.area_plantada_ou_destinada_a_colheita` |
  | `tabela5457_quantidade_produzida.csv` | `raw.quantidade_produzida` |
  | `tabela5457_rendimento_medio_da_producao.csv` | `raw.rendimento_medio_da_producao` |
  | `tabela5457_valor_da_producao.csv` | `raw.valor_da_producao` |

  Especificaçẽos específicas para os .csvs de Entradas IBGE.:
    As 5 entradas foram inspecionadas: CSV com separador `;`, codificação UTF-8 com BOM, aspas CSV, 5.593 registros lógicos (incluindo cabeçalhos, rodapé e linhas vazias), 5.564 registros `MU`, um registro `BR`, 26 anos (2000–2025), sete culturas por ano, 182 células de medida por município, 185 campos em cada linha de dados.

    **Importante:** a quarta linha (anos) tem **179 campos**, enquanto a quinta linha (culturas) e as linhas de dados têm **185**. O parser deve aceitar a omissão das seis células vazias finais da linha de anos, preencher logicamente até 185 e propagar o ano 2025. Não exigir igualdade de largura entre todas as linhas de cabeçalho.

    As sete culturas observadas, na ordem: `Algodão herbáceo (em caroço)`, `Arroz (em casca)`, `Café (em grão) Total`, `Feijão (em grão)`, `Milho (em grão)`, `Soja (em grão)`, `Trigo (em grão)`.

    Cabeçalho e mapeamento de colunas:

    - Registro lógico CSV 1: título da tabela.
    - Registro lógico CSV 2: descrição da variável e unidade; validar contra o arquivo configurado.
    - Registro lógico CSV 3: cabeçalho descritivo (`Nível`, `Cód.`, `Brasil e Município`, ...).
    - Registro lógico CSV 4: anos nas posições 0-based `3,10,17,...,178`, demais posições vazias ou ausentes no fim da linha.
    - Registro lógico CSV 5: produtos nas posições 3 a 184; sete produtos por ano.
    - Registros seguintes: uma linha `BR`, depois linhas `MU`, seguidos de rodapé.

    Algoritmo obrigatório:
    1. Ler com `csv.reader` (`encoding='utf-8-sig'`, `delimiter=';'`, `newline=''`), **nunca** fazer `split(';')` simples: notas possuem quebras de linha dentro de campos citados.
    2. Validar largura das linhas `MU/BR` = 185 e largura da linha de produtos = 185.
    3. Completar a linha de anos com strings vazias até atingir 185 campos; rejeitar se exceder 185.
    4. Para cada posição `j` de 3 a 184, associar `ano` ao último ano não vazio visto até `j` e `cultura` à posição `j` da linha de produtos.
    5. Validar exatamente 26 anos, de 2000 a 2025, sete culturas em cada ano, mesmo conjunto e ordem de culturas nos 26 grupos, e unicidade dos pares `(ano,cultura)`.
    6. Iterar as linhas de dados até a primeira linha cujo primeiro campo começa com `Fonte:`; aceitar somente `nivel == 'MU' OU nivel == 'BR'`. Ignorar qualquer outro nível, sem inserção.
    7. Se aparecer nível com largura diferente de 185, código municipal inválido ou duplicado, **falhar**, sem truncar silenciosamente. Rejeitar estrutura de dados inesperada antes do rodapé.
    8. Emitir um registro para **cada** uma das 182 posições de medida de cada município, incluindo valores `0`, `-`, `...` e `NULL` resultantes.


## 2. Contrato de proibições e de preservação e escopo Raw

  Nenhuma conversão de tipo. Nenhum valor corrigido, preenchido ou normalizado.
  Data continua texto, nulo continua nulo.
  Motivo: a fronteira entre "o dado que chegou" e "o dado que eu decidi" precisa existir
  em algum lugar, e esse lugar é a passagem de raw para refined, na etapa 2.
  Se a correção acontecer aqui, a fronteira some.
  Manter os CSVs originais **inalterados** em `raw/` (cópia byte a byte, ou apontar para arquivos imutáveis e registrar SHA-256).
  O arquivo bruto é a evidência original; a tabela `raw.*` é uma **representação tabular derivada**, e não uma cópia byte a byte.
  Documentar essa distinção para atender ao requisito do curso de que o dado bruto não seja alterado.
  Criar exatamente uma tabela de saída por arquivo, no schema `raw`.
  Não incluir títulos, cabeçalhos, linhas `Fonte:`, `Notas`, `Legenda` ou descrições de símbolos como registros da tabela. Os CSVs originais permanecem íntegros.
  Não calcular métricas, agregações, médias, totais ou indicadores.


## 3. REEXECUÇÃO
  Rodar dez vezes tem que dar o mesmo resultado que rodar uma: a tabela é recriada (CREATE OR REPLACE),
  nunca acrescentada. É o que me deixa errar sem medo.

## 4. LEITURA DO ARQUIVO
  encoding declarado como utf-8, nunca adivinhado.
  Campo vazio continua virando nulo; não transforme em string vazia.

## 5. TIPAGEM
  Toda coluna entra como texto (dtype=str), inferência desligada.
  Motivo: As conversẽs acontecem na etapa 2, onde é uma decisão registrada.

## 6. SAÍDA NA TELA
   Uma linha por tabela, com nome qualificado e contagem de linhas vinda do
   banco (não do DataFrame), milhar separado por ponto.
   Uma linha final com o total.
   Essa saída é meu único instrumento de conferência nesta etapa.
   O stdout precisa ser reconfigurado para utf-8: rodo no Prompt de Comando
   do windows, onde acento sai embaralhado por padrão.

## 7. ERRO
   Antes de abrir o banco, verifique se os seis arquivos existem.
   Faltando qualquer um: liste os que faltam, diga em que pasta procurou e
   encerre com sys.exit(1). Não ingira parcialmente.
   Motivo: ingerir cinco de seis tabelas em silêncio produz um dashboard
   errado que parece certo.


CRITÉRIOS DE ACEITE (ingestão)
- A execução imprime seis linhas e um total de 729.021 registros.
- Rodar duas vezes seguidas imprime exatamente a mesma coisa.
- SELECT * FROM raw.area_colhida devolve todas as colunas como VARCHAR.
- Remover um arquivo da pasta faz o script parar antes de gravar qualquer
  tabela.
- O script termina sozinho e devolve o terminal: nenhum processo fica de pé.


# SPEC DO ui.py (terceiro artefato)

Quero explorar o banco pelo navegador, em vez de ler tabela no terminal.

U1. O QUE FAZ
    Abre o agrodata.duckdb da raiz do projeto, instala e carrega a extensão
    `ui` do DuckDB (INSTALL ui; LOAD ui;) e chama CALL start_ui(), que sobe
    o servidor em http://localhost:4213 e abre o navegador.
U2. FICA DE PÉ ATÉ CTRL+C
    A extensão serve enquanto a conexão estiver viva. O script mantém o
    processo rodando, imprime a URL e a instrução "Ctrl+C para encerrar", e
    no Ctrl+C fecha a conexão e sai limpo, sem traceback.
    Motivo: o arquivo .duckdb aceita um único processo escrevendo. Com o
    ui.py de pé, a ingestão falha com "Could not set lock on file". Saber
    exatamente como desligar o servidor faz parte da ferramenta.
U3. NÃO CRIA BANCO
    Se agrodata.duckdb não existir, diga que é preciso rodar a ingestão antes
    e encerre com sys.exit(1). Por isso NÃO use conectar() de pipeline/db.py,
    que cria o arquivo quando ele falta: um banco vazio aberto no navegador
    parece ingestão quebrada.
U4. SEPARAÇÃO
    ui.py não importa pipeline/ingestao.py, e a ingestão não importa ui.py:
    a ingestão não sobe servidor, não abre navegador e não depende da
    extensão ui para rodar.
U5. SAÍDA NA TELA
    Mesma regra do item 6: stdout reconfigurado para utf-8.

CRITÉRIOS DE ACEITE (ui.py)
- uv run python ui.py abre o navegador em localhost:4213 e o schema raw
  aparece com as seis tabelas.
- Ctrl+C devolve o terminal sem traceback, e logo depois a ingestão roda
  sem erro de lock.
- Renomear agrodata.duckdb faz o ui.py parar com a mensagem, sem criar arquivo
  novo.

ENTREGA, nesta ordem, para cada um dos seis arquivos
1. A spec como docstring no topo do arquivo, dizendo por que cada regra
   existe — não só o que ela manda fazer.
2. O código, com comentários apenas onde a decisão não é óbvia pelo código.
3. Uma lista final do que você assumiu e que não estava na spec. Se a lista
   não estiver vazia, é a minha spec que precisa melhorar.


