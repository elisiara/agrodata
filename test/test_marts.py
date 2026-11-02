from pathlib import Path

import duckdb
import pandas as pd
import pytest

from pipeline import marts

RAIZ = Path(__file__).resolve().parents[1]
COLUNAS_MEDIDA = (
    "algodao_herbaceo_em_caroco",
    "arroz_em_casca",
    "cafe_em_grao_total",
    "feijao_em_grao_total",
    "milho_em_grao_total",
    "soja_em_grao_total",
    "trigo_em_grao_total",
)


def _valores_municipais(tabela, codigo, ano):
    indice = {"2000": 0, "2024": 1, "2025": 2}[str(ano)]
    if tabela == "valor_da_producao":
        bases = {"1001": (1, 2, 10), "1002": (3, 5, 7)}
        return [bases[codigo][indice] * (posicao + 1) for posicao in range(7)]
    if tabela == "quantidade_produzida":
        bases = {"1001": (1, 1, 3), "1002": (1, 1, 2)}
        return [bases[codigo][indice]] * 7
    if tabela == "area_plantada_ou_destinada_a_colheita":
        bases = {"1001": (1, 1, 2), "1002": (2, 2, 2)}
        return [bases[codigo][indice]] * 7
    if tabela == "area_colhida":
        bases = {"1001": (1, 1, 2), "1002": (2, 2, 2)}
        return [bases[codigo][indice]] * 7
    bases = {"1001": (1, 2, 3), "1002": (2, 3, 4)}
    return [bases[codigo][indice]] * 7


def _valores_brasil(tabela, ano):
    if tabela == "quantidade_produzida":
        return {
            2000: [0, 5, 10, 15, 20, 25, 30],
            2024: [0, 10, 20, 30, 40, 50, 60],
            2025: [0, 20, 40, 60, 80, 100, 120],
        }[ano]
    if tabela == "area_plantada_ou_destinada_a_colheita":
        return [10 * (indice + 1) for indice in range(7)]
    if tabela == "area_colhida":
        return [5 * (indice + 1) for indice in range(7)]
    if tabela == "rendimento_medio_da_producao":
        return {
            2000: [0, 10, 20, 30, 40, 50, 60],
            2025: [0, 20, 40, 60, 80, 100, 120],
        }[ano]
    return {
        2000: [2 * (indice + 1) for indice in range(7)],
        2024: [5 * (indice + 1) for indice in range(7)],
        2025: [10 * (indice + 1) for indice in range(7)],
    }[ano]


def _criar_refined(con):
    con.execute("CREATE SCHEMA refined")
    con.execute(
        "CREATE TABLE refined.municipio ("
        "codigo_municipio_tom VARCHAR, codigo_municipio_ibge VARCHAR, "
        "municipio_tom VARCHAR, municipio_ibge VARCHAR, uf VARCHAR)"
    )
    con.executemany(
        "INSERT INTO refined.municipio VALUES (?, ?, ?, ?, ?)",
        [
            ("01", "1001", "Alpha", "Alpha", "SP"),
            ("02", "1002", "Beta", "Beta", "MG"),
        ],
    )

    for tabela in (
        "area_colhida",
        "area_plantada_ou_destinada_a_colheita",
        "quantidade_produzida",
        "rendimento_medio_da_producao",
        "valor_da_producao",
    ):
        tipo = "DECIMAL(20,2)" if tabela == "valor_da_producao" else "BIGINT"
        medidas = ", ".join(f'"{coluna}" {tipo}' for coluna in COLUNAS_MEDIDA)
        con.execute(
            f'CREATE TABLE refined."{tabela}" (nivel VARCHAR, '
            f"codigo_municipio_ibge VARCHAR, brasil_e_municipio VARCHAR, "
            f"ano SMALLINT, {medidas})"
        )
        anos = (
            (2000, 2024, 2025)
            if tabela != "rendimento_medio_da_producao"
            else (2000, 2025)
        )
        for codigo, nome in (("1001", "Alpha"), ("1002", "Beta")):
            for ano in anos:
                # Cada cidade/ano é uma observação sintética; Alpha expande área,
                # Beta não, e os valores distintos permitem conferir rankings.
                valores = _valores_municipais(tabela, codigo, ano)
                con.execute(
                    f'INSERT INTO refined."{tabela}" VALUES '
                    f"('MU', ?, ?, ?, {', '.join('?' for _ in range(7))})",
                    [codigo, nome, ano, *valores],
                )
        if tabela != "area_plantada_ou_destinada_a_colheita":
            # As linhas BR verificam que as consultas nacionais não somam
            # novamente os totais municipais.
            for ano in anos:
                valores = _valores_brasil(tabela, ano)
                con.execute(
                    f'INSERT INTO refined."{tabela}" VALUES '
                    f"('BR', '', 'Brasil', ?, {', '.join('?' for _ in range(7))})",
                    [ano, *valores],
                )
        else:
            for ano in anos:
                valores = _valores_brasil(tabela, ano)
                con.execute(
                    f'INSERT INTO refined."{tabela}" VALUES '
                    f"('BR', '', 'Brasil', ?, {', '.join('?' for _ in range(7))})",
                    [ano, *valores],
                )


