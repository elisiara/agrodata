"""Transforma as seis tabelas do schema raw para o schema refined.

As tabelas de saída usam os nomes e tipos definidos no mapa da especificação,
pois esse vocabulário e essas chaves serão usados nos JOINs e cálculos
posteriores. As colunas de medida continuam wide: não são criadas colunas
adicionais de valor original ou status. O significado dos símbolos é aplicado
diretamente às medidas refinadas, enquanto raw preserva os CSVs e os valores
recebidos para auditoria.

As conversões e validações numéricas são executadas pelo DuckDB para não
carregar as tabelas em memória. Valores inesperados causam erro com tabela,
coluna e amostra, porque transformá-los silenciosamente em NULL ocultaria a
diferença entre dado ausente e falha de conversão. Valores nulos de origem
continuam nulos; `-` representa zero; `...`, `..` e `X` representam NULL.
Texto vazio ou composto apenas por espaços também representa NULL, conforme a
convenção de célula vazia, sem alterar o valor armazenado na camada raw.

Duplicatas de linha inteira são reduzidas a uma ocorrência e contabilizadas.
Se uma chave se repetir com conteúdo diferente, a transformação para, pois
escolher uma versão apagaria informação. Nenhuma linha é removida por conter
nulos e raw nunca é alterado.

As seis tabelas de entrada são verificadas antes de escrever em refined para
evitar uma transformação parcial causada por entrada ausente. As tabelas são
recriadas em cada execução e as contagens e nulos impressos são consultados no
banco. O stdout usa UTF-8 para exibir acentos corretamente no Windows.
"""

from __future__ import annotations

import sys
from typing import Final

import duckdb

from pipeline.db import conectar, criar_schema

SCHEMA_RAW: Final = "raw"
SCHEMA_REFINED: Final = "refined"
SIMBOLOS_NULOS: Final = ("", "...", "..", "X")

COLUNAS_MEDIDA: Final = (
    ("Algodão herbáceo (em caroço)", "algodao_herbaceo_em_caroco"),
    ("Arroz (em casca)", "arroz_em_casca"),
    ("Café (em grão) Total", "cafe_em_grao_total"),
    ("Feijão (em grão)", "feijao_em_grao_total"),
    ("Milho (em grão)", "milho_em_grao_total"),
    ("Soja (em grão)", "soja_em_grao_total"),
    ("Trigo (em grão)", "trigo_em_grao_total"),
)

TABELAS_PAM: Final = (
    ("area_colhida", "area_colhida", "BIGINT"),
    (
        "area_plantada_ou_destinada_a_colheita",
        "area_plantada_ou_destinada_a_colheita",
        "BIGINT",
    ),
    ("quantidade_produzida", "quantidade_produzida", "BIGINT"),
    ("rendimento_medio_da_producao", "rendimento_medio_da_producao", "BIGINT"),
    ("valor_da_producao", "valor_da_producao", "DECIMAL(20,2)"),
)

COLUNAS_IDENTIFICADORAS_PAM: Final = (
    ("Nível", "nivel", "VARCHAR"),
    ("Cód.", "codigo_municipio_ibge", "VARCHAR"),
    ("Brasil e Município", "brasil_e_municipio", "VARCHAR"),
    ("Ano", "ano", "SMALLINT"),
)

COLUNAS_MUNICIPIO: Final = (
    ("CÓDIGO DO MUNICÍPIO - TOM", "codigo_municipio_tom", "VARCHAR"),
    ("CÓDIGO DO MUNICÍPIO - IBGE", "codigo_municipio_ibge", "VARCHAR"),
    ("MUNICÍPIO - TOM", "municipio_tom", "VARCHAR"),
    ("MUNICÍPIO - IBGE", "municipio_ibge", "VARCHAR"),
    ("UF", "uf", "VARCHAR"),
)


class ErroTransformacao(Exception):
    """Erro de dados que deve ser apresentado sem traceback ao usuário."""


