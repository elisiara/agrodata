CONTEXTO
Estou construindo um pipeline de dados em Python sobre o dataset público do IBGE sobre
Pesquisa Agrícola Municipal (PAM), tabela SIDRA 5457(2000-2025) e tabela de municípios do GOV.BR.
Trabalho com spec-driven development: a spec abaixo é a fonte da
verdade e o código é consequência dela. Não acrescente requisito que não
esteja escrito aqui. Se algo estiver ambíguo, pergunte antes de escrever código.

STACK
- Python 3.13, uv, DuckDB (agrodata.duckdb na raiz do projeto)
- streamlit e plotly (plotly.express), já instalados com uv add

O QUE JÁ EXISTE (use, não reimplemente)
O schema marts, com quinze tabelas, criado por pipeline/marts.py:
ranking_valor_da_producao_muncipio_por_cultura,
20_municipios_maiores_produtores_em_2025,
municipios_maior_expansao_area_plantada,
variacao_percentual_quantidade_produzida_por_cultura_2024_2025,
percentual_area_plantada_colhida_em_2025,
diferenca_area_plantada_colhida_por_estado_2025,
municipios_maior_aumento_quantidade_produzida_2000_2025,
evolucao_valor_producao_por_cultura_2000_2025,
expansao_area_sem_aumento_producao_2000_2025,
distribuicao_geografica_producao_por_estado_2000_2025,
ranking_aumento_rendimento_medio_por_cultura_2000_2025,
resumo_totais_2025,
ranking_valor_bruto_por_hectare_cultura_2025,
ranking_municipios_evolucao_rendimento_agregado_2000_2025,
concentracao_valor_producao_por_cultura_estado_2025.
O rascunho da tela em design/rascunho.html.

ARTEFATOS A PRODUZIR
painel.py, na raiz: leitura, formatação e gráficos. Não importa streamlit.
app.py, na raiz: a página. Executável com:
  uv run streamlit run app.py

SPEC
1. LEITURA (painel.py)
   ler(marts) -> dict nome -> DataFrame. Para cada nome, só
   SELECT * FROM marts.<nome>. Nenhuma outra SQL.
   Conexão com duckdb.connect("agrodata.duckdb", read_only=True), aberta e
   fechada dentro de ler(). Motivo: conexão aberta segura o arquivo, e o
   pipeline.marts não consegue gravar com o painel de pé.

2. NENHUM CÁLCULO
   Proibido em painel.py e app.py: groupby, sum, mean, count, merge, pivot,
   e qualquer conta entre colunas. Permitido: ordenar, filtrar linhas,
   head(n), renomear coluna e formatar texto.
   Motivo: número novo na tela exige um .sql novo em marts. Se faltar
   algum número, pare e diga qual mart está faltando.

