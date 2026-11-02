"""Camada de leitura, formatação e figuras reutilizáveis pelo dashboard.

Esta docstring registra a spec de implementação e os motivos das decisões.

CONTEXTO E STACK
O dashboard apresenta os marts DuckDB construídos a partir da PAM, SIDRA 5457,
e da tabela municipal do GOV.BR. O projeto usa Python, uv, DuckDB, Streamlit e
Plotly. A camada de tela não substitui nem altera as regras de negócio SQL.

LEITURA
ler(marts) devolve um dicionário de nome do mart para DataFrame. Para cada nome,
executa somente SELECT * FROM marts.<nome>. A conexão usa
duckdb.connect("agrodata.duckdb", read_only=True) e é aberta/fechada dentro
da função. Isso libera o arquivo para que pipeline.marts possa gravar enquanto
o painel está aberto.

REGRAS DE DADOS
Não agregar, combinar, pivotar ou calcular valores derivados em painel.py ou
app.py. São permitidos filtros de linhas, ordenação, head(n), renomear colunas
e formatar valores para exibição. Uma métrica nova exige um mart SQL novo.
O motivo é preservar o SQL como única fonte das regras e evitar que a interface
apresente indicadores calculados de modo diferente.

FORMATADORES
reais(valor, casas=2), pct(valor, casas=1) e numero(valor, casas=0) são funções
puras, independentes do locale do sistema. Milhares usam ponto e decimais usam
vírgula, pois a mesma apresentação precisa ocorrer em qualquer máquina.

GRÁFICOS
Há uma função por gráfico; cada função recebe DataFrame(s) já materializado(s)
e retorna uma figura Plotly, sem importar Streamlit. O motivo é permitir que o
relatório HTML e outros consumidores reutilizem as figuras.

FONTES E MÁRTS
Os nomes consultados são:
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
ranking_municipios_evolucao_rendimento_agregado_2000_2025 e
concentracao_valor_producao_por_cultura_estado_2025.
Se o banco ou qualquer mart faltar, a página deve informar os nomes e orientar
uv run python -m pipeline.marts; não fabricar valores de demonstração.

LAYOUT E REGRAS DA PÁGINA
app.py configura layout wide, cabeçalho com título, subtítulo das sete culturas,
fonte PAM/SIDRA 5457 e aviso de estado dos dados. Quatro métricas nacionais
de 2025 (valor em mil R$, quantidade em toneladas, área colhida em hectares e
rendimento em kg/ha) ficam antes das quatro abas e são independentes dos filtros.

Aba Panorama:
05 apresenta área colhida e não colhida em rosca, com percentuais que somam
100%. 08 apresenta série anual de valor (mil R$) por cultura, com filtro de
culturas e recorte de período somente sobre as linhas já carregadas. 01 apresenta
o líder municipal de cada cultura no período do mart; 02 apresenta até vinte
municípios em 2025, com ordenação e busca.

Aba Distribuição por estado:
10 oferece somente 2000 ou 2025, sincronizando mapa, barras e tabela. Os cartões
identificam estado líder, volume e participação. O mapa usa os limites estaduais
do IBGE incluídos em data/brasil_ufs.geojson.
06 exibe área plantada, área colhida e diferença por UF em 2025. 15 mostra a
composição das sete culturas da UF selecionada, participação, valor estadual,
HHI entre 0 e 1 e número efetivo de culturas.

Aba Expansão e rankings:
03, 07 e 14 abastecem cartões e rankings municipais; 04 mostra a variação
percentual por cultura entre 2024 e 2025, preservando sinais; 09 lista casos
em que área aumentou sem aumento de produção. Filtros só recortam resultados
carregados e devem indicar quando reduzem o universo de um ranking nacional.

Aba Produtividade e valor por hectare:
11 compara rendimento físico em kg/ha somente entre 2000 e 2025 e mantém a
ordem do mart. 13 exibe o Top 10 municipal por cultura em 2025. Sua unidade
materializada é mil R$/ha; multiplicar por 1.000 é permitido somente para
exibição em R$/ha. Valor bruto não é lucro nem desconta custos.

Filtros nunca prometem afetar resultados sem a dimensão/anos correspondentes:
08 aceita recorte de anos entre 2000 e 2025; 10 somente 2000 ou 2025; 01, 03,
07, 09, 11 e 14 conservam as comparações/agregações do SQL; 02, 05, 06, 12,
13 e 15 são referentes a 2025. Isso evita um filtro global enganoso.

CACHE E ERROS
app.py aplica st.cache_data à chamada de ler. O botão Atualizar limpa o cache,
para que uma nova leitura veja a materialização mais recente. Banco ausente,
marts ausentes ou erro de leitura devem ser mostrados com st.error e interromper
a página com st.stop; não esconder falhas nem recorrer a dados de exemplo.

CRITÉRIOS DE ACEITE
O cabeçalho e as quatro abas correspondem ao texto e conteúdo acima, e as quatro
métricas ficam acima de todas as abas. Todos os gráficos e tabelas identificam
número do mart, período e unidade. Totais e rankings vêm diretamente dos marts;
as participações 05 e 15 respeitam 100% dentro do respectivo universo. O painel
estadual usa somente os anos disponíveis. 11 não é apresentado como série
anual. 13 explicita a conversão de unidade e que o valor bruto não é lucro.
Tabelas permitem ordenação; tabelas municipais e estaduais permitem busca ou
filtro. Dados ausentes são informados, nunca substituídos por exemplos.
Com app.py em execução, uv run python -m pipeline.marts pode atualizar os marts
sem erro de lock, pois ler fecha a conexão. app.py e painel.py não executam
operações de agregação, combinações de colunas ou leitura de dados fora dos
SELECT * definidos.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

MARTS: tuple[str, ...] = (
    "ranking_valor_da_producao_muncipio_por_cultura",
    "20_municipios_maiores_produtores_em_2025",
    "municipios_maior_expansao_area_plantada",
    "variacao_percentual_quantidade_produzida_por_cultura_2024_2025",
    "percentual_area_plantada_colhida_em_2025",
    "diferenca_area_plantada_colhida_por_estado_2025",
    "municipios_maior_aumento_quantidade_produzida_2000_2025",
    "evolucao_valor_producao_por_cultura_2000_2025",
    "expansao_area_sem_aumento_producao_2000_2025",
    "distribuicao_geografica_producao_por_estado_2000_2025",
    "ranking_aumento_rendimento_medio_por_cultura_2000_2025",
    "resumo_totais_2025",
    "ranking_valor_bruto_por_hectare_cultura_2025",
    "ranking_municipios_evolucao_rendimento_agregado_2000_2025",
    "concentracao_valor_producao_por_cultura_estado_2025",
)

CULTURAS: tuple[str, ...] = (
    "Arroz (em casca)",
    "Algodão herbáceo (em caroço)",
    "Café (em grão) Total",
    "Feijão (em grão)",
    "Milho (em grão)",
    "Soja (em grão)",
    "Trigo (em grão)",
)

GEOJSON_UFS = json.loads(
    (Path(__file__).parent / "data" / "brasil_ufs.geojson").read_text(
        encoding="utf-8"
    )
)
# Plotly's spherical projection expects GeoJSON exterior rings clockwise.
for feature in GEOJSON_UFS["features"]:
    geometry = feature["geometry"]
    polygons = (
        geometry["coordinates"]
        if geometry["type"] == "MultiPolygon"
        else [geometry["coordinates"]]
    )
    for polygon in polygons:
        for ring in polygon:
            ring.reverse()

UFS = tuple(
    feature["properties"]["uf"] for feature in GEOJSON_UFS["features"]
)


class ErroLeituraMarts(RuntimeError):
    """Falha explícita ao abrir o banco ou carregar os marts solicitados."""


def ler(marts: Sequence[str] = MARTS) -> dict[str, pd.DataFrame]:
    """Carrega cada mart com um SELECT * e fecha sempre a conexão."""
    caminho_banco = Path("agrodata.duckdb")
    if not caminho_banco.is_file():
        raise ErroLeituraMarts(
            "Banco agrodata.duckdb não encontrado. "
            "Execute `uv run python -m pipeline.marts` após preparar os dados."
        )

    try:
        conexao = duckdb.connect("agrodata.duckdb", read_only=True)
    except duckdb.Error as erro:
        raise ErroLeituraMarts(
            f"Não foi possível abrir agrodata.duckdb em modo somente leitura: {erro}"
        ) from erro

    dados: dict[str, pd.DataFrame] = {}
    ausentes: list[str] = []
    try:
        for nome in marts:
            identificador = '"' + nome.replace('"', '""') + '"'
            try:
                dados[nome] = conexao.execute(
                    f"SELECT * FROM marts.{identificador}"
                ).df()
            except duckdb.Error:
                ausentes.append(nome)
    finally:
        conexao.close()

    if ausentes:
        nomes = ", ".join(f"marts.{nome}" for nome in ausentes)
        raise ErroLeituraMarts(
            f"Marts ausentes ou indisponíveis: {nomes}. "
            "Execute `uv run python -m pipeline.marts`."
        )
    return dados


def _formatar(valor: object, casas: int) -> str:
    if pd.isna(valor):
        return "—"
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "\0").replace(".", ",").replace("\0", ".")


def reais(valor: object, casas: int = 2) -> str:
    return f"R$ {_formatar(valor, casas)}"


def pct(valor: object, casas: int = 1) -> str:
    return f"{_formatar(valor, casas)}%"


def numero(valor: object, casas: int = 0) -> str:
    return _formatar(valor, casas)


def _layout(figura: go.Figure, altura: int = 390) -> go.Figure:
    figura.update_layout(
        template="plotly_white",
        height=altura,
        margin={"l": 12, "r": 12, "t": 34, "b": 12},
        legend_title_text="",
        font={"family": "sans-serif", "size": 12, "color": "#435148"},
    )
    return figura


def grafico_area_colhida(df: pd.DataFrame) -> go.Figure:
    linha = df.iloc[0]
    figura = go.Figure(
        go.Pie(
            labels=["Área colhida", "Não colhida"],
            values=[
                linha["percentual_area_plantada_colhida"],
                linha["percentual_area_plantada_nao_colhida"],
            ],
            hole=0.62,
            sort=False,
            texttemplate="%{label}<br>%{value:.1f}%",
            hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
            marker={"colors": ["#23734d", "#e8c879"]},
        )
    )
    figura.update_layout(showlegend=False)
    return _layout(figura, 330)


def grafico_evolucao_valor(df: pd.DataFrame) -> go.Figure:
    figura = px.line(
        df.sort_values(["ano", "cultura"]),
        x="ano",
        y="valor_producao_mil_reais",
        color="cultura",
        markers=True,
        labels={
            "ano": "Ano",
            "valor_producao_mil_reais": "Valor da produção (mil R$)",
            "cultura": "Cultura",
        },
    )
    figura.update_xaxes(dtick=2)
    figura.update_yaxes(tickformat=",.0f")
    return _layout(figura, 390)


def grafico_mapa_estados(df: pd.DataFrame, ano: int) -> go.Figure:
    selecionados = df.loc[df["ano"].eq(ano)]
    dados_mapa = selecionados.set_index("uf").reindex(UFS)
    customdata = dados_mapa[
        [
            "quantidade_produzida_toneladas",
            "participacao_nacional_percentual",
        ]
    ].to_numpy()

    figura = go.Figure(
        go.Choropleth(
            geojson=GEOJSON_UFS,
            featureidkey="properties.uf",
            locations=UFS,
            z=dados_mapa["quantidade_produzida_toneladas"],
            customdata=customdata,
            colorscale=[
                [0, "#c8ece6"],
                [0.35, "#81c9c4"],
                [0.7, "#428e9f"],
                [1, "#234f70"],
            ],
            showscale=True,
            colorbar={
                "title": {"text": "Produção (t)", "side": "top"},
                "thickness": 14,
                "len": 0.72,
                "outlinewidth": 0,
                "tickformat": ",.0f",
                "tickfont": {"color": "#748178"},
            },
            marker_line_color="white",
            marker_line_width=1.1,
            hovertemplate=(
                "<b>%{location}</b><br>"
                f"Ano: {ano}<br>"
                "Produção: %{customdata[0]:,.0f} t<br>"
                "Participação: %{customdata[1]:.2f}%<extra></extra>"
            ),
        )
    )
    figura.update_geos(
        fitbounds="geojson",
        visible=False,
        projection_type="mercator",
        domain={"x": [0.02, 0.82], "y": [0.03, 0.97]},
        showcoastlines=False,
        showframe=False,
        showland=False,
        showlakes=False,
        showrivers=False,
        showcountries=False,
    )
    figura.update_traces(
        hoverlabel={"bgcolor": "#193d2d", "font": {"color": "white"}}
    )
    figura.update_layout(
        showlegend=False,
        margin={"l": 0, "r": 8, "t": 22, "b": 0},
    )
    return _layout(figura, 450)


def grafico_participacao_estados(df: pd.DataFrame) -> go.Figure:
    ordenado = df.sort_values("participacao_nacional_percentual", ascending=False)
    figura = px.bar(
        ordenado,
        x="participacao_nacional_percentual",
        y="uf",
        orientation="h",
        hover_data={"quantidade_produzida_toneladas": ":,.0f"},
        labels={
            "participacao_nacional_percentual": "Participação nacional (%)",
            "uf": "UF",
            "quantidade_produzida_toneladas": "Produção (t)",
        },
        color_discrete_sequence=["#4a9367"],
    )
    figura.update_yaxes(
        categoryorder="array",
        categoryarray=ordenado["uf"].tolist(),
        autorange="reversed",
    )
    figura.update_xaxes(ticksuffix="%")
    return _layout(figura, 520)


def grafico_comparacao_estados(df: pd.DataFrame, metrica: str) -> go.Figure:
    colunas = {
        "Produção (t)": "quantidade_produzida_toneladas",
        "Participação (%)": "participacao_nacional_percentual",
    }
    coluna_valor = colunas[metrica]
    figura = px.bar(
        df.sort_values(["uf", "ano"]),
        x="uf",
        y=coluna_valor,
        color="ano",
        barmode="group",
        labels={
            "uf": "UF",
            "ano": "Ano",
            coluna_valor: metrica,
        },
        color_discrete_sequence=["#b7d77a", "#23734d"],
    )
    return _layout(figura, 390)


def grafico_area_por_estado(df: pd.DataFrame) -> go.Figure:
    ordenado = df.sort_values(
        "diferenca_area_plantada_colhida_hectares", ascending=False
    )
    figura = go.Figure()
    figura.add_trace(
        go.Bar(
            name="Plantada",
            y=ordenado["uf"],
            x=ordenado["area_plantada_total_hectares"],
            orientation="h",
            marker_color="#b7d77a",
        )
    )
    figura.add_trace(
        go.Bar(
            name="Colhida",
            y=ordenado["uf"],
            x=ordenado["area_colhida_total_hectares"],
            orientation="h",
            marker_color="#23734d",
        )
    )
    figura.update_layout(barmode="group")
    figura.update_yaxes(autorange="reversed")
    figura.update_xaxes(title_text="Área (ha)")
    return _layout(figura, 560)


def grafico_composicao_cultura(df: pd.DataFrame, uf: str) -> go.Figure:
    selecionado = df.loc[df["uf"].eq(uf)].sort_values("ranking_no_estado")
    figura = go.Figure(
        go.Pie(
            labels=selecionado["cultura"],
            values=selecionado["participacao_valor_estado_percentual"],
            hole=0.58,
            sort=False,
            texttemplate="%{label}<br>%{value:.1f}%",
            hovertemplate="%{label}: %{value:.2f}%<extra></extra>",
            marker={"colors": px.colors.qualitative.Safe},
        )
    )
    figura.update_layout(showlegend=False)
    return _layout(figura, 370)


def grafico_variacao_producao(df: pd.DataFrame) -> go.Figure:
    figura = go.Figure()
    aumentos = df.loc[df["variacao_percentual"].ge(0)]
    reducoes = df.loc[df["variacao_percentual"].lt(0)]
    for dados, nome, cor in (
        (aumentos, "Aumento", "#23734d"),
        (reducoes, "Redução", "#c65a4a"),
    ):
        figura.add_trace(
            go.Bar(
                name=nome,
                x=dados["variacao_percentual"],
                y=dados["cultura"],
                orientation="h",
                marker_color=cor,
                text=[pct(valor, 1) for valor in dados["variacao_percentual"]],
                textposition="outside",
                hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
            )
        )
    figura.add_vline(x=0, line_color="#758178", line_width=1)
    figura.update_layout(barmode="overlay")
    figura.update_xaxes(
        title_text="Variação da quantidade produzida (%)", ticksuffix="%"
    )
    figura.update_yaxes(title_text="Cultura", autorange="reversed")
    return _layout(figura, 370)


def grafico_rendimento_culturas(df: pd.DataFrame) -> go.Figure:
    ordenado = df.sort_values("ranking_aumento")
    positivos = ordenado.loc[ordenado["aumento_rendimento_kg_por_hectare"].ge(0)]
    negativos = ordenado.loc[ordenado["aumento_rendimento_kg_por_hectare"].lt(0)]
    figura = go.Figure()

    for dados, nome, cor in (
        (positivos, "Aumento", "#23734d"),
        (negativos, "Queda", "#c65a4a"),
    ):
        x_linhas: list[float | None] = []
        y_linhas: list[str | None] = []
        for linha in dados.itertuples(index=False):
            x_linhas.extend(
                [
                    linha.rendimento_2000_kg_por_hectare,
                    linha.rendimento_2025_kg_por_hectare,
                    None,
                ]
            )
            y_linhas.extend([linha.cultura, linha.cultura, None])
        figura.add_trace(
            go.Scatter(
                x=x_linhas,
                y=y_linhas,
                mode="lines",
                line={"color": cor, "width": 2},
                name=nome,
                hoverinfo="skip",
            )
        )

    for coluna, ano, cor, posicao in (
        ("rendimento_2000_kg_por_hectare", "2000", "#9aa79d", "middle left"),
        ("rendimento_2025_kg_por_hectare", "2025", "#23734d", "middle right"),
    ):
        figura.add_trace(
            go.Scatter(
                x=ordenado[coluna],
                y=ordenado["cultura"],
                mode="markers+text",
                text=[numero(valor, 0) for valor in ordenado[coluna]],
                textposition=posicao,
                customdata=ordenado[
                    ["aumento_rendimento_kg_por_hectare", "aumento_percentual"]
                ],
                marker={"color": cor, "size": 9},
                name=ano,
                hovertemplate=(
                    "%{y} · " + ano + ": %{x:,.0f} kg/ha<br>"
                    "Aumento: %{customdata[0]:,.0f} kg/ha<br>"
                    "Variação: %{customdata[1]:.2f}%<extra></extra>"
                ),
            )
        )

    figura.update_yaxes(
        categoryorder="array",
        categoryarray=ordenado["cultura"].tolist(),
        autorange="reversed",
    )
    figura.update_xaxes(title_text="Rendimento médio (kg/ha)")
    return _layout(figura, 440)


def grafico_valor_bruto_hectare(df: pd.DataFrame) -> go.Figure:
    ordenado = df.sort_values("ranking_na_cultura")
    valores_reais = [
        valor * 1000 for valor in ordenado["valor_bruto_por_hectare_mil_reais"]
    ]
    customdata = list(
        zip(
            ordenado["uf"],
            ordenado["valor_producao_mil_reais"],
            ordenado["area_colhida_hectares"],
            strict=True,
        )
    )
    figura = go.Figure(
        go.Bar(
            x=valores_reais,
            y=ordenado["municipio"],
            orientation="h",
            customdata=customdata,
            marker_color="#4a9367",
            hovertemplate=(
                "%{y} · %{customdata[0]}<br>"
                "Valor bruto: R$ %{x:,.0f}/ha<br>"
                "Valor da produção: %{customdata[1]:,.0f} mil R$<br>"
                "Área colhida: %{customdata[2]:,.0f} ha<extra></extra>"
            ),
        )
    )
    figura.update_yaxes(autorange="reversed", title_text="Município")
    figura.update_xaxes(title_text="Valor bruto da produção (R$/ha)", tickprefix="R$ ")
    return _layout(figura, 440)
