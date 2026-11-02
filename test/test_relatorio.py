from datetime import datetime

import pandas as pd

import painel
import relatorio


def _marts_sinteticos():
    return {
        "resumo_totais_2025": pd.DataFrame(
            [
                {
                    "valor_producao_bilhoes_reais": 1.25,
                    "volume_milhoes_toneladas": 2.5,
                    "area_milhoes_hectares": 3.75,
                    "rendimento_toneladas_por_hectare": 4.5,
                }
            ]
        ),
        "evolucao_valor_producao_por_cultura_2000_2025": pd.DataFrame(
            [
                {"ano": 2000, "cultura": "Arroz (em casca)", "valor_producao_mil_reais": 10},
                {"ano": 2025, "cultura": "Arroz (em casca)", "valor_producao_mil_reais": 20},
            ]
        ),
        "distribuicao_geografica_producao_por_estado_2000_2025": pd.DataFrame(
            [
                {
                    "uf": uf,
                    "ano": ano,
                    "ranking_no_ano": ranking,
                    "quantidade_produzida_toneladas": volume,
                    "participacao_nacional_percentual": participacao,
                    "destaque": "Maior produtor no ano" if ranking == 1 else None,
                }
                for ano, dados in (
                    (2000, [("SP", 1, 100, 60), ("MG", 2, 70, 40)]),
                    (2025, [("SP", 1, 200, 65), ("MG", 2, 100, 35)]),
                )
                for uf, ranking, volume, participacao in dados
            ]
        ),
        "concentracao_valor_producao_por_cultura_estado_2025": pd.DataFrame(
            [
                {
                    "uf": "SP",
                    "cultura": cultura,
                    "valor_producao_mil_reais": valor,
                    "valor_total_estado_mil_reais": 100,
                    "participacao_valor_estado_percentual": participacao,
                    "ranking_no_estado": ranking,
                    "indice_concentracao_hhi": 0.58,
                    "numero_efetivo_culturas": 1.72,
                }
                for cultura, valor, participacao, ranking in (
                    ("Arroz (em casca)", 70, 70, 1),
                    ("Milho (em grão)", 30, 30, 2),
                )
            ]
        ),
        "municipios_maior_expansao_area_plantada": pd.DataFrame(
            [
                {
                    "ranking": 1,
                    "codigo_municipio_ibge": "1001",
                    "municipio": "Alpha",
                    "area_plantada_2000_hectares": 10,
                    "area_plantada_2025_hectares": 20,
                    "crescimento_area_hectares": 10,
                    "crescimento_area_percentual": 100,
                }
            ]
        ),
        "municipios_maior_aumento_quantidade_produzida_2000_2025": pd.DataFrame(
            [
                {
                    "ranking_2025": 1,
                    "codigo_municipio_ibge": "1001",
                    "municipio": "Alpha",
                    "quantidade_2000_toneladas": 10,
                    "quantidade_2025_toneladas": 30,
                    "aumento_quantidade_toneladas": 20,
                }
            ]
        ),
        "ranking_municipios_evolucao_rendimento_agregado_2000_2025": pd.DataFrame(
            [
                {
                    "ranking": 1,
                    "codigo_municipio_ibge": "1001",
                    "municipio": "Alpha",
                    "uf": "SP",
                    "rendimento_2000_kg_por_hectare": 1000,
                    "rendimento_2025_kg_por_hectare": 1500,
                    "aumento_rendimento_kg_por_hectare": 500,
                    "aumento_rendimento_percentual": 50,
                }
            ]
        ),
        "variacao_percentual_quantidade_produzida_por_cultura_2024_2025": pd.DataFrame(
            [
                {"cultura": "Arroz (em casca)", "variacao_percentual": 10},
                {"cultura": "Milho (em grão)", "variacao_percentual": -5},
            ]
        ),
        "diferenca_area_plantada_colhida_por_estado_2025": pd.DataFrame(
            [
                {
                    "uf": "SP",
                    "area_plantada_total_hectares": 20,
                    "area_colhida_total_hectares": 15,
                    "diferenca_area_plantada_colhida_hectares": 5,
                }
            ]
        ),
        "ranking_valor_bruto_por_hectare_cultura_2025": pd.DataFrame(
            [
                {
                    "cultura": "Arroz (em casca)",
                    "ranking_na_cultura": 1,
                    "codigo_municipio_ibge": "1001",
                    "municipio": "Alpha",
                    "uf": "SP",
                    "valor_producao_mil_reais": 20,
                    "area_colhida_hectares": 10,
                    "valor_bruto_por_hectare_mil_reais": 2,
                }
            ]
        ),
        "ranking_aumento_rendimento_medio_por_cultura_2000_2025": pd.DataFrame(
            [
                {
                    "ranking_aumento": 1,
                    "cultura": "Arroz (em casca)",
                    "rendimento_2000_kg_por_hectare": 1000,
                    "rendimento_2025_kg_por_hectare": 1500,
                    "aumento_rendimento_kg_por_hectare": 500,
                    "aumento_percentual": 50,
                }
            ]
        ),
        "expansao_area_sem_aumento_producao_2000_2025": pd.DataFrame(
            columns=[
                "codigo_municipio_ibge",
                "municipio",
                "uf",
                "area_plantada_2000_hectares",
                "area_plantada_2025_hectares",
                "aumento_area_hectares",
                "quantidade_2000_toneladas",
                "quantidade_2025_toneladas",
                "variacao_quantidade_toneladas",
            ]
        ),
        "percentual_area_plantada_colhida_em_2025": pd.DataFrame(
            [
                {
                    "area_plantada_total_hectares": 100,
                    "area_colhida_total_hectares": 70,
                    "area_nao_colhida_total_hectares": 30,
                    "percentual_area_plantada_colhida": 70,
                    "percentual_area_plantada_nao_colhida": 30,
                }
            ]
        ),
        "ranking_valor_da_producao_muncipio_por_cultura": pd.DataFrame(
            [
                {
                    "cultura": "Arroz (em casca)",
                    "codigo_municipio_ibge": "1001",
                    "municipio": "Alpha",
                    "uf": "SP",
                    "valor_total_producao_mil_reais": 20,
                }
            ]
        ),
        "20_municipios_maiores_produtores_em_2025": pd.DataFrame(
            [
                {
                    "ranking": 1,
                    "codigo_municipio_ibge": "1001",
                    "municipio": "Alpha",
                    "valor_total_producao_mil_reais": 20,
                    "quantidade_total_toneladas": 10,
                }
            ]
        ),
    }