3. LAYOUT (app.py) — de cima para baixo, layout="wide"
  Cabeçalho:
    Título "Produção agrícola brasileira", alinhado à esquerda.
    Subtítulo abaixo do título:
      "Culturas consideradas: Arroz, Algodão, Café, Feijão, Milho, Soja e Trigo.
       Período: 2000 a 2025."
    Identificação da fonte: "PAM · IBGE SIDRA 5457".
    Aviso discreto para indicar quando os dados exibidos forem demonstrativos
    ou quando ainda não estiverem carregados.

  Faixa fixa no topo do conteúdo:
    Quatro cartões st.metric, visíveis em todas as abas, com indicadores
    nacionais de 2025 da consulta 12:
        Valor da produção (bi R$)
        Quantidade produzida (mi t)
        Área colhida (mi ha)
        Rendimento médio (t/ha)
    Os cartões não mudam com filtros de período, cultura, UF ou município.
    Formatar os valores para leitura, sem mudar os números do mart.
    Se exibir rendimento em t/ha, deixar explícita a conversão de kg/ha.

  Navegação:
    Quatro abas, abaixo dos cartões:
      Panorama
      Distribuição por estado
      Expansão e rankings
      Produtividade e valor/ha
    Os cartões permanecem acima do conteúdo de todas as abas.

  ABA 1 — Panorama da produção agrícola
    Introdução: "Indicadores nacionais de 2025 e evolução das culturas PAM."

    Duas colunas:
      Coluna esquerda:
        Gráfico de rosca — "05 · Área plantada: colhida × não colhida"
        Valores de percentual_area_plantada_colhida e
        percentual_area_plantada_nao_colhida.
        Exibir percentuais no gráfico/legenda; parcelas somam 100%.

      Coluna direita:
        Gráfico de linhas — "08 · Evolução do valor da produção"
        Eixo X: ano, 2000–2025.
        Eixo Y: valor da produção, em mil R$.
        Uma linha por cultura; oferecer seletor de culturas.
        Filtro de período pode recortar as linhas já carregadas, sem executar
        novamente o SQL. Aplicável a esta série, que contém linhas anuais.

    Largura inteira:
      Tabela com alternância de visualização:
        "01 · Município líder por cultura (2000–2025)"
          Uma linha por cultura, com município, UF e valor acumulado no período.
        "02 · Top 20 municípios produtores (2025)"
          Posição, município, valor (mil R$) e quantidade (t).
      Permitir ordenação e busca na tabela.

  ABA 2 — Distribuição por estado
    Controles no topo da aba:
      Ano: 2000 ou 2025, conforme dados da consulta 10.
      Métrica do mapa: produção (t) ou participação nacional (%).

    Faixa de três cartões:
      Estado líder no ano selecionado.
      Produção do estado líder (t).
      Participação nacional do estado líder (%).

    Duas colunas:
      Coluna esquerda:
        Mapa coroplético do Brasil — "10 · Produção agrícola por UF"
        Colorir estados pela métrica selecionada; tooltip com UF, ano,
        produção e participação.
        A consulta retorna 2000 e 2025. Não oferecer anos intermediários.
        O mapa geográfico real exige GeoJSON/contornos estaduais; se isso
        ainda não estiver disponível, usar temporariamente a grade esquemática
        do HTML e identificá-la claramente como não geográfica.

      Coluna direita:
        Barras horizontais — "10 · Estados com maior participação"
        Ordenar da maior para a menor; mostrar participação e produção.
        O seletor de ano deve atualizar mapa e barras em conjunto.

    Duas colunas:
      Barras/tabela — "10 · Comparação da produção por UF"
        Comparar 2000 e 2025 por volume ou participação.
      Tabela — "06 · Área plantada versus colhida por UF (2025)"
        UF, área plantada (ha), área colhida (ha) e diferença (ha).

    Largura inteira:
      Composição estadual — "15 · Valor por cultura e UF (2025)"
        Seletor de UF.
        Pizza/rosca com participação das sete culturas no valor estadual.
        Mostrar também valor total estadual, HHI e número efetivo de culturas.
        A consulta 15 retorna uma linha por UF × cultura; a pizza usa todas
        as culturas daquela UF, cujas participações somam 100%.
        HHI é um índice entre 0 e 1, calculado como proporções, não como
        percentuais ao quadrado.

    Largura inteira:
      Tabela — "10 · Ranking estadual por ano"
        UF, ano, posição, produção (t), participação nacional (%) e destaque.
        Permitir ordenar e filtrar por ano.

  ABA 3 — Expansão e rankings municipais
    Introdução: "Comparações de 2000 a 2025 e variação anual de 2024 a 2025."

    Faixa de três cartões:
      Maior expansão municipal de área (ha), consulta 03.
      Maior aumento municipal de produção (t), consulta 07.
      Maior aumento de rendimento agregado (%), consulta 14.

    Duas colunas:
      Coluna esquerda:
        Barras horizontais divergentes — "04 · Variação da produção por cultura"
        Uma barra por cultura, eixo centrado em zero, percentuais de 2024–2025.
        Diferenciar visualmente aumentos e quedas.

      Coluna direita:
        Filtros para tabelas/rankings:
          Cultura, quando aplicável.
          UF.
          Busca por município ou código IBGE.
        Não apresentar filtros como se recalculassem os marts.
        Filtros devem atuar sobre os resultados carregados e indicar quando
        uma seleção restringir o universo do ranking nacional.

    Duas colunas:
      Tabela — "03 · Municípios com maior expansão de área"
        Ranking, município, UF, área em 2000, área em 2025,
        crescimento em hectares e percentual.

      Tabela — "07 · Municípios com maior aumento de produção"
        Ranking, município, quantidade em 2000 e 2025 (t),
        aumento em toneladas.

    Duas colunas:
      Tabela — "14 · Maiores aumentos de rendimento agregado"
        Ranking, município, UF, rendimentos de 2000 e 2025 (kg/ha),
        aumento absoluto e percentual.
        Aviso: rendimento agregado das culturas, não rendimento de cultura
        individual.

      Tabela de alerta — "09 · Área aumentou, produção não acompanhou"
        Município, UF, aumento da área (ha) e variação da quantidade (t).
        Apresentar como lista de casos para investigação, não como diagnóstico
        de causa.

  ABA 4 — Produtividade e valor por hectare
    Introdução: distinguir rendimento físico (kg/ha) de valor bruto (R$/ha).

    Duas colunas:
      Coluna esquerda:
        Dumbbell/slope chart — "11 · Rendimento nacional por cultura"
        Um par de pontos por cultura, conectando 2000 a 2025.
        Eixo em kg/ha; ordenar pela variação percentual.
        Rótulos nos pontos com os valores absolutos e variação percentual.
        Destacar aumentos e quedas com cores distintas.
        A consulta compara apenas 2000 e 2025; não mostrar como série anual.
        Se disponível, cartões compactos para maior aumento percentual e
        maior aumento absoluto.

      Coluna direita:
        Tabela — "11 · Rendimento por cultura"
        Cultura, rendimento de 2000 e 2025 (kg/ha), aumento (kg/ha)
        e variação percentual.

    Largura inteira:
      Seletor de cultura para o ranking da consulta 13.

    Duas colunas:
      Coluna esquerda:
        Barras horizontais — "13 · Top 10 municípios por valor bruto/ha"
        Município e UF na identificação; eixo em R$/ha.
        Ordenar do maior para o menor.
        Tooltip com valor da produção, área colhida e valor bruto por hectare.
        A consulta retorna mil R$/ha; multiplicar por 1.000 apenas para
        apresentar em R$/ha.

      Coluna direita:
        Tabela — "13 · Ranking detalhado por município"
        Posição, município, UF, valor da produção (mil R$),
        área colhida (ha) e valor bruto por hectare (R$/ha).
        Aviso visível: valor bruto não é lucro e não desconta custos.
        Um filtro de UF, se oferecido, deve deixar claro que filtra a lista
        Top 10 nacional, não recalcula um ranking estadual.

  PADRÕES VISUAIS E DE IMPLEMENTAÇÃO
    Usar st.metric para os quatro indicadores nacionais.
    Usar gráficos interativos com width="stretch"; não usar use_container_width.
    Tabelas devem permitir ordenação e rolagem horizontal quando necessário.
    Mostrar unidade nos títulos/eixos e o número da consulta em cada visual.
    Não inventar ou manter valores de exemplo como se fossem resultados reais.
    Períodos aceitos dependem do grão de cada consulta:
      08: recorte de anos individuais disponíveis entre 2000 e 2025.
      10: somente 2000 e 2025.
      01, 03, 07, 09, 11 e 14: comparações/agregações definidas no SQL.
      02, 05, 06, 12, 13 e 15: ano de referência 2025.
    Portanto, não criar um único filtro global de período que prometa afetar
    todos os painéis.