def _identificador(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def _literal(valor: str) -> str:
    return "'" + valor.replace("'", "''") + "'"


def _tabela(schema: str, nome: str) -> str:
    return f"{_identificador(schema)}.{_identificador(nome)}"


def _formatar_milhar(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def _colunas_esperadas(
    colunas: tuple[tuple[str, str, str], ...],
) -> list[str]:
    return [origem for origem, _, _ in colunas]


def _validar_colunas(
    con: duckdb.DuckDBPyConnection,
    tabela_origem: str,
    colunas_esperadas: list[str],
) -> None:
    linhas = con.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = ? AND table_name = ?
        ORDER BY ordinal_position
        """,
        [SCHEMA_RAW, tabela_origem],
    ).fetchall()
    colunas_reais = [linha[0] for linha in linhas]
    if colunas_reais != colunas_esperadas:
        raise ErroTransformacao(
            f"raw.{tabela_origem}: colunas inesperadas. "
            f"Esperadas: {colunas_esperadas!r}; encontradas: {colunas_reais!r}."
        )


def _validar_numeros(
    con: duckdb.DuckDBPyConnection,
    tabela_origem: str,
    coluna_origem: str,
    tipo_destino: str,
) -> None:
    origem = _tabela(SCHEMA_RAW, tabela_origem)
    coluna = _identificador(coluna_origem)
    valor = f"TRIM({coluna})"
    locais = ", ".join(_literal(simbolo) for simbolo in SIMBOLOS_NULOS)
    invalido = con.execute(
        f"""
        SELECT DISTINCT {coluna}
        FROM {origem}
        WHERE {coluna} IS NOT NULL
          AND {valor} <> '-'
          AND {valor} NOT IN ({locais})
          AND NOT regexp_full_match({valor}, '[0-9]+')
        LIMIT 1
        """
    ).fetchone()
    if invalido is not None:
        raise ErroTransformacao(
            f"raw.{tabela_origem}.{coluna_origem}: valor numérico inesperado "
            f"{invalido[0]!r}."
        )

    try:
        con.execute(
            f"""
            SELECT max(CAST({valor} AS {tipo_destino}))
            FROM {origem}
            WHERE regexp_full_match({valor}, '[0-9]+')
            """
        ).fetchone()
    except duckdb.Error as erro:
        amostra = con.execute(
            f"""
            SELECT {coluna}
            FROM {origem}
            WHERE regexp_full_match({valor}, '[0-9]+')
            ORDER BY length({coluna}) DESC, {coluna} DESC
            LIMIT 1
            """
        ).fetchone()
        valor = amostra[0] if amostra is not None else "desconhecido"
        raise ErroTransformacao(
            f"raw.{tabela_origem}.{coluna_origem}: não foi possível converter "
            f"{valor!r} para {tipo_destino}. {erro}"
        ) from erro


def _validar_ano(con: duckdb.DuckDBPyConnection, tabela_origem: str) -> None:
    coluna = _identificador("Ano")
    origem = _tabela(SCHEMA_RAW, tabela_origem)
    invalido = con.execute(
        f"""
        SELECT DISTINCT {coluna}
        FROM {origem}
        WHERE {coluna} IS NULL
           OR NOT regexp_full_match({coluna}, '[0-9]+')
        LIMIT 1
        """
    ).fetchone()
    if invalido is not None:
        raise ErroTransformacao(
            f"raw.{tabela_origem}.Ano: valor inesperado {invalido[0]!r}."
        )
    try:
        con.execute(f"SELECT max(CAST({coluna} AS SMALLINT)) FROM {origem}").fetchone()
    except duckdb.Error as erro:
        amostra = con.execute(
            f"""
            SELECT {coluna}
            FROM {origem}
            ORDER BY length({coluna}) DESC, {coluna} DESC
            LIMIT 1
            """
        ).fetchone()
        valor = amostra[0] if amostra is not None else "desconhecido"
        raise ErroTransformacao(
            f"raw.{tabela_origem}.Ano: não foi possível converter "
            f"{valor!r} para SMALLINT. {erro}"
        ) from erro


def _validar_chaves(
    con: duckdb.DuckDBPyConnection,
    tabela_origem: str,
    chaves: list[str],
    colunas: list[str],
) -> None:
    origem = _tabela(SCHEMA_RAW, tabela_origem)
    campos_struct = ", ".join(
        f"c{indice} := t.{_identificador(coluna)}"
        for indice, coluna in enumerate(colunas)
    )
    campos_chave = ", ".join(f"t.{_identificador(chave)}" for chave in chaves)
    conflitos = con.execute(
        f"""
        SELECT {campos_chave}
        FROM {origem} AS t
        GROUP BY {", ".join(_identificador(chave) for chave in chaves)}
        HAVING count(*) > 1
           AND count(DISTINCT struct_pack({campos_struct})) > 1
        LIMIT 5
        """
    ).fetchall()
    if not conflitos:
        return

    exemplos: list[str] = []
    for chave_valores in conflitos:
        condicoes = " AND ".join(
            f"{_identificador(chave)} IS NOT DISTINCT FROM ?" for chave in chaves
        )
        linhas = con.execute(
            f"""
            SELECT *
            FROM {origem}
            WHERE {condicoes}
            LIMIT 10
            """,
            list(chave_valores),
        ).fetchall()
        exemplos.append(f"chave={chave_valores!r}, linhas={linhas!r}")

    raise ErroTransformacao(
        f"raw.{tabela_origem}: chave repetida com conteúdo diferente "
        f"({', '.join(chaves)}). Conflitos: {'; '.join(exemplos)}"
    )


def _contagem_nulos(
    con: duckdb.DuckDBPyConnection,
    tabela_refinada: str,
    colunas: list[str],
) -> list[tuple[str, int]]:
    tabela = _tabela(SCHEMA_REFINED, tabela_refinada)
    expressoes = ", ".join(
        f"count(*) FILTER (WHERE {_identificador(coluna)} IS NULL) "
        f"AS {_identificador(f'nulo_{indice}')}"
        for indice, coluna in enumerate(colunas)
    )
    valores = con.execute(f"SELECT {expressoes} FROM {tabela}").fetchone()
    return [
        (coluna, int(quantidade))
        for coluna, quantidade in zip(colunas, valores, strict=True)
        if quantidade
    ]


def _expressao_medida(
    coluna_origem: str, coluna_destino: str, tipo_destino: str
) -> str:
    coluna = _identificador(coluna_origem)
    destino = _identificador(coluna_destino)
    valor = f"TRIM({coluna})"
    locais = ", ".join(_literal(simbolo) for simbolo in SIMBOLOS_NULOS)
    return (
        f"CASE WHEN {valor} = '-' THEN CAST(0 AS {tipo_destino}) "
        f"WHEN {valor} IN ({locais}) THEN CAST(NULL AS {tipo_destino}) "
        f"ELSE CAST({valor} AS {tipo_destino}) "
        f"END AS {destino}"
    )


def _projecao_pam(tipo_medida: str) -> tuple[list[str], list[str]]:
    definicoes = list(COLUNAS_IDENTIFICADORAS_PAM)
    definicoes.extend(
        (origem, destino, tipo_medida) for origem, destino in COLUNAS_MEDIDA
    )
    projecao = []
    saidas = []
    for origem, destino, tipo in definicoes:
        saidas.append(destino)
        if tipo in {"VARCHAR", "SMALLINT"}:
            projecao.append(
                f"CAST({_identificador(origem)} AS {tipo}) AS {_identificador(destino)}"
            )
        else:
            projecao.append(_expressao_medida(origem, destino, tipo))
    return projecao, saidas


def _criar_tabela(
    con: duckdb.DuckDBPyConnection,
    tabela_origem: str,
    tabela_refinada: str,
    projecao: list[str],
) -> tuple[int, int]:
    origem = _tabela(SCHEMA_RAW, tabela_origem)
    destino = _tabela(SCHEMA_REFINED, tabela_refinada)
    linhas_entrada = int(con.execute(f"SELECT count(*) FROM {origem}").fetchone()[0])
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {destino} AS
        SELECT {", ".join(projecao)}
        FROM (SELECT DISTINCT * FROM {origem})
        """
    ).fetchall()
    linhas_saida = int(con.execute(f"SELECT count(*) FROM {destino}").fetchone()[0])
    return linhas_entrada, linhas_saida


def _verificar_tabelas_entrada(con: duckdb.DuckDBPyConnection) -> None:
    entradas = [
        "municipio",
        *(origem for origem, _, _ in TABELAS_PAM),
    ]
    existentes = {
        linha[0]
        for linha in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = ?",
            [SCHEMA_RAW],
        ).fetchall()
    }
    ausentes = [nome for nome in entradas if nome not in existentes]
    if ausentes:
        raise ErroTransformacao(
            f"Tabelas ausentes em raw: {', '.join(ausentes)}. "
            "Execute `uv run python -m pipeline.ingestao` antes."
        )


