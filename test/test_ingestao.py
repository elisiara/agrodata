import csv

import duckdb
import pytest

from pipeline import ingestao


def _criar_csv_ibge(caminho, descricao, delimitador):
    identificadores = list(ingestao.COLUNAS_IDENTIFICADORAS)
    culturas = list(ingestao.PRODUTOS)
    cabecalho_anos = identificadores + [""] * (ingestao.LARGURA_IBGE - 3)
    cabecalho_culturas = identificadores + culturas * len(ingestao.ANOS_ESPERADOS)
    for indice, ano in enumerate(ingestao.ANOS_ESPERADOS):
        cabecalho_anos[3 + indice * len(culturas)] = ano

    def linha(nivel, codigo, nome):
        registro = [nivel, codigo, nome]
        registro.extend(str(indice) for indice in range(ingestao.LARGURA_IBGE - 3))
        return registro

    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=delimitador)
        escritor.writerow(["Título"])
        escritor.writerow([descricao])
        escritor.writerow(identificadores + ["medida"] * (ingestao.LARGURA_IBGE - 3))
        escritor.writerow(cabecalho_anos)
        escritor.writerow(cabecalho_culturas)
        escritor.writerow(["Notas", "texto com\nquebra de linha"])
        escritor.writerow(linha("BR", "", "Brasil"))
        escritor.writerow(linha("MU", "0000001", "Município Inventado"))
        escritor.writerow(["Fonte: teste"])


def _preparar_entradas(pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / ingestao.ARQUIVO_MUNICIPIOS).write_text(
        "CÓDIGO DO MUNICÍPIO - TOM;CÓDIGO DO MUNICÍPIO - IBGE;"
        "MUNICÍPIO - TOM;MUNICÍPIO - IBGE;UF\n1;0000001;Cidade;Cidade;SP\n",
        encoding="latin-1",
    )
    for arquivo, _, descricao, delimitador in ingestao.ARQUIVOS_IBGE:
        _criar_csv_ibge(pasta / arquivo, descricao, delimitador)


def test_ingestao_grava_tabelas_com_linhas_e_valores_dos_csvs(
    tmp_path, monkeypatch, capsys
):
    pasta_raw = tmp_path / "raw"
    _preparar_entradas(pasta_raw)
    caminho_banco = tmp_path / "temporario.duckdb"
    monkeypatch.setattr(ingestao, "PASTA_RAW", pasta_raw)
    monkeypatch.setattr(
        ingestao, "conectar", lambda: duckdb.connect(str(caminho_banco))
    )

    ingestao.main()

    conexao = duckdb.connect(str(caminho_banco), read_only=True)
    try:
        assert conexao.execute("SELECT count(*) FROM raw.municipio").fetchone()[0] == 1
        assert (
            conexao.execute("SELECT count(*) FROM raw.area_colhida").fetchone()[0] == 52
        )
        assert conexao.execute(
            'SELECT "Nível", "Cód.", "Ano" FROM raw.area_colhida '
            'WHERE "Cód." = \'0000001\' ORDER BY "Ano" LIMIT 1'
        ).fetchone() == ("MU", "0000001", "2000")
        assert (
            conexao.execute(
                'SELECT "Algodão herbáceo (em caroço)" FROM raw.area_colhida '
                "WHERE \"Cód.\" = '0000001' AND \"Ano\" = '2000'"
            ).fetchone()[0]
            == "0"
        )
    finally:
        conexao.close()

    assert "raw.area_colhida: 52" in capsys.readouterr().out


def test_arquivo_de_ingestao_ausente_encerra_antes_de_abrir_banco(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(ingestao, "PASTA_RAW", tmp_path)
    monkeypatch.setattr(
        ingestao,
        "conectar",
        lambda: pytest.fail("A conexão não deve abrir antes da validação dos arquivos"),
    )

    with pytest.raises(SystemExit) as saida:
        ingestao.main()

    assert saida.value.code == 1