4. FORMATO (painel.py), funções puras, sem streamlit e sem banco
   reais(valor, casas=2)  -> "R$ 1.003.862,14"
   pct(valor, casas=1)    -> "93,2%"
   numero(valor, casas=0) -> "96.470"
   Milhar com ponto, decimal com vírgula, sempre. Não use locale do sistema.
   Motivo: o resultado não pode depender da máquina de quem roda.
   Uma função por gráfico, recebendo o DataFrame e devolvendo a figura
   plotly. Motivo: o relatório HTML reaproveita as mesmas funções.

5. FILTROS
   OS filtros devem apenas recortar linhas do SELECT; Não recalcular nada que esteja fora do SQL.

6. CACHE E ERRO
   Leitura com st.cache_data. Um botão "Atualizar" limpa o cache.
   Sem agrodata.duckdb, ou faltando qualquer mart da lista do item 3: st.error
   dizendo quais e o comando "uv run python -m pipeline.marts", e st.stop().

CRITÉRIOS DE ACEITE
-
- O cabeçalho exibe o título "Produção agrícola brasileira" e, logo abaixo,
  o subtítulo com as sete culturas consideradas e o período de 2000 a 2025.
- As quatro abas — Panorama, Distribuição por estado, Expansão e rankings,
  Produtividade e valor/ha — abrem o conteúdo correspondente. Os quatro
  indicadores nacionais permanecem visíveis acima da navegação em todas elas.
