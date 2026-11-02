"""Gera um relatório HTML estático a partir dos marts agrícolas."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd

import painel

RAIZ = Path(__file__).resolve().parent
SAIDA = RAIZ / "relatorio.html"

ESTILO = """
<style>
:root {
  color-scheme: light;
  --ink: #1d3028;
  --muted: #748178;
  --line: #e4eae4;
  --paper: #f4f6f3;
  --green: #23734d;
  --green-dark: #193d2d;
}
* { box-sizing: border-box; }
body {
  max-width: 1540px;
  margin: 0 auto;
  padding: 32px clamp(16px, 3vw, 44px) 48px;
  color: var(--ink);
  background: var(--paper);
  font: 15px/1.5 sans-serif;
}
h1, h2, h3 { color: var(--ink); letter-spacing: -.025em; }
h1 { margin: 4px 0 8px; font-size: clamp(1.8rem, 2.4vw, 2.3rem); }
h2 { margin: 0 0 4px; font-size: 1.45rem; }
h3 { margin: 24px 0 10px; font-size: 1.05rem; }
p { margin: 6px 0; }
.eyebrow {
  color: var(--green);
  font-size: .72rem;
  font-weight: 800;
  letter-spacing: .12em;
  text-transform: uppercase;
}
.muted, .caption { color: var(--muted); }
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(205px, 1fr));
  gap: 14px;
  margin: 20px 0;
}
.card, .panel {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 8px 24px #203b2b0a;
}
.card {
  min-height: 108px;
  padding: 16px 18px;
  border-top: 3px solid var(--green);
}
.card-label { color: var(--muted); font-size: .82rem; font-weight: 650; }
.card-value {
  margin-top: 8px;
  font-size: clamp(1.2rem, 1.8vw, 1.65rem);
  font-weight: 760;
  letter-spacing: -.04em;
  overflow-wrap: anywhere;
}
.faixa {
  margin-top: 28px;
  padding: 22px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
}
.grade {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  align-items: start;
  margin-top: 14px;
}
.panel { overflow: hidden; padding: 12px; }
.chart { min-width: 0; }
.wide { grid-column: 1 / -1; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: .86rem; }
th, td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}
th { color: var(--green-dark); background: #f4f7f3; font-weight: 700; }
tr:last-child td { border-bottom: 0; }
footer {
  margin-top: 28px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  text-align: right;
}
@media (max-width: 760px) {
  body { padding-top: 20px; }
  .faixa { padding: 16px; }
  .grade { grid-template-columns: minmax(0, 1fr); }
  .wide { grid-column: auto; }
}
</style>
"""


def cartao(rotulo: str, valor: str) -> str:
    return (
        '<article class="card">'
        f'<div class="card-label">{escape(rotulo)}</div>'
        f'<div class="card-value">{escape(valor)}</div>'
        "</article>"
    )


def cartoes_html(itens: list[tuple[str, str]]) -> str:
    return (
        '<div class="cards">'
        + "".join(cartao(rotulo, valor) for rotulo, valor in itens)
        + "</div>"
    )


def tabela_html(dados: pd.DataFrame, colunas: Mapping[str, str]) -> str:
    cabecalho = "".join(f"<th>{escape(rotulo)}</th>" for rotulo in colunas.values())
    linhas = []
    for linha in dados.loc[:, list(colunas)].itertuples(index=False, name=None):
        celulas = "".join(f"<td>{escape(str(valor))}</td>" for valor in linha)
        linhas.append(f"<tr>{celulas}</tr>")
    return (
        '<div class="panel table-wrap"><table><thead><tr>'
        f"{cabecalho}</tr></thead><tbody>{''.join(linhas)}</tbody></table></div>"
    )


def grafico_html(figura: object, div_id: str, titulo: str) -> str:
    figura.update_layout(title_text=titulo)
    return figura.to_html(
        full_html=False,
        include_plotlyjs="cdn" if div_id == "g01" else False,
        div_id=div_id,
        config={"responsive": True, "displaylogo": False},
    )


def gerar_relatorio(marts: dict[str, pd.DataFrame], gerado_em: datetime) -> str:
    resumo = marts["resumo_totais_2025"].iloc[0]
    cards_nacionais = cartoes_html(
        [
            (
                "Valor da produção (bi R$)",
                f"{painel.reais(resumo['valor_producao_bilhoes_reais'])} bi",
            ),
            (
                "Quantidade produzida (mi t)",
                f"{painel.numero(resumo['volume_milhoes_toneladas'])} mi t",
            ),
            (
                "Área colhida (mi ha)",
                f"{painel.numero(resumo['area_milhoes_hectares'])} mi ha",
            ),
            (
                "Rendimento médio (t/ha)",
                f"{painel.numero(resumo['rendimento_toneladas_por_hectare'])} t/ha",
            ),
        ]
    )

    evolucao = marts["evolucao_valor_producao_por_cultura_2000_2025"]
    evolucao = evolucao.loc[
        evolucao["ano"].between(2000, 2025) & evolucao["cultura"].isin(painel.CULTURAS)
    ]

    distribuicao = marts["distribuicao_geografica_producao_por_estado_2000_2025"]
    dados_ano = distribuicao.loc[distribuicao["ano"].eq(2025)]
    lider = dados_ano.sort_values("ranking_no_ano").iloc[0]
    cards_estado = cartoes_html(
        [
            ("Estado líder · 2025", str(lider["uf"])),
            (
                "Produção do estado líder (t) · 2025",
                f"{painel.numero(lider['quantidade_produzida_toneladas'])} t",
            ),
            (
                "Participação nacional · 2025",
                painel.pct(lider["participacao_nacional_percentual"], 2),
            ),
        ]
    )

    composicao = marts["concentracao_valor_producao_por_cultura_estado_2025"]
    ufs_composicao = tuple(sorted(composicao["uf"].drop_duplicates().tolist()))
    uf_selecionada = ufs_composicao[0]
    composicao_uf = composicao.loc[composicao["uf"].eq(uf_selecionada)]
    linha_composicao = composicao_uf.iloc[0]
    cards_composicao = cartoes_html(
        [
            (
                f"Valor total estadual · {uf_selecionada} (mil R$)",
                painel.reais(linha_composicao["valor_total_estado_mil_reais"]),
            ),
            (
                f"HHI · concentração · {uf_selecionada}",
                painel.numero(linha_composicao["indice_concentracao_hhi"], 3),
            ),
            (
                f"Número efetivo de culturas · {uf_selecionada}",
                painel.numero(linha_composicao["numero_efetivo_culturas"], 1),
            ),
        ]
    )

    expansao = marts["municipios_maior_expansao_area_plantada"]
    aumento_producao = marts["municipios_maior_aumento_quantidade_produzida_2000_2025"]
    rendimento_municipal = marts[
        "ranking_municipios_evolucao_rendimento_agregado_2000_2025"
    ]
    maior_expansao = expansao.sort_values(
        "crescimento_area_hectares", ascending=False
    ).iloc[0]
    maior_aumento = aumento_producao.sort_values(
        "aumento_quantidade_toneladas", ascending=False
    ).iloc[0]
    maior_rendimento = rendimento_municipal.sort_values("ranking").iloc[0]
    cards_municipais = cartoes_html(
        [
            (
                f"Maior expansão de área · {maior_expansao['municipio']}",
                f"{painel.numero(maior_expansao['crescimento_area_hectares'])} ha",
            ),
            (
                f"Maior aumento de produção · {maior_aumento['municipio']}",
                f"{painel.numero(maior_aumento['aumento_quantidade_toneladas'])} t",
            ),
            (
                f"Maior aumento de rendimento · {maior_rendimento['municipio']}",
                painel.pct(maior_rendimento["aumento_rendimento_percentual"], 1),
            ),
        ]
    )

    variacao = marts["variacao_percentual_quantidade_produzida_por_cultura_2024_2025"]
    diferenca_area = marts["diferenca_area_plantada_colhida_por_estado_2025"]
    composicao_ordenada = composicao_uf.sort_values("ranking_no_estado")
    distribuicao_ordenada = dados_ano.sort_values("ranking_no_ano")
    cultura_valor = painel.CULTURAS[0]
    valor_hectare = marts["ranking_valor_bruto_por_hectare_cultura_2025"]
    ranking_cultura = valor_hectare.loc[
        valor_hectare["cultura"].eq(cultura_valor)
    ].sort_values("ranking_na_cultura")

    rendimento_cultura = marts["ranking_aumento_rendimento_medio_por_cultura_2000_2025"]
    alertas = marts["expansao_area_sem_aumento_producao_2000_2025"]
    area_colhida = marts["percentual_area_plantada_colhida_em_2025"]
    html_graficos = [
        grafico_html(
            painel.grafico_area_colhida(area_colhida),
            "g01",
            "05 · Área plantada: colhida × não colhida · Brasil · 2025",
        ),
        grafico_html(
            painel.grafico_evolucao_valor(evolucao),
            "g02",
            "08 · Evolução do valor da produção · Brasil · 2000–2025",
        ),
        grafico_html(
            painel.grafico_mapa_estados(distribuicao, 2025),
            "g03",
            "10 · Produção agrícola por UF · 2025",
        ),
        grafico_html(
            painel.grafico_participacao_estados(dados_ano),
            "g04",
            "10 · Estados com maior participação · 2025",
        ),
        grafico_html(
            painel.grafico_comparacao_estados(distribuicao, "Produção (t)"),
            "g05",
            "10 · Comparação da produção por UF · 2000 e 2025",
        ),
        grafico_html(
            painel.grafico_area_por_estado(diferenca_area),
            "g06",
            "06 · Área plantada versus colhida por UF · 2025",
        ),
        grafico_html(
            painel.grafico_composicao_cultura(composicao, uf_selecionada),
            "g07",
            f"15 · Composição do valor por cultura e UF · 2025 · {uf_selecionada}",
        ),
        grafico_html(
            painel.grafico_variacao_producao(variacao),
            "g08",
            "04 · Variação da produção por cultura · 2024 → 2025",
        ),
        grafico_html(
            painel.grafico_rendimento_culturas(rendimento_cultura),
            "g09",
            "11 · Rendimento nacional por cultura · 2000 e 2025",
        ),
        grafico_html(
            painel.grafico_valor_bruto_hectare(ranking_cultura),
            "g10",
            f"13 · Valor bruto por hectare · {cultura_valor} · 2025",
        ),
    ]

    tabela_lideres = marts["ranking_valor_da_producao_muncipio_por_cultura"]
    tabela_area_estado = diferenca_area.sort_values(
        "diferenca_area_plantada_colhida_hectares", ascending=False
    )
    tabela_expansao = expansao.sort_values("ranking").head(10)
    tabela_aumento = aumento_producao.sort_values("ranking_2025").head(10)
    tabela_rendimento_municipal = rendimento_municipal.sort_values("ranking").head(20)
    tabela_rendimento_cultura = rendimento_cultura.sort_values("ranking_aumento")
    tabela_valor = ranking_cultura[
        [
            "ranking_na_cultura",
            "municipio",
            "uf",
            "valor_producao_mil_reais",
            "area_colhida_hectares",
        ]
    ].copy()
    tabela_valor["valor_bruto_por_hectare"] = [
        painel.reais(valor * 1000)
        for valor in ranking_cultura["valor_bruto_por_hectare_mil_reais"]
    ]

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Produção agrícola brasileira | AgroData</title>
{ESTILO}
</head>
<body>
<header>
  <div class="eyebrow">Painel de inteligência agrícola</div>
  <h1>Produção agrícola brasileira</h1>
  <p class="muted">Culturas consideradas: Arroz, Algodão, Café, Feijão, Milho, Soja e Trigo. Período: 2000 a 2025.</p>
  <p class="muted">Fonte: PAM · IBGE SIDRA 5457</p>
  <p class="caption">Dados carregados do DuckDB · indicadores nacionais de 2025 · rendimento convertido de kg/ha para t/ha.</p>
</header>
{cards_nacionais}
<main>
  <section class="faixa" id="panorama">
    <h2>Panorama da produção</h2>
    <p class="caption">Indicadores nacionais de 2025 e evolução das culturas PAM.</p>
    <div class="grade">
      <div><h3>05 · Área plantada: colhida × não colhida</h3><p class="caption">Brasil · 2025 · participação percentual</p>{
        html_graficos[0]
    }</div>
      <div><h3>08 · Evolução do valor da produção</h3><p class="caption">Brasil · 2000–2025 · mil R$</p>{
        html_graficos[1]
    }<p class="caption">Série completa e sete culturas; sem recorte de período.</p></div>
    </div>
    <h3>Municípios em destaque · líder por cultura · 2000–2025</h3>
    {
        tabela_html(
            tabela_lideres,
            {
                "cultura": "Cultura",
                "municipio": "Município líder",
                "uf": "UF",
                "valor_total_producao_mil_reais": "Valor total (mil R$)",
            },
        )
    }
  </section>
  <section class="faixa" id="estados">
    <h2>Distribuição por estado</h2>
    <p class="caption">Produção e participação estadual nos anos disponíveis · padrão: 2025.</p>
    {cards_estado}
    <div class="grade">
      <div><h3>10 · Produção agrícola por UF</h3><p class="caption">Contornos estaduais: malhas territoriais do IBGE.</p>{
        html_graficos[2]
    }</div>
      <div><h3>10 · Estados com maior participação</h3><p class="caption">2025 · participação nacional e volume produzido</p>{
        html_graficos[3]
    }</div>
      <div><h3>10 · Comparação da produção por UF</h3><p class="caption">Produção (t) · 2000 e 2025</p>{
        html_graficos[4]
    }</div>
      <div><h3>06 · Área plantada versus colhida por UF</h3><p class="caption">2025 · hectares</p>{
        html_graficos[5]
    }
        {
        tabela_html(
            tabela_area_estado,
            {
                "uf": "UF",
                "area_plantada_total_hectares": "Plantada (ha)",
                "area_colhida_total_hectares": "Colhida (ha)",
                "diferenca_area_plantada_colhida_hectares": "Diferença (ha)",
            },
        )
    }
      </div>
    </div>
    <h3>15 · Composição do valor por cultura e UF · 2025 · {escape(uf_selecionada)}</h3>
    {cards_composicao}
    <div class="grade">
      <div>{html_graficos[6]}</div>
      <div>{
        tabela_html(
            composicao_ordenada,
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
        )
    }</div>
    </div>
    <h3>10 · Ranking estadual por ano · 2025</h3>
    {
        tabela_html(
            distribuicao_ordenada,
            {
                "uf": "UF",
                "ano": "Ano",
                "ranking_no_ano": "Posição",
                "quantidade_produzida_toneladas": "Produção (t)",
                "participacao_nacional_percentual": "Participação (%)",
                "destaque": "Destaque",
            },
        )
    }
  </section>
  <section class="faixa" id="expansao">
    <h2>Expansão e rankings</h2>
    <p class="caption">Comparações de 2000 a 2025 e variação anual de 2024 a 2025.</p>
    {cards_municipais}
    <div class="grade">
      <div><h3>04 · Variação da produção por cultura</h3><p class="caption">2024 → 2025 · variação percentual nacional</p>{
        html_graficos[7]
    }</div>
      <div><h3>Filtros dos rankings municipais</h3><p>UF: Todas · Município/código IBGE: sem busca</p><p class="caption">03 e 07 não retornam UF; as tabelas aplicam o universo materializado. Sem filtro individual por cultura.</p></div>
    </div>
    <h3>03 · Municípios com maior expansão de área · 2000–2025</h3>
    {
        tabela_html(
            tabela_expansao,
            {
                "ranking": "Posição",
                "codigo_municipio_ibge": "Código IBGE",
                "municipio": "Município",
                "area_plantada_2000_hectares": "Área 2000 (ha)",
                "area_plantada_2025_hectares": "Área 2025 (ha)",
                "crescimento_area_hectares": "Aumento (ha)",
                "crescimento_area_percentual": "Aumento (%)",
            },
        )
    }
    <h3>07 · Municípios com maior aumento de produção · 2000–2025</h3>
    {
        tabela_html(
            tabela_aumento,
            {
                "ranking_2025": "Posição",
                "codigo_municipio_ibge": "Código IBGE",
                "municipio": "Município",
                "quantidade_2000_toneladas": "Quantidade 2000 (t)",
                "quantidade_2025_toneladas": "Quantidade 2025 (t)",
                "aumento_quantidade_toneladas": "Aumento (t)",
            },
        )
    }
    <h3>14 · Maiores aumentos de rendimento agregado · 2000–2025</h3>
    <p class="caption">Indicador agregado das culturas, não rendimento de cultura individual.</p>
    {
        tabela_html(
            tabela_rendimento_municipal,
            {
                "ranking": "Posição",
                "codigo_municipio_ibge": "Código IBGE",
                "municipio": "Município",
                "uf": "UF",
                "rendimento_2000_kg_por_hectare": "Rendimento 2000 (kg/ha)",
                "rendimento_2025_kg_por_hectare": "Rendimento 2025 (kg/ha)",
                "aumento_rendimento_kg_por_hectare": "Aumento (kg/ha)",
                "aumento_rendimento_percentual": "Aumento (%)",
            },
        )
    }
    <h3>09 · Área aumentou, produção não acompanhou · 2000–2025</h3>
    <p class="caption">Lista de casos para investigação; não constitui diagnóstico da causa.</p>
    {
        tabela_html(
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
        )
    }
  </section>
  <section class="faixa" id="produtividade">
    <h2>Produtividade e valor por hectare</h2>
    <p class="caption">Rendimento físico nacional (kg/ha) e valor bruto municipal (R$/ha) são indicadores distintos.</p>
    <div class="grade">
      <div><h3>11 · Rendimento nacional por cultura · 2000–2025</h3><p class="caption">Dumbbell · kg/ha · ordenado pelo aumento percentual do mart</p>{
        html_graficos[8]
    }</div>
      <div><h3>11 · Rendimento por cultura</h3>
        {
        tabela_html(
            tabela_rendimento_cultura,
            {
                "ranking_aumento": "Posição",
                "cultura": "Cultura",
                "rendimento_2000_kg_por_hectare": "2000 (kg/ha)",
                "rendimento_2025_kg_por_hectare": "2025 (kg/ha)",
                "aumento_rendimento_kg_por_hectare": "Aumento (kg/ha)",
                "aumento_percentual": "Variação (%)",
            },
        )
    }
      </div>
    </div>
    <h3>13 · Valor bruto por hectare · municípios · 2025</h3>
    <p class="caption">Cultura padrão: {
        escape(cultura_valor)
    }. Valor bruto não representa lucro. Conversão de mil R$/ha para R$/ha aplicada somente para apresentação.</p>
    <div class="grade">
      <div><h3>Top 10 · valor bruto por hectare</h3>{html_graficos[9]}</div>
      <div><h3>Ranking detalhado · R$/ha</h3>
        {
        tabela_html(
            tabela_valor,
            {
                "ranking_na_cultura": "Posição",
                "municipio": "Município",
                "uf": "UF",
                "valor_producao_mil_reais": "Valor da produção (mil R$)",
                "area_colhida_hectares": "Área colhida (ha)",
                "valor_bruto_por_hectare": "Valor bruto por hectare (R$/ha)",
            },
        )
    }
      </div>
    </div>
  </section>
</main>
<footer>Dados de {gerado_em.strftime("%d/%m/%Y %H:%M")}</footer>
</body>
</html>
"""


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    os.chdir(RAIZ)
    marts = painel.ler()
    conteudo = gerar_relatorio(marts, datetime.now().astimezone())
    SAIDA.write_text(conteudo, encoding="utf-8", newline="\n")
    tamanho_kb = SAIDA.stat().st_size / 1024
    print(f"Arquivo gerado: {SAIDA} ({tamanho_kb:.2f} KB)")


if __name__ == "__main__":
    main()