def _resultado(tmp_path, nome_arquivo):
    con = duckdb.connect(str(tmp_path / "consulta.duckdb"))
    _criar_refined(con)
    sql = (RAIZ / "sql" / "marts" / nome_arquivo).read_text(encoding="utf-8")
    resultado = con.execute(sql).fetchdf()
    con.close()
    return resultado


def _preparar_db_e_marts(tmp_path):
    caminho = tmp_path / "materializacao.duckdb"
    con = duckdb.connect(str(caminho))
    _criar_refined(con)
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.anterior AS SELECT 99 AS valor")
    con.close()
    return caminho


def _patch_caminhos(monkeypatch, tmp_path, caminho_banco, pasta_sql):
    monkeypatch.setattr(marts, "PASTA_MARTS", pasta_sql)
    monkeypatch.setattr(marts, "conectar", lambda: duckdb.connect(str(caminho_banco)))


def test_mart_01_escolhe_lider_por_cultura_e_ignora_brasil(tmp_path):
    dados = _resultado(
        tmp_path, "01_ranking_valor_da_producao_muncipio_por_cultura.sql"
    )

    assert len(dados) == 7
    assert set(dados["cultura"]) == {
        "Algodão herbáceo (em caroço)",
        "Arroz (em casca)",
        "Café (em grão) Total",
        "Feijão (em grão)",
        "Milho (em grão)",
        "Soja (em grão)",
        "Trigo (em grão)",
    }
    assert set(dados["codigo_municipio_ibge"]) == {"1002"}
    assert dados["valor_total_producao_mil_reais"].tolist() == [
        float(15 * indice) for indice in range(1, 8)
    ]


def test_mart_02_limita_top_20_e_soma_as_culturas_de_2025(tmp_path):
    con = duckdb.connect(str(tmp_path / "consulta-top20.duckdb"))
    _criar_refined(con)
    # Estes municípios excedentes provam o limite de 20 e o desempate por código.
    candidatos = [
        (f"3000{indice:02}", f"Extra {indice}", pontuacao)
        for indice, pontuacao in enumerate(range(30, 13, -1))
    ]
    candidatos.extend([("2001", "Empate A", 13), ("2002", "Empate B", 13)])
    for codigo, nome, pontuacao in candidatos:
        con.execute(
            "INSERT INTO refined.municipio VALUES (?, ?, ?, ?, ?)",
            (codigo, codigo, nome, nome, "SP"),
        )
        for tabela in ("valor_da_producao", "quantidade_produzida"):
            tipo = tabela
            valores = [pontuacao] * 7
            con.execute(
                f'INSERT INTO refined."{tipo}" VALUES '
                f"('MU', ?, ?, 2025, {', '.join('?' for _ in range(7))})",
                [codigo, nome, *valores],
            )
    sql = (
        RAIZ / "sql" / "marts" / "02_20_municipios_maiores_produtores_em_2025.sql"
    ).read_text(encoding="utf-8")
    dados = con.execute(sql).fetchdf()
    con.close()

    assert len(dados) == 20
    assert dados.loc[0, "municipio"] == "Alpha"
    assert dados.loc[0, "valor_total_producao_mil_reais"] == 280
    assert dados.loc[0, "quantidade_total_toneladas"] == 21
    assert dados["ranking"].tolist() == list(range(1, 21))
    assert dados.iloc[-1]["codigo_municipio_ibge"] == "2001"


def test_mart_03_calcula_expansao_e_percentual_sobre_2000(tmp_path):
    dados = _resultado(tmp_path, "03_municipios_maior_expansao_area_plantada.sql")

    assert dados["municipio"].tolist() == ["Alpha"]
    assert dados.loc[0, "crescimento_area_hectares"] == 7
    assert dados.loc[0, "crescimento_area_percentual"] == 100