- Os quatro cartões nacionais exibem os resultados da consulta 12, para 2025,
  na ordem: valor da produção, quantidade produzida, área colhida e rendimento
  médio. Cada número é apresentado com unidade correta; qualquer conversão de unidade
  é explícita e não altera o resultado do mart.
- A rosca da consulta 05 exibe área colhida e não colhida. As duas porcentagens
  somam 100%, admitindo apenas a diferença de arredondamento da exibição.
- A série da consulta 08 contém os anos disponíveis entre 2000 e 2025 e as
  culturas retornadas pelo SQL. O filtro de período recorta as linhas já
  carregadas dessa série; não altera os cartões de 2025 nem os resultados de
  outros marts.
- A tabela da consulta 01 apresenta uma linha por cultura, com município líder,
  UF e valor acumulado no período definido pela consulta. A visualização
  alternativa da consulta 02 apresenta no máximo 20 municípios de 2025,
  ordenados do maior para o menor valor de produção.
- O painel estadual permite selecionar somente 2000 ou 2025 para os visuais
  baseados na consulta 10. Mapa, barras e tabela refletem o mesmo ano
  selecionado. Para cada ano, as participações estaduais totalizam 100%,
  considerando arredondamento e os estados retornados pela consulta.
- O mapa distingue claramente um mapa geográfico de uma representação
  esquemática. Se forem usados contornos geográficos, cada UF apresentada
  corresponde ao estado correto; tooltips informam UF, ano, produção e
  participação.
- Os cartões de estado líder, produção e participação correspondem ao ano
  selecionado e ao maior valor retornado pela consulta 10.
- A tabela da consulta 06 apresenta área plantada, área colhida e diferença
  em hectares por UF, usando apenas o ano de 2025.
- A composição da consulta 15 mostra as culturas da UF selecionada. As
  participações percentuais somam 100% por UF, admitindo arredondamento.
  HHI é apresentado na escala de 0 a 1; número efetivo de culturas e valor
  total estadual correspondem à mesma UF.
- As barras da consulta 04 mostram as sete culturas retornadas e preservam
  os sinais das variações: valores positivos indicam aumento e negativos,
  redução entre 2024 e 2025.
- As tabelas municipais usam as unidades e os períodos definidos nos marts:
    consulta 03: no máximo 10 municípios, aumento de área em hectares;
    consulta 07: no máximo 10 municípios, aumento de quantidade em toneladas;
    consulta 14: no máximo 20 municípios, evolução de rendimento agregado;
    consulta 09: municípios cuja área aumentou e cuja produção não aumentou.
  Rankings aparecem na ordem indicada pela consulta e não são recalculados
  com base em filtros locais.
- A consulta 11 compara 2000 com 2025. O gráfico dumbbell/slope e a tabela
  exibem rendimentos em kg/ha, aumento absoluto e variação percentual;
  culturas seguem a ordenação de aumento percentual retornada pelo mart.
  O painel não apresenta essa comparação como série anual.
- A consulta 13 apresenta até 10 municípios por cultura, conforme o ranking
  retornado. O seletor de cultura filtra as linhas já carregadas; um filtro
  de UF não recalcula o ranking nacional. O indicador é rotulado como valor
  bruto por hectare, não como lucro. Se exibido em R$/ha, a conversão de
  mil R$/ha para R$/ha é aplicada uma única vez e identificada.
- Todos os gráficos e tabelas exibem título com o número do mart, unidade e
  período de referência. Os rankings podem ser ordenados e as tabelas extensas
  permitem rolagem ou paginação sem ocultar colunas relevantes.
- Nenhum valor de exemplo do rascunho — incluindo cards, participações,
  municípios ou séries — é apresentado como resultado real. Quando os dados
  de um mart não estiverem disponíveis, a tela informa a ausência em vez de
  exibir valores demonstrativos.
- Os filtros só afetam os resultados que possuem as dimensões necessárias.
  Não existe um filtro global de período que aparente modificar consultas
  agregadas ou comparações fixas em 2000/2025.
- Com o painel de pé, uv run python -m pipeline.marts a aplicação inicia sem erro,
  e cada consulta/mart necessário ao dashboard pode ser carregado sem erro de lock.
- Uma busca por "groupby", ".sum(", ".mean(" e "merge" em painel.py e
  app.py não encontra nada.

ENTREGA
1. A spec como docstring no topo de painel.py, com o motivo de cada regra.
2. O código, comentado só onde a decisão não é óbvia.
3. Uma lista final do que você assumiu e que não estava na spec.