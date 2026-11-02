import duckdb
import pytest

from pipeline import transformacao


def _criar_raw(caminho, duplicata_exata=True, valor="1"):
    con = duckdb.connect(str(caminho))
    con.execute("CREATE SCHEMA raw")
    con.execute(
        "CREATE TABLE raw.municipio ("
        '"CÓDIGO DO MUNICÍPIO - TOM" VARCHAR, '
        '"CÓDIGO DO MUNICÍPIO - IBGE" VARCHAR, '
        '"MUNICÍPIO - TOM" VARCHAR, "MUNICÍPIO - IBGE" VARCHAR, UF VARCHAR)'
    )
    municipio = ("0001", "0000001", "Cidade", "Cidade", "SP")
    con.execute("INSERT INTO raw.municipio VALUES (?, ?, ?, ?, ?)", municipio)
    if duplicata_exata:
        con.execute("INSERT INTO raw.municipio VALUES (?, ?, ?, ?, ?)", municipio)

    colunas = [origem for origem, _, _ in transformacao.COLUNAS_IDENTIFICADORAS_PAM]
    colunas.extend(origem for origem, _ in transformacao.COLUNAS_MEDIDA)
    definicoes = ", ".join(f'"{coluna}" VARCHAR' for coluna in colunas)
    medidas = [valor, "-", "...", "..", "X", "", "7"]
    linha = ("MU", "0000001", "Cidade", "2025", *medidas)
    for origem, _, _ in transformacao.TABELAS_PAM:
        con.execute(f'CREATE TABLE raw."{origem}" ({definicoes})')
        placeholders = ", ".join("?" for _ in linha)
        con.execute(f'INSERT INTO raw."{origem}" VALUES ({placeholders})', linha)
        if duplicata_exata:
            con.execute(f'INSERT INTO raw."{origem}" VALUES ({placeholders})', linha)
    con.close()


def _usar_banco_temporario(monkeypatch, caminho):
    monkeypatch.setattr(transformacao, "conectar", lambda: duckdb.connect(str(caminho)))


def test_transformacao_remove_duplicatas_converte_tipos_e_preserva_nulos(
    tmp_path, monkeypatch, capsys
):
    caminho = tmp_path / "transformacao.duckdb"
    _criar_raw(caminho)
    _usar_banco_temporario(monkeypatch, caminho)

    transformacao.main()
    primeira_saida = capsys.readouterr().out
    transformacao.main()
    segunda_saida = capsys.readouterr().out

    con = duckdb.connect(str(caminho), read_only=True)
    try:
        assert (
            con.execute("SELECT count(*) FROM refined.valor_da_producao").fetchone()[0]
            == 1
        )
        assert con.execute(
            "SELECT algodao_herbaceo_em_caroco, arroz_em_casca, "
            "cafe_em_grao_total, feijao_em_grao_total, "
            "milho_em_grao_total, soja_em_grao_total, trigo_em_grao_total "
            "FROM refined.valor_da_producao"
        ).fetchone() == (1, 0, None, None, None, None, 7)
        assert (
            con.execute(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_schema = 'refined' AND table_name = 'valor_da_producao' "
                "AND column_name = 'algodao_herbaceo_em_caroco'"
            ).fetchone()[0]
            == "DECIMAL(20,2)"
        )
        assert (
            con.execute(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_schema = 'refined' AND table_name = 'area_colhida' "
                "AND column_name = 'ano'"
            ).fetchone()[0]
            == "SMALLINT"
        )
        assert (
            con.execute("SELECT count(*) FROM raw.valor_da_producao").fetchone()[0] == 2
        )
    finally:
        con.close()

    assert primeira_saida == segunda_saida
    assert "2 -> 1 linhas  (1 duplicatas)" in primeira_saida


def test_valor_numerico_invalido_encerra_sem_transformar_em_nulo(
    tmp_path, monkeypatch, capsys
):
    caminho = tmp_path / "valor-invalido.duckdb"
    _criar_raw(caminho, duplicata_exata=False, valor="1,2")
    _usar_banco_temporario(monkeypatch, caminho)

    with pytest.raises(SystemExit) as saida:
        transformacao.main()

    assert saida.value.code == 1
    assert "valor numérico inesperado '1,2'" in capsys.readouterr().err


def test_chave_repetida_com_conteudo_diferente_encerra(tmp_path, monkeypatch, capsys):
    caminho = tmp_path / "conflito.duckdb"
    _criar_raw(caminho, duplicata_exata=False)
    con = duckdb.connect(str(caminho))
    con.execute(
        "INSERT INTO raw.area_colhida VALUES "
        "('MU', '0000001', 'Cidade', '2025', '9', '-', '...', '..', 'X', '', '7')"
    )
    con.close()
    _usar_banco_temporario(monkeypatch, caminho)

    with pytest.raises(SystemExit) as saida:
        transformacao.main()

    assert saida.value.code == 1
    erro = capsys.readouterr().err
    assert "chave repetida com conteúdo diferente" in erro
    assert "0000001" in erro


def test_tabelas_raw_ausentes_sao_listadas_antes_da_transformacao(
    tmp_path, monkeypatch, capsys
):
    caminho = tmp_path / "sem-raw.duckdb"
    duckdb.connect(str(caminho)).close()
    _usar_banco_temporario(monkeypatch, caminho)

    with pytest.raises(SystemExit) as saida:
        transformacao.main()

    assert saida.value.code == 1
    assert "Tabelas ausentes em raw" in capsys.readouterr().err
