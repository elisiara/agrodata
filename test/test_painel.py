import duckdb
import pandas as pd
import plotly.graph_objects as go
import pytest

import painel


def test_formatadores_usam_notacao_brasileira_e_preservam_nulos():
    assert painel.reais(1234.5) == "R$ 1.234,50"
    assert painel.pct(12.345) == "12,3%"
    assert painel.numero(-1234.5, 1) == "-1.234,5"
    assert painel.reais(float("nan")) == "R$ —"
    assert painel.numero(None) == "—"


def test_ler_carrega_selects_e_fecha_conexao_para_escrita(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    con = duckdb.connect("agrodata.duckdb")
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.exemplo AS SELECT 1 AS valor")
    con.close()

    dados = painel.ler(["exemplo"])

    assert list(dados) == ["exemplo"]
    assert dados["exemplo"]["valor"].tolist() == [1]
    con = duckdb.connect("agrodata.duckdb")
    con.execute("CREATE TABLE marts.pos_leitura AS SELECT 2 AS valor")
    assert con.execute("SELECT valor FROM marts.pos_leitura").fetchone()[0] == 2
    con.close()


def test_ler_falha_explicitamente_se_banco_ou_mart_nao_existir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(painel.ErroLeituraMarts, match="Banco agrodata.duckdb"):
        painel.ler(["exemplo"])

    con = duckdb.connect("agrodata.duckdb")
    con.execute("CREATE SCHEMA marts")
    con.close()
    with pytest.raises(painel.ErroLeituraMarts, match="marts.ausente"):
        painel.ler(["ausente"])


def test_grafico_area_colhida_representa_duas_partes_do_total():
    df = pd.DataFrame(
        {
            "percentual_area_plantada_colhida": [75],
            "percentual_area_plantada_nao_colhida": [25],
        }
    )

    figura = painel.grafico_area_colhida(df)

    assert isinstance(figura, go.Figure)
    assert list(figura.data[0].values) == [75, 25]
    assert len(figura.data[0].labels) == 2


def test_grafico_evolucao_valor_tem_um_ponto_por_linha():
    df = pd.DataFrame(
        {
            "ano": [2000, 2001],
            "cultura": ["Arroz", "Arroz"],
            "valor_producao_mil_reais": [10, 20],
        }
    )

    figura = painel.grafico_evolucao_valor(df)

    assert isinstance(figura, go.Figure)
    assert len(figura.data) == 1
    assert len(figura.data[0].x) == len(df)


def test_grafico_mapa_filtra_ano_e_ignora_uf_sem_coordenada():
    df = pd.DataFrame(
        {
            "uf": ["SP", "MG", "XX"],
            "ano": [2025, 2025, 2025],
            "quantidade_produzida_toneladas": [100, 50, 1],
            "participacao_nacional_percentual": [60, 30, 10],
        }
    )

    figura = painel.grafico_mapa_estados(df, 2025, "Produção (t)")

    assert isinstance(figura, go.Figure)
    assert list(figura.data[0].text) == ["SP", "MG"]
    assert list(figura.data[0].marker.color) == [100, 50]


def test_grafico_participacao_estados_representa_todas_as_ufs():
    df = pd.DataFrame(
        {
            "uf": ["SP", "MG"],
            "participacao_nacional_percentual": [60, 40],
            "quantidade_produzida_toneladas": [60, 40],
        }
    )

    figura = painel.grafico_participacao_estados(df)

    assert isinstance(figura, go.Figure)
    assert len(figura.data[0].y) == len(df)
    assert list(figura.data[0].y) == ["SP", "MG"]


def test_grafico_comparacao_estados_tem_ponto_por_uf_e_ano():
    df = pd.DataFrame(
        {
            "uf": ["SP", "SP", "MG", "MG"],
            "ano": [2000, 2025, 2000, 2025],
            "quantidade_produzida_toneladas": [10, 20, 5, 15],
            "participacao_nacional_percentual": [50, 60, 50, 40],
        }
    )

    figura = painel.grafico_comparacao_estados(df, "Produção (t)")

    assert isinstance(figura, go.Figure)
    assert sum(len(trace.x) for trace in figura.data) == len(df)


def test_grafico_area_por_estado_tem_duas_series_com_todas_as_ufs():
    df = pd.DataFrame(
        {
            "uf": ["SP", "MG"],
            "area_plantada_total_hectares": [20, 10],
            "area_colhida_total_hectares": [15, 8],
            "diferenca_area_plantada_colhida_hectares": [5, 2],
        }
    )

    figura = painel.grafico_area_por_estado(df)

    assert isinstance(figura, go.Figure)
    assert len(figura.data) == 2
    assert all(len(trace.y) == len(df) for trace in figura.data)


def test_grafico_composicao_filtra_uf_e_representa_culturas():
    df = pd.DataFrame(
        {
            "uf": ["SP", "SP", "MG"],
            "cultura": ["Soja", "Milho", "Soja"],
            "ranking_no_estado": [1, 2, 1],
            "participacao_valor_estado_percentual": [70, 30, 100],
        }
    )

    figura = painel.grafico_composicao_cultura(df, "SP")

    assert isinstance(figura, go.Figure)
    assert list(figura.data[0].labels) == ["Soja", "Milho"]
    assert list(figura.data[0].values) == [70, 30]


def test_grafico_variacao_separa_aumentos_e_reducoes_sem_perder_linhas():
    df = pd.DataFrame(
        {
            "cultura": ["Soja", "Arroz", "Milho"],
            "variacao_percentual": [10, -5, 0],
        }
    )

    figura = painel.grafico_variacao_producao(df)

    assert isinstance(figura, go.Figure)
    assert [len(trace.y) for trace in figura.data] == [2, 1]
    assert sum(len(trace.y) for trace in figura.data) == len(df)


def test_grafico_rendimento_representa_as_duas_medicoes_de_cada_cultura():
    df = pd.DataFrame(
        {
            "cultura": ["Soja", "Arroz"],
            "ranking_aumento": [1, 2],
            "rendimento_2000_kg_por_hectare": [1000, 2000],
            "rendimento_2025_kg_por_hectare": [1500, 1000],
            "aumento_rendimento_kg_por_hectare": [500, -1000],
            "aumento_percentual": [50, -50],
        }
    )

    figura = painel.grafico_rendimento_culturas(df)

    assert isinstance(figura, go.Figure)
    assert len(figura.data) == 4
    assert len(figura.data[2].x) == len(df)
    assert len(figura.data[3].x) == len(df)


def test_grafico_valor_bruto_converte_mil_reais_para_reais_por_hectare():
    df = pd.DataFrame(
        {
            "ranking_na_cultura": [2, 1],
            "municipio": ["Beta", "Alpha"],
            "uf": ["MG", "SP"],
            "valor_producao_mil_reais": [20, 10],
            "area_colhida_hectares": [10, 5],
            "valor_bruto_por_hectare_mil_reais": [2, 2],
        }
    )

    figura = painel.grafico_valor_bruto_hectare(df)

    assert isinstance(figura, go.Figure)
    assert list(figura.data[0].x) == [2000, 2000]
    assert list(figura.data[0].y) == ["Alpha", "Beta"]
