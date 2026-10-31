"""Abre a interface web da extensão UI do DuckDB para o banco do projeto.

O caminho é relativo ao próprio arquivo para permitir execução a partir de
qualquer diretório. A existência do banco é verificada antes da conexão porque
abrir um caminho inexistente com DuckDB criaria um banco vazio, confundindo a
falta de ingestão com dados ausentes.

A extensão é instalada/carregada e inicia o servidor local em
http://localhost:4213. O processo permanece vivo enquanto a conexão serve a
interface; Ctrl+C encerra o loop e fecha a conexão para liberar o lock do
banco. A ingestão não é importada nem iniciada por este módulo.
O stdout usa UTF-8 para que a URL e as instruções sejam exibidas corretamente
em terminais Windows configurados com outra codificação padrão.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import duckdb


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    caminho_banco = Path(__file__).resolve().parent / "agrodata.duckdb"
    if not caminho_banco.is_file():
        print(
            f"Banco não encontrado em {caminho_banco}. "
            "Execute a ingestão antes de abrir a interface.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    con = duckdb.connect(str(caminho_banco))
    try:
        con.execute("INSTALL ui").fetchall()
        con.execute("LOAD ui").fetchall()
        con.execute("CALL start_ui()").fetchall()
        print("Interface disponível em http://localhost:4213")
        print("Ctrl+C para encerrar")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        con.close()


if __name__ == "__main__":
    main()
