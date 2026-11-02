import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd

from pipeline import db


def test_importar_modulo_nao_cria_banco(tmp_path):
    projeto = Path(__file__).resolve().parents[1]
    resultado = subprocess.run(
        [
            sys.executable,
            "-c",
            "import pipeline.db",
        ],
        cwd=tmp_path,
        env={"PYTHONPATH": str(projeto)},
        capture_output=True,
        text=True,
        check=True,
    )

    assert resultado.stdout == ""
    assert not (tmp_path / "agrodata.duckdb").exists()


def test_conectar_cria_banco_ancorado_na_pasta_raw(tmp_path, monkeypatch):
    pasta_raw = tmp_path / "dados" / "raw"
    pasta_raw.mkdir(parents=True)
    monkeypatch.setattr(db, "PASTA_RAW", pasta_raw)
    monkeypatch.chdir(tmp_path)

    conexao = db.conectar()
    try:
        assert (tmp_path / "dados" / "agrodata.duckdb").is_file()
        assert not (tmp_path / "agrodata.duckdb").exists()
    finally:
        conexao.close()


def test_gravar_recria_tabela_retorna_contagem_e_remove_registro(tmp_path):
    conexao = duckdb.connect(str(tmp_path / "teste.duckdb"))
    try:
        db.criar_schema(conexao, "raw")
        dados = pd.DataFrame({"codigo": ["01", "02", "03"], "valor": [1, 2, 3]})

        assert db.gravar(conexao, dados, "raw", "itens") == 3
        assert db.gravar(conexao, dados, "raw", "itens") == 3
        assert conexao.execute(
            "SELECT * FROM raw.itens ORDER BY codigo"
        ).fetchall() == [
            ("01", 1),
            ("02", 2),
            ("03", 3),
        ]
        assert (
            conexao.execute(
                "SELECT count(*) FROM duckdb_views() WHERE view_name LIKE '_dataframe_%'"
            ).fetchone()[0]
            == 0
        )
    finally:
        conexao.close()