def test_mart_04_calcula_variacao_nacional_e_base_zero_fica_nula(tmp_path):
    dados = _resultado(
        tmp_path,
        "04_variacao_percentual_quantidade_produzida_por_cultura_2024_2025.sql",
    )

    assert len(dados) == 7
    primeira = dados.loc[dados["quantidade_2024_toneladas"].eq(0)].iloc[0]
    assert pd.isna(primeira["variacao_percentual"])
    assert (
        dados.loc[
            dados["quantidade_2024_toneladas"].gt(0), "variacao_percentual"
        ].tolist()
        == [100.0] * 6
    )


def test_mart_05_soma_areas_e_calcula_percentuais_complementares(tmp_path):
    dados = _resultado(
        tmp_path, "05_percentual_area_plantada_colhida_em_2025.sql"
    ).iloc[0]

    assert dados["area_plantada_total_hectares"] == 280
    assert dados["area_colhida_total_hectares"] == 140
    assert dados["area_nao_colhida_total_hectares"] == 140
    assert dados["percentual_area_plantada_colhida"] == 50
    assert dados["percentual_area_plantada_nao_colhida"] == 50


def test_mart_06_agrega_diferenca_de_areas_por_estado(tmp_path):
    dados = _resultado(
        tmp_path, "06_diferenca_area_plantada_colhida_por_estado_2025.sql"
    ).set_index("uf")

    assert dados.loc["SP", "area_plantada_total_hectares"] == 14
    assert dados.loc["SP", "area_colhida_total_hectares"] == 14
    assert dados.loc["MG", "diferenca_area_plantada_colhida_hectares"] == 0


def test_mart_07_ordena_aumentos_e_exige_ambos_os_anos(tmp_path):
    dados = _resultado(
        tmp_path,
        "07_municipios_maior_aumento_quantidade_produzida_2000_2025.sql",
    )

    assert dados["municipio"].tolist() == ["Alpha", "Beta"]
    assert dados["aumento_quantidade_toneladas"].tolist() == [14, 7]
    assert dados["ranking_2025"].tolist() == [1, 2]


def test_mart_08_calcula_lag_por_cultura_e_primeiro_ano_sem_anterior(tmp_path):
    dados = _resultado(tmp_path, "08_evolucao_valor_producao_por_cultura_2000_2025.sql")
    cultura = dados.loc[dados["cultura"].eq("Arroz (em casca)")].set_index("ano")

    assert len(dados) == 21
    assert pd.isna(cultura.loc[2000, "valor_ano_anterior_mil_reais"])
    assert cultura.loc[2025, "valor_ano_anterior_mil_reais"] == 10
    assert cultura.loc[2025, "variacao_valor_mil_reais"] == 10
    assert cultura.loc[2025, "variacao_percentual"] == 100


def test_mart_09_retorna_apenas_area_maior_sem_aumento_de_producao(tmp_path):
    dados = _resultado(tmp_path, "09_expansao_area_sem_aumento_producao_2000_2025.sql")

    assert dados.empty


def test_mart_10_calcula_participacao_por_estado_em_cada_ano(tmp_path):
    dados = _resultado(
        tmp_path,
        "10_distribuicao_geografica_producao_por_estado_2000_2025.sql",
    )
    ano_2025 = dados.loc[dados["ano"].eq(2025)].set_index("uf")

    assert len(dados) == 4
    assert ano_2025.loc["SP", "quantidade_produzida_toneladas"] == 21
    assert ano_2025.loc["MG", "quantidade_produzida_toneladas"] == 14
    assert ano_2025.loc["SP", "participacao_nacional_percentual"] == 60
    assert ano_2025.loc["MG", "participacao_nacional_percentual"] == 40


def test_mart_11_calcula_aumento_de_rendimento_e_descarta_nivel_municipal(
    tmp_path,
):
    dados = _resultado(
        tmp_path,
        "11_ranking_aumento_rendimento_medio_por_cultura_2000_2025.sql",
    )

    assert len(dados) == 7
    assert (
        dados.loc[dados["ranking_aumento"].eq(1), "cultura"].iloc[0]
        == "Arroz (em casca)"
    )
    assert (
        dados.loc[dados["rendimento_2000_kg_por_hectare"].eq(0), "aumento_percentual"]
        .isna()
        .all()
    )
    assert pd.isna(dados.iloc[-1]["aumento_percentual"])


def test_mart_12_calcula_totais_e_escalas_convertidas_do_brasil(tmp_path):
    dados = _resultado(tmp_path, "12_resumo_totais_2025.sql").iloc[0]

    assert dados["receita_producao_mil_reais"] == 280
    assert dados["volume_total_toneladas"] == 420
    assert dados["area_total_hectares"] == 140
    assert dados["rendimento_medio_kg_por_hectare"] == 3000
    assert round(dados["valor_producao_bilhoes_reais"], 8) == 0.00028
    assert round(dados["volume_milhoes_toneladas"], 8) == 0.00042
    assert round(dados["area_milhoes_hectares"], 8) == 0.00014
    assert dados["rendimento_toneladas_por_hectare"] == 3


