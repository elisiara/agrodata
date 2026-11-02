"""Módulo compartilhado de acesso ao DuckDB.

Os caminhos são ancorados nesta localização, e não ao diretório corrente,
para que uma execução iniciada em outra pasta use sempre o banco do projeto.
Importar este módulo não abre nem cria o banco; cada etapa controla a própria
conexão e a fecha quando terminar.

Este módulo expõe somente PASTA_RAW, conectar, criar_schema e gravar. Ele não
conhece arquivos ou nomes de tabelas nem altera tipos, pois essas decisões
pertencem a cada etapa do pipeline.
gravar recria a tabela a cada execução para tornar a ingestão repetível,
remove o registro temporário do DataFrame e lê a contagem do próprio banco
para que a confirmação corresponda ao que foi persistido.
"""

from pathlib import Path as _Path
from uuid import uuid4 as _uuid4

import duckdb as _duckdb
import pandas as _pandas

PASTA_RAW = _Path(__file__).resolve().parent.parent / "raw"


def conectar() -> _duckdb.DuckDBPyConnection:
    """Abre o banco na raiz do projeto, criando-o se ainda não existir."""
    caminho_banco = PASTA_RAW.parent / "agrodata.duckdb"
    return _duckdb.connect(str(caminho_banco))


def criar_schema(con: _duckdb.DuckDBPyConnection, nome: str) -> None:
    """Cria o schema quando necessário."""
    schema_sql = '"' + nome.replace('"', '""') + '"'
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_sql}").fetchall()


def gravar(
    con: _duckdb.DuckDBPyConnection,
    df: _pandas.DataFrame,
    schema: str,
    tabela: str,
) -> int:
    """Recria a tabela com os dados do DataFrame e retorna sua contagem."""
    schema_sql = '"' + schema.replace('"', '""') + '"'
    tabela_sql = '"' + tabela.replace('"', '""') + '"'
    relacao = f"_dataframe_{_uuid4().hex}"
    relacao_sql = '"' + relacao + '"'
    destino = f"{schema_sql}.{tabela_sql}"

    con.register(relacao, df)
    try:
        con.execute(
            f"CREATE OR REPLACE TABLE {destino} AS SELECT * FROM {relacao_sql}"
        ).fetchall()
    finally:
        con.unregister(relacao)

    resultados = con.execute(f"SELECT count(*) FROM {destino}").fetchall()
    if not resultados:
        raise RuntimeError(f"Não foi possível contar as linhas de {destino}.")
    return int(resultados[0][0])