def _validar_entradas(con: duckdb.DuckDBPyConnection) -> None:
    colunas_municipio = list(_colunas_esperadas(COLUNAS_MUNICIPIO))
    _validar_colunas(con, "municipio", colunas_municipio)
    _validar_chaves(
        con,
        "municipio",
        ["CÓDIGO DO MUNICÍPIO - IBGE"],
        colunas_municipio,
    )

    for origem, _, tipo_medida in TABELAS_PAM:
        definicoes = list(COLUNAS_IDENTIFICADORAS_PAM)
        definicoes.extend(
            (coluna, nome, tipo_medida) for coluna, nome in COLUNAS_MEDIDA
        )
        colunas = [coluna for coluna, _, _ in definicoes]
        _validar_colunas(con, origem, colunas)
        _validar_chaves(con, origem, ["Cód.", "Ano"], colunas)
        _validar_ano(con, origem)
        for coluna, _, tipo in definicoes[len(COLUNAS_IDENTIFICADORAS_PAM) :]:
            _validar_numeros(con, origem, coluna, tipo)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    con = conectar()
    try:
        _verificar_tabelas_entrada(con)
        _validar_entradas(con)
        criar_schema(con, SCHEMA_REFINED)
        total = 0

        definicoes_municipio = list(COLUNAS_MUNICIPIO)
        projecao_municipio = [
            f"CAST({_identificador(origem)} AS {tipo}) AS {_identificador(destino)}"
            for origem, destino, tipo in definicoes_municipio
        ]
        entrada, saida = _criar_tabela(
            con, "municipio", "municipio", projecao_municipio
        )
        nulos = _contagem_nulos(
            con, "municipio", [destino for _, destino, _ in definicoes_municipio]
        )
        print(
            f"refined.municipio  {_formatar_milhar(entrada)} -> "
            f"{_formatar_milhar(saida)} linhas  "
            f"({_formatar_milhar(entrada - saida)} duplicatas)"
        )
        if nulos:
            resumo = ", ".join(
                f"{coluna} ({_formatar_milhar(quantidade)})"
                for coluna, quantidade in nulos
            )
            print(f"    nulos mantidos: {resumo}")
        total += saida

        for origem, destino, tipo_medida in TABELAS_PAM:
            projecao, colunas_saida = _projecao_pam(tipo_medida)
            entrada, saida = _criar_tabela(con, origem, destino, projecao)
            nulos = _contagem_nulos(con, destino, colunas_saida)
            print(
                f"refined.{destino}  {_formatar_milhar(entrada)} -> "
                f"{_formatar_milhar(saida)} linhas  "
                f"({_formatar_milhar(entrada - saida)} duplicatas)"
            )
            if nulos:
                resumo = ", ".join(
                    f"{coluna} ({_formatar_milhar(quantidade)})"
                    for coluna, quantidade in nulos
                )
                print(f"    nulos mantidos: {resumo}")
            total += saida

        print(f"Total: {_formatar_milhar(total)}")
    except ErroTransformacao as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        raise SystemExit(1) from erro
    finally:
        con.close()


if __name__ == "__main__":
    main()