def test_relatorio_gera_html_tem_metricas_graficos_e_rodape(tmp_path, monkeypatch, capsys):
    dados = _marts_sinteticos()
    caminho = tmp_path / "saida" / "relatorio.html"
    caminho.parent.mkdir()
    monkeypatch.setattr(relatorio, "RAIZ", tmp_path)
    monkeypatch.setattr(relatorio, "SAIDA", caminho)
    monkeypatch.setattr(painel, "ler", lambda: dados)
    monkeypatch.chdir(tmp_path)

    relatorio.main()

    html = caminho.read_text(encoding="utf-8")
    assert caminho.is_file()
    assert html.count('class="card"') == 13
    assert 'id="g01"' in html
    assert 'id="g10"' in html
    assert "Dados de " in html
    assert "Arquivo gerado:" in capsys.readouterr().out


def test_gerar_relatorio_em_execucoes_deterministicas_muda_so_rodape():
    dados = _marts_sinteticos()

    primeira = relatorio.gerar_relatorio(dados, datetime(2026, 11, 2, 10, 0))
    segunda = relatorio.gerar_relatorio(dados, datetime(2026, 11, 2, 10, 1))

    assert primeira.replace("Dados de 02/11/2026 10:00", "Dados de <rodape>") == segunda.replace(
        "Dados de 02/11/2026 10:01", "Dados de <rodape>"
    )
    assert len(primeira.encode("utf-8")) < 200 * 1024
