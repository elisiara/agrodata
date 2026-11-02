"""Materializa os arquivos SQL em tabelas no schema marts.

Esta etapa lê somente refined e escreve somente em marts, para manter raw e
refined como camadas de entrada imutáveis. O schema marts é apagado e recriado
em cada execução para que tabelas cujo arquivo SQL foi removido também
desapareçam.

Cada arquivo sql/marts/NN_nome.sql produz uma tabela marts.nome. O conteúdo SQL
é executado sem alterações, exceto pela remoção de espaços e de um ponto e
vírgula finais, pois toda regra de negócio pertence ao arquivo. Os arquivos
são processados em ordem alfabética para tornar a execução e sua saída
repetíveis.

As seis tabelas de refined são verificadas antes da materialização para
orientar a execução da transformação quando faltar uma entrada. Arquivos sem
prefixo NN_ e nomes de tabela duplicados são recusados antes de executar SQL,
evitando destinos inválidos ou ambíguos. Um diretório sem arquivos também é
recusado para não substituir marts por um schema vazio por acidente.

Todo o rebuild ocorre em uma transação: qualquer erro, inclusive um mart sem
linhas, restaura o schema da última execução bem-sucedida para não deixar o
dashboard com uma camada parcial. As contagens são consultadas no banco e
formatadas com ponto como separador de milhar; stdout usa UTF-8 para exibir
corretamente o marcador ✓.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Final

import duckdb

from pipeline.db import conectar, criar_schema
from pipeline.transformacao import SCHEMA_REFINED, TABELAS_PAM

SCHEMA_MARTS: Final = "marts"
PASTA_MARTS: Final = Path(__file__).resolve().parent.parent / "sql" / "marts"
PADRAO_ARQUIVO: Final = re.compile(r"^\d{2}_(.+)\.sql$")


class ErroMarts(Exception):
    """Falha esperada de validação ou materialização da camada marts."""


def _identificador(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def _tabela(schema: str, nome: str) -> str:
    return f"{_identificador(schema)}.{_identificador(nome)}"


def _formatar_milhar(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def _tabelas_refined_ausentes(con: duckdb.DuckDBPyConnection) -> list[str]:
    esperadas = [
        "municipio",
        *(destino for _, destino, _ in TABELAS_PAM),
    ]
    existentes = {
        linha[0]
        for linha in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = ?",
            [SCHEMA_REFINED],
        ).fetchall()
    }
    return [nome for nome in esperadas if nome not in existentes]


def _ler_arquivos_sql() -> list[tuple[str, str, str]]:
    arquivos = sorted(
        (arquivo for arquivo in PASTA_MARTS.glob("*.sql") if arquivo.is_file()),
        key=lambda arquivo: arquivo.name,
    )
    if not arquivos:
        raise ErroMarts(f"Nenhum arquivo SQL encontrado em {PASTA_MARTS}.")

    nomes_por_tabela: dict[str, list[str]] = {}
    invalidos: list[str] = []
    identificados: list[tuple[Path, str]] = []

    for arquivo in arquivos:
        correspondencia = PADRAO_ARQUIVO.fullmatch(arquivo.name)
        if correspondencia is None:
            invalidos.append(arquivo.name)
            continue
        nome_tabela = correspondencia.group(1)
        identificados.append((arquivo, nome_tabela))
        nomes_por_tabela.setdefault(nome_tabela, []).append(arquivo.name)

    duplicados = {
        nome: nomes for nome, nomes in nomes_por_tabela.items() if len(nomes) > 1
    }
    erros: list[str] = []
    if invalidos:
        erros.append("Arquivos sem prefixo NN_: " + ", ".join(invalidos))
    if duplicados:
        detalhes = "; ".join(
            f"{nome}: {', '.join(nomes)}" for nome, nomes in sorted(duplicados.items())
        )
        erros.append(f"Arquivos com nome de tabela duplicado: {detalhes}")
    if erros:
        raise ErroMarts(" ".join(erros))

    consultas: list[tuple[str, str, str]] = []
    for arquivo, nome_tabela in identificados:
        try:
            consulta = arquivo.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError) as erro:
            raise ErroMarts(f"Não foi possível ler {arquivo.name}: {erro}") from erro
        if consulta.endswith(";"):
            consulta = consulta[:-1].rstrip()
        consultas.append((arquivo.name, nome_tabela, consulta))
    return consultas


def _materializar(
    con: duckdb.DuckDBPyConnection,
    consultas: list[tuple[str, str, str]],
) -> list[tuple[str, int]]:
    con.execute("BEGIN TRANSACTION")
    try:
        con.execute(f"DROP SCHEMA IF EXISTS {_identificador(SCHEMA_MARTS)} CASCADE")
        criar_schema(con, SCHEMA_MARTS)

        resultados: list[tuple[str, int]] = []
        for arquivo, nome_tabela, consulta in consultas:
            tabela = _tabela(SCHEMA_MARTS, nome_tabela)
            try:
                con.execute(f"CREATE TABLE {tabela} AS {consulta}")
                quantidade = int(
                    con.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]
                )
            except duckdb.Error as erro:
                raise ErroMarts(f"Falha em {arquivo}: {erro}") from erro
            if quantidade == 0:
                raise ErroMarts(f"Mart vazio em {arquivo} (marts.{nome_tabela}).")
            resultados.append((nome_tabela, quantidade))

        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return resultados


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    con = conectar()
    try:
        ausentes = _tabelas_refined_ausentes(con)
        if ausentes:
            raise ErroMarts(
                f"Tabelas ausentes em refined: {', '.join(ausentes)}. "
                "Execute `uv run python -m pipeline.transformacao`."
            )

        consultas = _ler_arquivos_sql()
        resultados = _materializar(con, consultas)
        largura = max(len(f"marts.{nome}") for nome, _ in resultados)
        for nome, quantidade in resultados:
            print(
                f"✓ {f'marts.{nome}':<{largura}} {_formatar_milhar(quantidade)} linhas"
            )
        total = sum(quantidade for _, quantidade in resultados)
        print(f"Total: {len(resultados)} marts, {_formatar_milhar(total)} linhas")
    except ErroMarts as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        raise SystemExit(1) from erro
    finally:
        con.close()


if __name__ == "__main__":
    main()
