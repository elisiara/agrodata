"""Aplicação Streamlit para exploração dos marts agrícolas."""

from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

import painel
from dashboard import validar_marts

st.set_page_config(
    page_title="Produção agrícola brasileira | AgroData",
    page_icon="🌱",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --agro-ink: #1d3028;
        --agro-muted: #5e6f65;
        --agro-line: #e2e8e3;
        --agro-paper: #f4f6f3;
        --agro-green: #23734d;
        --agro-green-dark: #193d2d;
        --agro-green-soft: #e7f2e9;
        --agro-slate: #526056;
        --agro-sage: #b5c7b8;
    }

    [data-testid="stAppViewContainer"] {
        background: var(--agro-paper);
        color: var(--agro-ink);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1540px;
        padding: 2rem clamp(1rem, 3vw, 2.75rem) 3rem;
    }

    h1, h2, h3, [data-testid="stMarkdownContainer"] strong {
        color: var(--agro-ink);
    }

    h1 {
        font-size: clamp(1.8rem, 2.4vw, 2.3rem);
        font-weight: 750;
        letter-spacing: -0.045em;
    }

    h2, h3 {
        letter-spacing: -0.025em;
    }

    .agro-eyebrow {
        margin-bottom: -0.55rem;
        color: var(--agro-green);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .agro-card-note {
        padding: 0.85rem 1.15rem;
        border: 1px solid var(--agro-line);
        border-left: 4px solid var(--agro-green);
        border-radius: 10px;
        background: #ffffff;
        margin: 0.5rem 0 0.9rem;
        font-size: 0.86rem;
        color: var(--agro-ink);
        line-height: 1.55;
        box-shadow: 0 4px 14px rgba(25, 61, 45, 0.04);
    }

    .agro-card-note strong {
        color: var(--agro-green-dark);
        font-weight: 700;
    }

    .agro-card-note p {
        margin: 0.3rem 0 0;
        color: #3f5047;
    }

    .agro-badge-info {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        background: var(--agro-green-soft);
        color: var(--agro-green-dark);
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }

    [data-testid="stCaptionContainer"] {
        color: var(--agro-muted);
    }

    [data-testid="stMetric"] {
        min-height: 118px;
        padding: 1rem 1.15rem;
        border: 1px solid var(--agro-line);
        border-top: 3px solid var(--agro-green);
        border-radius: 14px;
        background: #fff;
        box-shadow: 0 8px 24px #203b2b0a;
    }

    [data-testid="stMetricLabel"] {
        color: var(--agro-muted);
        font-size: 0.8rem;
        font-weight: 650;
    }

    [data-testid="stMetricValue"] {
        color: var(--agro-ink);
        font-size: clamp(1.25rem, 1.8vw, 1.75rem);
        font-weight: 760;
        letter-spacing: -0.04em;
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 0.5rem;
        padding: 0.45rem;
        border: 1px solid var(--agro-line);
        border-radius: 16px;
        background: #fff;
    }

    [data-testid="stTabs"] button[role="tab"] {
        min-height: 2.65rem;
        padding: 0.6rem 1.1rem;
        border: 1px solid transparent;
        border-radius: 12px;
        color: var(--agro-green-dark);
        font-weight: 700;
        transition: color 120ms ease, background 120ms ease, box-shadow 120ms ease;
    }

    [data-testid="stTabs"] button[role="tab"]:hover:not([aria-selected="true"]) {
        color: var(--agro-green-dark);
        background: var(--agro-green-soft);
    }

    [data-testid="stTabs"] [role="tab"][aria-selected="true"],
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
    [data-testid="stTabs"] [data-selected="true"] {
        padding: 5px;
        border-radius: 5px;
        color: #fff !important;
        background: var(--agro-green-dark) !important;
        border-color: var(--agro-green-dark) !important;
        box-shadow: none !important;
    }

    [data-testid="stTabs"] .st-emotion-cache-qksclw[data-hovered] {
        color: rgb(63 202 136) !important;
    }

    [data-testid="stTabs"] .react-aria-SelectionIndicator {
        background-color: var(--agro-green-dark) !important;
        border-color: var(--agro-green-dark) !important;
        border-radius: 999px;
    }

    [data-testid="stTabs"] [role="tab"][aria-selected="true"] *,
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] *,
    [data-testid="stTabs"] [data-selected="true"] * {
        color: #fff !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab-highlight"],
    [data-testid="stTabs"] [data-baseweb="tab-border"] {
        background-color: var(--agro-green-dark) !important;
        border-color: var(--agro-green-dark) !important;
    }

    [data-testid="stTabs"] [role="tab"][aria-selected="true"]::after,
    [data-testid="stTabs"] [data-selected="true"]::after {
        background-color: var(--agro-green-dark) !important;
        border-color: var(--agro-green-dark) !important;
    }

    [data-testid="stTabs"] [data-testid="stTabContent"] {
        padding-top: 1.15rem;
    }

    [data-testid="stPlotlyChart"] {
        overflow: hidden;
        border: 1px solid var(--agro-line);
        border-radius: 14px;
        background: #fff;
        box-shadow: 0 8px 24px #203b2b08;
    }

    [data-testid="stDataFrame"] {
        overflow: hidden;
        border: 1px solid var(--agro-line);
        border-radius: 12px;
        background: #fff;
    }

    [data-testid="stTextInput"] input,
    [data-baseweb="select"] > div {
        border-color: #dce4dc;
        border-radius: 9px;
        background: #fff;
    }

    [data-testid="stButton"] button {
        min-height: 2.55rem;
        border: 1px solid var(--agro-green);
        border-radius: 9px;
        color: #fff;
        background: var(--agro-green);
        font-weight: 700;
        transition: background 120ms ease, border-color 120ms ease;
    }

    [data-testid="stButton"] button:hover {
        border-color: var(--agro-green-dark);
        color: #fff;
        background: var(--agro-green-dark);
    }

    [data-testid="stAlert"] {
        border: 1px solid var(--agro-line) !important;
        border-left: 4px solid var(--agro-green) !important;
        background: #ffffff !important;
        color: var(--agro-ink) !important;
        border-radius: 11px !important;
        box-shadow: 0 4px 14px rgba(25, 61, 45, 0.04) !important;
    }

    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
        color: var(--agro-ink) !important;
    }

    @media (max-width: 760px) {
        [data-testid="stMainBlockContainer"] {
            padding-top: 1.25rem;
        }

        [data-testid="stMetric"] {
            min-height: 104px;
            padding: 0.8rem;
        }

        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            overflow-x: auto;
        }

        [data-testid="stTabs"] button[role="tab"] {
            padding-inline: 0.75rem;
            white-space: nowrap;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(show_spinner="Carregando resultados dos marts...")
def carregar_marts() -> dict[str, pd.DataFrame]:
    return painel.ler(painel.MARTS)


def tabela(
    dados: pd.DataFrame,
    nomes: dict[str, str] | None = None,
    *,
    altura: int | None = 420,
) -> None:
    st.dataframe(
        dados.rename(columns=nomes or {}),
        hide_index=True,
        width="stretch",
        height=altura,
    )


def filtrar_busca(
    dados: pd.DataFrame,
    termo: str,
    colunas: tuple[str, ...],
) -> pd.DataFrame:
    if not termo.strip():
        return dados
    mascara = pd.Series(False, index=dados.index)
    for coluna in colunas:
        if coluna in dados.columns:
            mascara |= (
                dados[coluna]
                .astype("string")
                .str.contains(termo.strip(), case=False, regex=False, na=False)
            )
    return dados.loc[mascara]


def filtrar_municipios(dados: pd.DataFrame, uf: str, busca: str) -> pd.DataFrame:
    filtrados = dados
    if uf != "Todas" and "uf" in filtrados.columns:
        filtrados = filtrados.loc[filtrados["uf"].eq(uf)]
    return filtrar_busca(filtrados, busca, ("municipio", "codigo_municipio_ibge"))


def mostrar_erro_marts(mensagem: str) -> None:
    st.error(mensagem)
    st.stop()


cabecalho, acao = st.columns([8, 1])
with cabecalho:
    st.markdown(
        '<div class="agro-eyebrow">Painel de inteligência agrícola</div>',
        unsafe_allow_html=True,
    )
    st.title("🌱 AgroData: Produção agrícola brasileira")
    st.caption(
        "Culturas consideradas: Arroz, Algodão, Café, Feijão, Milho, Soja e "
        "Trigo. Período: 2000 a 2025."
    )
    st.caption("Fonte: PAM · IBGE SIDRA 5457")
with acao:
    st.write("")
    st.write("")
    if st.button("↻ Atualizar", help="Limpar o cache e recarregar os marts"):
        st.cache_data.clear()
        st.rerun()

try:
    marts = carregar_marts()
except painel.ErroLeituraMarts as erro:
    mostrar_erro_marts(f"{erro} O dashboard não usa dados demonstrativos.")

incompatibilidades = validar_marts(marts)
if incompatibilidades:
    mostrar_erro_marts(
        "Os marts estão ausentes, vazios ou incompatíveis com o dashboard: "
        + "; ".join(incompatibilidades)
        + ". Execute `uv run python -m pipeline.marts`."
    )

st.markdown(
    '<div class="agro-card-note">'
    "<strong>Macroindicadores Nacionais Consolidados (Safra 2025):</strong> "
    "Visão macroeconômica e agregada da agricultura brasileira abrangendo as 7 culturas monitoradas pela PAM "
    "(Arroz, Algodão, Café, Feijão, Milho, Soja e Trigo). "
    "O rendimento médio nacional reflete a razão ponderada de colheita: <em>Volume Físico Total (t) ÷ Área Colhida Total (ha)</em>."
    "</div>",
    unsafe_allow_html=True,
)
resumo = marts["resumo_totais_2025"].iloc[0]
metricas = st.columns(4)
metricas[0].metric(
    "Valor da produção (bi R$)",
    f"{painel.reais(resumo['valor_producao_bilhoes_reais'])} bi",
    help="Faturamento bruto estimado das 7 culturas agrícolas em 2025.",
)
metricas[1].metric(
    "Quantidade produzida (mi t)",
    f"{painel.numero(resumo['volume_milhoes_toneladas'])} mi t",
    help="Volume físico total de grãos e fibras colhidos no país em 2025.",
)
metricas[2].metric(
    "Área colhida (mi ha)",
    f"{painel.numero(resumo['area_milhoes_hectares'])} mi ha",
    help="Extensão de solo efetivamente colhida em 2025.",
)
metricas[3].metric(
    "Rendimento médio (t/ha)",
    f"{painel.numero(resumo['rendimento_toneladas_por_hectare'])} t/ha",
    help="Produtividade física agregada ponderada (convertida de kg/ha para t/ha).",
)

aba_panorama, aba_estados, aba_municipios, aba_produtividade = st.tabs(
    [
        "Panorama",
        "Distribuição por estado",
        "Expansão e rankings",
        "Produtividade e valor/ha",
    ]
)

with aba_panorama:
    st.subheader("Panorama da produção agrícola")
    st.caption("Indicadores nacionais de 2025 e evolução das culturas PAM.")
    esquerda, direita = st.columns(2)

    with esquerda:
        st.markdown(
            '<div class="agro-badge-info">Mart 05 · Balanço de Uso do Solo</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**05 · Área plantada: colhida × não colhida**")
        st.caption("Brasil · 2025 · participação percentual")
        st.markdown(
            '<div class="agro-card-note">'
            "<strong>O que esta métrica entrega:</strong> Avalia o índice de efetivação da safra em 2025. "
            "A área colhida (verde) representa o solo que completou o ciclo produtivo; "
            "a área não colhida (sálvia) representa a parcela da área plantada que não consta como colhida. "
            "Essa diferença não comprova perda nem permite atribuir sua causa; fatores climáticos, pragas e "
            "decisões econômicas são hipóteses que exigem dados adicionais."
            "</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            painel.grafico_area_colhida(
                marts["percentual_area_plantada_colhida_em_2025"]
            ),
            width="stretch",
        )

    with direita:
        st.markdown(
            '<div class="agro-badge-info">Mart 08 · Séries Temporais de Receita</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**08 · Evolução do valor da produção**")
        st.caption("Brasil · 2000–2025 · mil R$")
        st.markdown(
            '<div class="agro-card-note">'
            "<strong>O que esta série entrega:</strong> Histórico nominal de receitas brutas (em mil R$) geradas por cada cultura. "
            "Evidencia o ciclo de valorização de commodities agrícolas a partir de 2018–2020 impulsionado por demanda global "
            "e câmbio, destacando a preponderância de Soja e Milho na balança comercial."
            "</div>",
            unsafe_allow_html=True,
        )
        anos = st.slider(
            "Recortar período da série",
            min_value=2000,
            max_value=2025,
            value=(2000, 2025),
            key="periodo_evolucao",
        )
        culturas = st.multiselect(
            "Culturas da série",
            options=painel.CULTURAS,
            default=list(painel.CULTURAS),
            key="culturas_evolucao",
        )
        evolucao = marts["evolucao_valor_producao_por_cultura_2000_2025"]
        evolucao = evolucao.loc[
            evolucao["ano"].between(anos[0], anos[1])
            & evolucao["cultura"].isin(culturas)
        ]
        st.plotly_chart(
            painel.grafico_evolucao_valor(evolucao),
            width="stretch",
        )
        st.caption("O recorte afeta somente esta série; os cartões continuam em 2025.")

    st.markdown("**Municípios em destaque**")
    visualizacao = st.radio(
        "Visualização do ranking",
        ["Líder por cultura · 2000–2025", "Top 20 · 2025"],
        horizontal=True,
        label_visibility="collapsed",
        key="ranking_panorama",
    )
    if visualizacao.startswith("Líder"):
        st.markdown(
            '<div class="agro-badge-info">Mart 01 · Polos Históricos por Cultura</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="agro-card-note">'
            "<strong>O que esta tabela entrega (Mart 01):</strong> Mapeia para cada uma das 7 culturas o município que acumulou "
            "o maior valor financeiro de produção ao longo de 26 safras (2000 a 2025). "
            "<em>Nota analítica:</em> Os valores refletem a soma nominal histórica acumulada, evidenciando polos consolidados "
            "(como Sorriso/MT na soja, Rio Verde/GO no milho e Patrocínio/MG no café)."
            "</div>",
            unsafe_allow_html=True,
        )
        ranking = marts["ranking_valor_da_producao_muncipio_por_cultura"]
        termo = st.text_input("Buscar cultura ou município", key="busca_lideres")
        ranking = filtrar_busca(ranking, termo, ("cultura", "municipio", "uf"))
        tabela(
            ranking,
            {
                "cultura": "Cultura",
                "municipio": "Município líder",
                "uf": "UF",
                "valor_total_producao_mil_reais": "Valor total acumulado (mil R$)",
            },
        )
    else:
        st.markdown(
            '<div class="agro-badge-info">Mart 02 · Capitais Agrícolas Nacionais</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="agro-card-note">'
            "<strong>O que esta tabela entrega (Mart 02):</strong> Ranking dos 20 municípios com maior receita agrícola bruta na safra 2025, "
            "integrando as 7 culturas monitoradas. Correlaciona o faturamento total em mil R$ com a produção física colhida em toneladas, "
            "evidenciando os polos municipais de alta intensidade tecnológica."
            "</div>",
            unsafe_allow_html=True,
        )
        ranking = marts["20_municipios_maiores_produtores_em_2025"]
        termo = st.text_input("Buscar município", key="busca_top20")
        ranking = filtrar_busca(ranking, termo, ("municipio",))
        tabela(
            ranking.sort_values("ranking").head(20),
            {
                "ranking": "Posição",
                "municipio": "Município",
                "valor_total_producao_mil_reais": "Valor safra 2025 (mil R$)",
                "quantidade_total_toneladas": "Quantidade colhida (t)",
            },
        )

with aba_estados:
    st.subheader("Distribuição geográfica por estado")
    st.caption("Compare produção e participação estadual nos anos disponíveis.")
    distribuicao = marts["distribuicao_geografica_producao_por_estado_2000_2025"]
    anos_estado = painel.anos_disponiveis(distribuicao)
    if not anos_estado:
        mostrar_erro_marts("A consulta 10 não retornou anos disponíveis.")
    ano_estado = st.selectbox(
        "Ano",
        options=anos_estado,
        index=len(anos_estado) - 1,
        key="ano_estados",
    )
    dados_ano = distribuicao.loc[distribuicao["ano"].eq(ano_estado)]
    if dados_ano.empty:
        mostrar_erro_marts(
            f"A consulta 10 não retornou registros para o ano {ano_estado}."
        )
    lider = dados_ano.sort_values("ranking_no_ano").head(1).iloc[0]
    uf_lider_html = escape(str(lider["uf"]), quote=True)

    st.markdown(
        '<div class="agro-card-note">'
        f"<strong>Destaque Estadual na Safra {ano_estado}:</strong> "
        f"A unidade federativa de maior relevância produtiva no ano de referência foi <strong>{uf_lider_html}</strong>, "
        f"responsável por {painel.numero(lider['quantidade_produzida_toneladas'])} toneladas "
        f"({painel.pct(lider['participacao_nacional_percentual'], 2)} de todo o volume nacional das 7 culturas)."
        "</div>",
        unsafe_allow_html=True,
    )

    cards_uf = st.columns(3)
    cards_uf[0].metric(
        "Estado líder",
        lider["uf"],
        help=f"Unidade Federativa em primeiro lugar no ranking de volume em {ano_estado}.",
    )
    cards_uf[1].metric(
        "Produção do estado líder (t)",
        f"{painel.numero(lider['quantidade_produzida_toneladas'])} t",
        help="Volume total colhido no estado líder somando as 7 culturas.",
    )
    cards_uf[2].metric(
        "Participação nacional",
        painel.pct(lider["participacao_nacional_percentual"], 2),
        help="Fração da produção nacional originada no estado líder.",
    )

    mapa_coluna, participacao_coluna = st.columns([1.25, 0.75])
    with mapa_coluna:
        st.markdown(
            '<div class="agro-badge-info">Mart 10 · Geografia da Safra</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**10 · Produção agrícola por UF**")
        st.caption(
            "Cada estado é colorido pelo volume produzido; passe o cursor "
            "para ver produção e participação nacional."
        )
        st.markdown(
            '<div class="agro-card-note">'
            "<strong>O que este mapa entrega:</strong> Densidade territorial da produção sobre contornos oficiais do IBGE. "
            "Tons mais escuros de verde representam maior tonelagem física colhida, "
            "ressaltando a concentração no Centro-Oeste e nos polos do Sul e Sudeste."
            "</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            painel.grafico_mapa_estados(distribuicao, ano_estado),
            width="stretch",
        )

    with participacao_coluna:
        st.markdown(
            '<div class="agro-badge-info">Mart 10 · Concentração de Mercado</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**10 · Estados com maior participação**")
        st.caption(f"{ano_estado} · participação nacional e volume produzido")
        st.markdown(
            '<div class="agro-card-note">'
            "<strong>O que este gráfico entrega:</strong> Ranking das UFs por participação relativa (%). "
            "Evidencia o princípio de Pareto no agronegócio: os líderes concentram mais de metade de todo o grão nacional."
            "</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            painel.grafico_participacao_estados(dados_ano),
            width="stretch",
        )

    comparacao_coluna, area_coluna = st.columns(2)
    with comparacao_coluna:
        st.markdown(
            '<div class="agro-badge-info">Mart 10 · Série Histórica Estadual</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**10 · Comparação da produção por UF**")
        st.markdown(
            '<div class="agro-card-note">'
            "<strong>O que este gráfico entrega:</strong> Compara a trajetória temporal das 27 UFs entre 2000 e 2025. "
            "Permite acompanhar a ascensão acelerada do Centro-Oeste e a maturidade de estados tradicionais."
            "</div>",
            unsafe_allow_html=True,
        )
        metrica_comparacao = st.selectbox(
            "Comparar por",
            options=("Produção (t)", "Participação (%)"),
            key="metrica_comparacao_uf",
        )
        st.plotly_chart(
            painel.grafico_comparacao_estados(distribuicao, metrica_comparacao),
            width="stretch",
        )
    with area_coluna:
        st.markdown(
            '<div class="agro-badge-info">Mart 06 · Eficiência Operacional</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**06 · Área plantada versus colhida por UF**")
        st.caption("2025 · hectares")
        st.markdown(
            '<div class="agro-card-note">'
            "<strong>O que este painel entrega:</strong> Contrapõe os hectares semeados contra os colhidos em 2025. "
            "A diferença entre essas medidas não comprova perda nem identifica sua causa; explicações climáticas, "
            "fitossanitárias ou operacionais são hipóteses que precisam de dados adicionais."
            "</div>",
            unsafe_allow_html=True,
        )
        diferenca_area = marts["diferenca_area_plantada_colhida_por_estado_2025"]
        st.plotly_chart(
            painel.grafico_area_por_estado(diferenca_area),
            width="stretch",
        )
        tabela(
            diferenca_area.sort_values(
                "diferenca_area_plantada_colhida_hectares", ascending=False
            ),
            {
                "uf": "UF",
                "area_plantada_total_hectares": "Plantada (ha)",
                "area_colhida_total_hectares": "Colhida (ha)",
                "diferenca_area_plantada_colhida_hectares": "Diferença entre áreas (ha)",
            },
            altura=300,
        )

    st.markdown(
        '<div class="agro-badge-info">Mart 15 · Diversificação & Risco de Portfólio</div>',
        unsafe_allow_html=True,
    )
    st.markdown("**15 · Composição do valor por cultura e UF · 2025**")
    composicao = marts["concentracao_valor_producao_por_cultura_estado_2025"]
    ufs_composicao = tuple(sorted(composicao["uf"].drop_duplicates().tolist()))
    if not ufs_composicao:
        mostrar_erro_marts(
            "A consulta 15 não retornou UFs para a composição estadual de 2025."
        )
    uf_selecionada = st.selectbox(
        "UF para composição",
        options=ufs_composicao,
        key="uf_composicao",
    )
    composicao_uf = composicao.loc[composicao["uf"].eq(uf_selecionada)]
    if composicao_uf.empty:
        mostrar_erro_marts(
            f"A consulta 15 não retornou culturas para a UF {uf_selecionada}."
        )
    linha_composicao = composicao_uf.iloc[0]

    st.markdown(
        '<div class="agro-card-note">'
        "<strong>Conceitos Econômicos entregues nesta seção:</strong><br>"
        "• <strong>Valor Total Estadual:</strong> Faturamento agrícola bruto das 7 culturas na UF selecionada.<br>"
        "• <strong>Índice HHI (Herfindahl-Hirschman, 0 a 1):</strong> Mede o nível de dependência ou concentração da receita em poucas culturas. "
        "Valores próximos de 1,0 indicam forte monocultura; valores baixos (&lt; 0,30) indicam matriz agrícola diversificada.<br>"
        "• <strong>Número Efetivo de Culturas (1/HHI):</strong> Quantidade equivalente de culturas de igual receita necessária para reproduzir a concentração observada."
        "</div>",
        unsafe_allow_html=True,
    )

    indicadores_composicao = st.columns(3)
    indicadores_composicao[0].metric(
        "Valor total estadual (mil R$)",
        painel.reais(linha_composicao["valor_total_estado_mil_reais"]),
        help="Soma da receita bruta gerada pelas 7 culturas na UF selecionada em 2025.",
    )
    indicadores_composicao[1].metric(
        "HHI · concentração",
        painel.numero(linha_composicao["indice_concentracao_hhi"], 3),
        help="Índice Herfindahl-Hirschman (proporções de 0 a 1). Maior valor = maior concentração.",
    )
    indicadores_composicao[2].metric(
        "Número efetivo de culturas",
        painel.numero(linha_composicao["numero_efetivo_culturas"], 1),
        help="Inverso do HHI (1/HHI), indicando diversificação real da pauta produtiva.",
    )
    composicao_esquerda, composicao_direita = st.columns(2)
    with composicao_esquerda:
        st.plotly_chart(
            painel.grafico_composicao_cultura(composicao, uf_selecionada),
            width="stretch",
        )
    with composicao_direita:
        tabela(
            composicao_uf.sort_values("ranking_no_estado"),
            {
                "uf": "UF",
                "cultura": "Cultura",
                "valor_producao_mil_reais": "Valor (mil R$)",
                "valor_total_estado_mil_reais": "Total estadual (mil R$)",
                "participacao_valor_estado_percentual": "Participação (%)",
                "ranking_no_estado": "Posição",
                "indice_concentracao_hhi": "HHI",
                "numero_efetivo_culturas": "Nº efetivo de culturas",
            },
            altura=330,
        )

    st.markdown(
        '<div class="agro-badge-info">Mart 10 · Tabela Consolidada</div>',
        unsafe_allow_html=True,
    )
    st.markdown("**10 · Ranking estadual por ano**")
    st.markdown(
        '<div class="agro-card-note">'
        "<strong>O que esta tabela entrega:</strong> Classificação completa das 27 Unidades Federativas no ano selecionado, "
        "com produção física em toneladas, participação relativa na safra nacional e categorização de destaque."
        "</div>",
        unsafe_allow_html=True,
    )
    busca_uf = st.text_input("Buscar UF", key="busca_ranking_uf")
    tabela_estados = filtrar_busca(dados_ano, busca_uf, ("uf", "destaque")).sort_values(
        "ranking_no_ano"
    )
    tabela(
        tabela_estados,
        {
            "uf": "UF",
            "ano": "Ano",
            "ranking_no_ano": "Posição",
            "quantidade_produzida_toneladas": "Produção (t)",
            "participacao_nacional_percentual": "Participação (%)",
            "destaque": "Destaque",
        },
    )

with aba_municipios:
    st.subheader("Expansão, produtividade e rankings municipais")
    st.caption("Comparações de 2000 a 2025 e variação anual de 2024 a 2025.")

    expansao = marts["municipios_maior_expansao_area_plantada"]
    aumento_producao = marts["municipios_maior_aumento_quantidade_produzida_2000_2025"]
    rendimento_municipal = marts[
        "ranking_municipios_evolucao_rendimento_agregado_2000_2025"
    ]

    st.markdown(
        '<div class="agro-card-note">'
        "<strong>Recordes Municipais Históricos (2000–2025):</strong> "
        "Destaques dos municípios que lideraram os avanços em área cultivada, tonelagem colhida e rendimento ponderado no Brasil."
        "</div>",
        unsafe_allow_html=True,
    )

    cards_municipais = st.columns(3)
    maior_expansao = (
        expansao.sort_values("crescimento_area_hectares", ascending=False)
        .head(1)
        .iloc[0]
    )
    maior_aumento = (
        aumento_producao.sort_values("aumento_quantidade_toneladas", ascending=False)
        .head(1)
        .iloc[0]
    )
    maior_rendimento = (
        rendimento_municipal.sort_values("ranking", ascending=True).head(1).iloc[0]
    )
    cards_municipais[0].metric(
        f"Maior expansão de área · {maior_expansao['municipio']}",
        f"{painel.numero(maior_expansao['crescimento_area_hectares'])} ha",
        help="Maior incremento absoluto de área semeada no período de 26 safras.",
    )
    cards_municipais[1].metric(
        f"Maior aumento de produção · {maior_aumento['municipio']}",
        f"{painel.numero(maior_aumento['aumento_quantidade_toneladas'])} t",
        help="Maior salto absoluto em volume físico colhido no período.",
    )
    cards_municipais[2].metric(
        f"Maior aumento de rendimento · {maior_rendimento['municipio']}",
        painel.pct(maior_rendimento["aumento_rendimento_percentual"], 1),
        help="Maior evolução percentual de rendimento agregado (todas as 7 culturas).",
    )

    mudanca_coluna, filtros_coluna = st.columns(2)
    with mudanca_coluna:
        st.markdown(
            '<div class="agro-badge-info">Mart 04 · Oscilação Interanual</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**04 · Variação da produção por cultura**")
        st.caption("2024 → 2025 · variação percentual nacional")
        st.markdown(
            '<div class="agro-card-note">'
            "<strong>O que este gráfico entrega:</strong> Taxa de crescimento ou contração no volume físico colhido entre 2024 e 2025.<br>"
            "• Barras em <strong>verde</strong>: Culturas com expansão de produção física.<br>"
            "• Barras em <strong>cinza ardósia</strong>: Culturas com retração de colheita, alertando para quebras climáticas ou redução de área plantada."
            "</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            painel.grafico_variacao_producao(
                marts["variacao_percentual_quantidade_produzida_por_cultura_2024_2025"]
            ),
            width="stretch",
        )
    with filtros_coluna:
        st.markdown("**Filtros dos rankings municipais**")
        ufs_disponiveis = distribuicao["uf"].drop_duplicates().tolist()
        ufs = ["Todas", *sorted(ufs_disponiveis)]
        uf_filtro = st.selectbox("UF", options=ufs, key="uf_municipios")
        busca_municipio = st.text_input(
            "Município ou código IBGE", key="busca_municipios"
        )
        st.caption(
            "As consultas 03 e 07 não retornam UF; o filtro de UF só se aplica "
            "às tabelas que possuem essa coluna. As consultas desta aba somam "
            "as sete culturas e não oferecem filtro individual por cultura."
        )

    expansao_filtrada = filtrar_municipios(expansao, uf_filtro, busca_municipio)
    aumento_filtrado = filtrar_municipios(aumento_producao, uf_filtro, busca_municipio)
    rendimento_filtrado = filtrar_municipios(
        rendimento_municipal, uf_filtro, busca_municipio
    )
    alertas = filtrar_municipios(
        marts["expansao_area_sem_aumento_producao_2000_2025"],
        uf_filtro,
        busca_municipio,
    )

    st.markdown(
        '<div class="agro-badge-info">Mart 03 · Fronteira Agrícola</div>',
        unsafe_allow_html=True,
    )
    st.markdown("**03 · Municípios com maior expansão de área · 2000–2025**")
    st.markdown(
        '<div class="agro-card-note">'
        "<strong>O que esta tabela entrega:</strong> Top 10 municípios brasileiros com maior incorporação absoluta de área plantada (ha) "
        "ao longo de 26 safras. Retrata a abertura e consolidação da fronteira agrícola nacional (Centro-Oeste e MATOPIBA)."
        "</div>",
        unsafe_allow_html=True,
    )
    tabela(
        expansao_filtrada.sort_values("ranking").head(10),
        {
            "ranking": "Posição",
            "codigo_municipio_ibge": "Código IBGE",
            "municipio": "Município",
            "area_plantada_2000_hectares": "Área 2000 (ha)",
            "area_plantada_2025_hectares": "Área 2025 (ha)",
            "crescimento_area_hectares": "Aumento de área (ha)",
            "crescimento_area_percentual": "Aumento percentual (%)",
        },
    )

    st.markdown(
        '<div class="agro-badge-info">Mart 07 · Incremento em Volume Físico</div>',
        unsafe_allow_html=True,
    )
    st.markdown("**07 · Municípios com maior aumento de produção · 2000–2025**")
    st.markdown(
        '<div class="agro-card-note">'
        "<strong>O que esta tabela entrega:</strong> Top 10 municípios com maior ganho absoluto de colheita em toneladas (2000 a 2025). "
        "Destaca as regiões onde a ampliação territorial aliou-se à mecanização e biotecnologia."
        "</div>",
        unsafe_allow_html=True,
    )
    tabela(
        aumento_filtrado.sort_values("ranking_2025").head(10),
        {
            "ranking_2025": "Posição",
            "codigo_municipio_ibge": "Código IBGE",
            "municipio": "Município",
            "quantidade_2000_toneladas": "Quantidade 2000 (t)",
            "quantidade_2025_toneladas": "Quantidade 2025 (t)",
            "aumento_quantidade_toneladas": "Aumento em toneladas (t)",
        },
    )

    st.markdown(
        '<div class="agro-badge-info">Mart 14 · Eficiência Agronômica Agregada</div>',
        unsafe_allow_html=True,
    )
    st.markdown("**14 · Maiores aumentos de rendimento agregado · 2000–2025**")
    st.markdown(
        '<div class="agro-card-note">'
        "<strong>O que esta tabela entrega:</strong> Top 20 municípios com maior avanço percentual no rendimento médio agregado "
        "(kg/ha somando as 7 culturas).<br>"
        "<em>Nota metodológica:</em> Não representa a média simples dos rendimentos, mas a razão: "
        "<em>(1000 × Volume Total em t) ÷ Área Colhida Total em ha</em>."
        "</div>",
        unsafe_allow_html=True,
    )
    tabela(
        rendimento_filtrado.sort_values("ranking").head(20),
        {
            "ranking": "Posição",
            "codigo_municipio_ibge": "Código IBGE",
            "municipio": "Município",
            "uf": "UF",
            "rendimento_2000_kg_por_hectare": "Rendimento 2000 (kg/ha)",
            "rendimento_2025_kg_por_hectare": "Rendimento 2025 (kg/ha)",
            "aumento_rendimento_kg_por_hectare": "Aumento absoluto (kg/ha)",
            "aumento_rendimento_percentual": "Aumento percentual (%)",
        },
    )

    st.markdown(
        '<div class="agro-badge-info">Mart 09 · Auditoria & Sinais de Risco Agronômico</div>',
        unsafe_allow_html=True,
    )
    st.markdown("**09 · Área aumentou, produção não acompanhou · 2000–2025**")
    st.markdown(
        '<div class="agro-card-note">'
        "<strong>O que este painel investigativo entrega:</strong> Relação de municípios onde a área destinada ao cultivo cresceu entre 2000 e 2025, "
        "porém a produção física em toneladas sofreu retração.<br>"
        "<em>Guia de inteligência e auditoria:</em> Esta tabela serve para triagem investigativa. Pode apontar quebras climáticas severas "
        "na safra 2025, esgotamento do solo ou migração da área para culturas de menor peso físico mas maior valor agregado."
        "</div>",
        unsafe_allow_html=True,
    )
    tabela(
        alertas,
        {
            "codigo_municipio_ibge": "Código IBGE",
            "municipio": "Município",
            "uf": "UF",
            "area_plantada_2000_hectares": "Área 2000 (ha)",
            "area_plantada_2025_hectares": "Área 2025 (ha)",
            "aumento_area_hectares": "Aumento de área (ha)",
            "quantidade_2000_toneladas": "Quantidade 2000 (t)",
            "quantidade_2025_toneladas": "Quantidade 2025 (t)",
            "variacao_quantidade_toneladas": "Variação da quantidade (t)",
        },
        altura=500,
    )

with aba_produtividade:
    st.subheader("Produtividade e valor por hectare")
    st.caption(
        "Rendimento físico nacional (kg/ha) e valor bruto municipal (R$/ha) "
        "são indicadores distintos."
    )

    st.markdown(
        '<div class="agro-card-note">'
        "<strong>Diferenciação Metodológica Fundamental:</strong><br>"
        "• <strong>Rendimento Médio Físico (kg/ha):</strong> Mede a eficiência biológica da terra (quilos colhidos por hectare). "
        "É determinado por genética das sementes, manejo do solo, adubação e clima.<br>"
        "• <strong>Valor Bruto por Hectare (R$/ha):</strong> Avalia o retorno financeiro bruto do solo (faturamento monetário gerado por hectare colhido). "
        "Oscila conforme cotação de mercado da commodity e não desconta custos de produção."
        "</div>",
        unsafe_allow_html=True,
    )

    rendimento_cultura = marts["ranking_aumento_rendimento_medio_por_cultura_2000_2025"]
    grafico_coluna, tabela_coluna = st.columns(2)
    with grafico_coluna:
        st.markdown(
            '<div class="agro-badge-info">Mart 11 · Evolução Tecnológica por Cultura</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**11 · Rendimento nacional por cultura · 2000–2025**")
        st.caption("Dumbbell · kg/ha · ordenado pelo aumento percentual do mart")
        st.markdown(
            '<div class="agro-card-note">'
            "<strong>O que este gráfico dumbbell entrega:</strong> Compara a produtividade física nacional entre 2000 (ponto cinza) "
            "e 2025 (ponto verde). Destaca a evolução agronômica das culturas nas últimas duas décadas e meia."
            "</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            painel.grafico_rendimento_culturas(rendimento_cultura),
            width="stretch",
        )
    with tabela_coluna:
        st.markdown(
            '<div class="agro-badge-info">Mart 11 · Tabela Analítica de Produtividade</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**11 · Rendimento por cultura**")
        st.markdown(
            '<div class="agro-card-note">'
            "<strong>O que esta tabela entrega:</strong> Valores absolutos em kg/ha e variação percentual acumulada entre 2000 e 2025 "
            "para cada uma das 7 culturas monitoradas."
            "</div>",
            unsafe_allow_html=True,
        )
        tabela(
            rendimento_cultura.sort_values("ranking_aumento"),
            {
                "ranking_aumento": "Posição",
                "cultura": "Cultura",
                "rendimento_2000_kg_por_hectare": "2000 (kg/ha)",
                "rendimento_2025_kg_por_hectare": "2025 (kg/ha)",
                "aumento_rendimento_kg_por_hectare": "Aumento absoluto (kg/ha)",
                "aumento_percentual": "Variação percentual (%)",
            },
        )

    st.markdown(
        '<div class="agro-badge-info">Mart 13 · Monetização do Solo por Hectare</div>',
        unsafe_allow_html=True,
    )
    st.markdown("**13 · Valor bruto por hectare · municípios · 2025**")
    st.markdown(
        '<div class="agro-card-note">'
        "<strong>O que esta seção entrega:</strong> Identifica as cidades líderes em faturamento bruto por hectare colhido na cultura selecionada.<br>"
        "<em>Ressalva Executiva Crucial:</em> O valor bruto por hectare (R$/ha) reflete receita e <strong>NÃO representa lucro líquido</strong>, "
        "pois não desconta despesas com defensivos, adubos, combustível, leasing de máquinas ou frete."
        "</div>",
        unsafe_allow_html=True,
    )
    valor_hectare = marts["ranking_valor_bruto_por_hectare_cultura_2025"]
    cultura_valor = st.selectbox(
        "Cultura do ranking",
        options=painel.CULTURAS,
        key="cultura_valor_hectare",
    )
    ranking_cultura = valor_hectare.loc[
        valor_hectare["cultura"].eq(cultura_valor)
    ].sort_values("ranking_na_cultura")
    barras_coluna, tabela_coluna = st.columns(2)
    with barras_coluna:
        st.markdown("**Top 10 · valor bruto por hectare**")
        st.plotly_chart(
            painel.grafico_valor_bruto_hectare(ranking_cultura),
            width="stretch",
        )
    with tabela_coluna:
        st.markdown("**Ranking detalhado · R$/ha**")
        tabela_valor = ranking_cultura[
            [
                "ranking_na_cultura",
                "municipio",
                "uf",
                "valor_producao_mil_reais",
                "area_colhida_hectares",
            ]
        ].rename(
            columns={
                "ranking_na_cultura": "Posição",
                "municipio": "Município",
                "uf": "UF",
                "valor_producao_mil_reais": "Valor da produção (mil R$)",
                "area_colhida_hectares": "Área colhida (ha)",
            }
        )
        tabela_valor["Valor bruto por hectare (R$/ha)"] = [
            painel.reais(valor * 1000)
            for valor in ranking_cultura["valor_bruto_por_hectare_mil_reais"]
        ]
        tabela(
            tabela_valor,
            altura=440,
        )