def test_mart_13_calcula_valor_bruto_por_hectare_e_ranking(tmp_path):
    dados = _resultado(
        tmp_path,
        "13_ranking_valor_bruto_por_hectare_cultura_2025.sql",
    )

    assert len(dados) == 14
    assert (
        dados.loc[dados["cultura"].eq("Arroz (em casca)")].iloc[0]["municipio"]
        == "Alpha"
    )
    assert (
        dados.loc[dados["cultura"].eq("Arroz (em casca)")].iloc[0][
            "valor_bruto_por_hectare_mil_reais"
        ]
        == 10
    )


def test_mart_14_filtra_aumento_de_rendimento_e_calcula_percentual(tmp_path):
    dados = _resultado(
        tmp_path,
        "14_ranking_municipios_evolucao_rendimento_agregado_2000_2025.sql",
    )

    assert dados["municipio"].tolist() == ["Beta", "Alpha"]
    assert dados["aumento_rendimento_percentual"].tolist() == [100, 50]
    assert dados["ranking"].tolist() == [1, 2]


def test_mart_15_calcula_participacoes_hhi_e_numero_efetivo(tmp_path):
    dados = _resultado(
        tmp_path,
        "15_concentracao_valor_producao_por_cultura_estado_2025.sql",
    )
    sp = dados.loc[dados["uf"].eq("SP")]

    assert len(sp) == 7
    assert round(sp["participacao_valor_estado_percentual"].sum(), 8) == 100
    assert round(sp.iloc[0]["indice_concentracao_hhi"], 8) == round(5 / 28, 8)
    assert round(sp.iloc[0]["numero_efetivo_culturas"], 8) == 5.6


def test_marts_materializa_sql_e_remove_tabela_quando_arquivo_some(
    tmp_path, monkeypatch, capsys
):
    caminho = _preparar_db_e_marts(tmp_path)
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    (pasta_sql / "00_keep.sql").write_text("SELECT 1 AS valor;", encoding="utf-8")
    arquivo_removido = pasta_sql / "01_drop.sql"
    arquivo_removido.write_text("SELECT 2 AS valor", encoding="utf-8")
    _patch_caminhos(monkeypatch, tmp_path, caminho, pasta_sql)

    marts.main()
    primeira_saida = capsys.readouterr().out
    con = duckdb.connect(str(caminho), read_only=True)
    assert con.execute("SELECT valor FROM marts.keep").fetchone()[0] == 1
    assert con.execute("SELECT valor FROM marts.drop").fetchone()[0] == 2
    con.close()

    arquivo_removido.unlink()
    marts.main()
    segunda_saida = capsys.readouterr().out
    con = duckdb.connect(str(caminho), read_only=True)
    assert (
        con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'marts' AND table_name = 'drop'"
        ).fetchone()[0]
        == 0
    )
    con.close()
    assert "Total: 2 marts, 2 linhas" in primeira_saida
    assert segunda_saida == "✓ marts.keep 1 linhas\nTotal: 1 marts, 1 linhas\n"


def test_arquivo_sem_prefixo_e_recusado_sem_alterar_schema(
    tmp_path, monkeypatch, capsys
):
    caminho = _preparar_db_e_marts(tmp_path)
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    (pasta_sql / "00_valido.sql").write_text("SELECT 1", encoding="utf-8")
    (pasta_sql / "invalido.sql").write_text("SELECT 2", encoding="utf-8")
    _patch_caminhos(monkeypatch, tmp_path, caminho, pasta_sql)

    with pytest.raises(SystemExit) as saida:
        marts.main()

    assert saida.value.code == 1
    assert "invalido.sql" in capsys.readouterr().err
    con = duckdb.connect(str(caminho), read_only=True)
    assert con.execute("SELECT valor FROM marts.anterior").fetchone()[0] == 99
    assert (
        con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'marts' AND table_name = 'valido'"
        ).fetchone()[0]
        == 0
    )
    con.close()


def test_pasta_sem_arquivos_sql_e_recusada_sem_alterar_schema(
    tmp_path, monkeypatch, capsys
):
    caminho = _preparar_db_e_marts(tmp_path)
    pasta_sql = tmp_path / "sql-vazia"
    pasta_sql.mkdir()
    _patch_caminhos(monkeypatch, tmp_path, caminho, pasta_sql)

    with pytest.raises(SystemExit) as saida:
        marts.main()

    assert saida.value.code == 1
    assert "Nenhum arquivo SQL encontrado" in capsys.readouterr().err
    con = duckdb.connect(str(caminho), read_only=True)
    assert con.execute("SELECT valor FROM marts.anterior").fetchone()[0] == 99
    con.close()


def test_sql_ilegivel_e_reportado_sem_alterar_schema(tmp_path, monkeypatch, capsys):
    caminho = _preparar_db_e_marts(tmp_path)
    pasta_sql = tmp_path / "sql-ilegivel"
    pasta_sql.mkdir()
    (pasta_sql / "00_fonte.sql").write_bytes(b"\xff")
    _patch_caminhos(monkeypatch, tmp_path, caminho, pasta_sql)

    with pytest.raises(SystemExit) as saida:
        marts.main()

    assert saida.value.code == 1
    assert "Não foi possível ler 00_fonte.sql" in capsys.readouterr().err
    con = duckdb.connect(str(caminho), read_only=True)
    assert con.execute("SELECT valor FROM marts.anterior").fetchone()[0] == 99
    con.close()


def test_arquivos_com_nome_de_tabela_duplicado_sao_recusados(
    tmp_path, monkeypatch, capsys
):
    caminho = _preparar_db_e_marts(tmp_path)
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    (pasta_sql / "00_repetido.sql").write_text("SELECT 1", encoding="utf-8")
    (pasta_sql / "01_repetido.sql").write_text("SELECT 2", encoding="utf-8")
    _patch_caminhos(monkeypatch, tmp_path, caminho, pasta_sql)

    with pytest.raises(SystemExit) as saida:
        marts.main()

    assert saida.value.code == 1
    erro = capsys.readouterr().err
    assert "nome de tabela duplicado" in erro
    assert "00_repetido.sql" in erro
    assert "01_repetido.sql" in erro
    con = duckdb.connect(str(caminho), read_only=True)
    assert con.execute("SELECT valor FROM marts.anterior").fetchone()[0] == 99
    con.close()


def test_tabelas_refined_ausentes_sao_informadas_antes_do_rebuild(
    tmp_path, monkeypatch, capsys
):
    caminho = tmp_path / "refined-incompleto.duckdb"
    con = duckdb.connect(str(caminho))
    con.execute("CREATE SCHEMA refined")
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.anterior AS SELECT 99 AS valor")
    con.close()
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    (pasta_sql / "00_teste.sql").write_text("SELECT 1", encoding="utf-8")
    _patch_caminhos(monkeypatch, tmp_path, caminho, pasta_sql)

    with pytest.raises(SystemExit) as saida:
        marts.main()

    assert saida.value.code == 1
    erro = capsys.readouterr().err
    assert "Tabelas ausentes em refined" in erro
    assert "uv run python -m pipeline.transformacao" in erro
    con = duckdb.connect(str(caminho), read_only=True)
    assert con.execute("SELECT valor FROM marts.anterior").fetchone()[0] == 99
    con.close()


def test_mart_vazio_faz_rollback_e_preserva_schema_anterior(
    tmp_path, monkeypatch, capsys
):
    caminho = _preparar_db_e_marts(tmp_path)
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    (pasta_sql / "00_vazio.sql").write_text(
        "SELECT 1 AS valor WHERE false", encoding="utf-8"
    )
    _patch_caminhos(monkeypatch, tmp_path, caminho, pasta_sql)

    with pytest.raises(SystemExit) as saida:
        marts.main()

    assert saida.value.code == 1
    assert "Mart vazio" in capsys.readouterr().err
    con = duckdb.connect(str(caminho), read_only=True)
    assert con.execute("SELECT valor FROM marts.anterior").fetchone()[0] == 99
    con.close()


def test_erro_sql_informa_arquivo_e_reverte_materializacao(
    tmp_path, monkeypatch, capsys
):
    caminho = _preparar_db_e_marts(tmp_path)
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    (pasta_sql / "00_falha.sql").write_text(
        "SELECT * FROM inexistente", encoding="utf-8"
    )
    _patch_caminhos(monkeypatch, tmp_path, caminho, pasta_sql)

    with pytest.raises(SystemExit) as saida:
        marts.main()

    assert saida.value.code == 1
    assert "00_falha.sql" in capsys.readouterr().err
    con = duckdb.connect(str(caminho), read_only=True)
    assert con.execute("SELECT valor FROM marts.anterior").fetchone()[0] == 99
    con.close()
