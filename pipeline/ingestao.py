"""Ingestão dos CSVs originais para tabelas derivadas no schema raw.

Os arquivos de origem permanecem inalterados: cada tabela é uma representação
tabular derivada, não uma cópia byte a byte do CSV. Por isso, a etapa preserva
valores como texto e transforma somente campos vazios em nulos; conversões e
correções pertencem à etapa refined.

Os cinco arquivos PAM são lidos pelo parser CSV, pois notas podem conter
quebras de linha entre aspas. O encoding é UTF-8 explícito; o delimitador é
configurado por arquivo porque uma das fontes recebidas usa vírgula e as outras
quatro usam ponto e vírgula. O CSV GOV.BR atual é lido como Latin-1, conforme
sua codificação observada, sem regravar o original.

Cabeçalhos, rodapés e outros níveis não viram registros; BR e MU são
preservados. Os campos de ano e cultura são reorganizados em 26 registros
anuais por entidade para que cada cultura tenha uma coluna e o ano fique
explícito em outra. A validação dos cabeçalhos e das larguras evita que
arquivos inesperados sejam truncados silenciosamente.

Todos os seis arquivos são verificados antes de abrir o banco para evitar uma
ingestão parcial por ausência de entrada. Cada tabela é recriada, e a tela
mostra a contagem consultada no banco. O stdout usa UTF-8 para exibir acentos
corretamente também no Prompt de Comando do Windows.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

from pipeline.db import PASTA_RAW, conectar, criar_schema, gravar

SCHEMA = "raw"
ARQUIVO_MUNICIPIOS = "municipios_gov.csv"
COLUNAS_IDENTIFICADORAS = ("Nível", "Cód.", "Brasil e Município")
PRODUTOS = (
    "Algodão herbáceo (em caroço)",
    "Arroz (em casca)",
    "Café (em grão) Total",
    "Feijão (em grão)",
    "Milho (em grão)",
    "Soja (em grão)",
    "Trigo (em grão)",
)
ANOS_ESPERADOS = tuple(str(ano) for ano in range(2000, 2026))
LARGURA_IBGE = 185
COLUNA_INICIAL_MEDIDAS = 3

ARQUIVOS_IBGE = (
    (
        "tabela5457_area_colhida.csv",
        "area_colhida",
        "Variável - Área colhida (Hectares)",
        ";",
    ),
    (
        "tabela5457_area_plantada_ou_destinada_a_colheita.csv",
        "area_plantada_ou_destinada_a_colheita",
        "Variável - Área plantada ou destinada à colheita (Hectares)",
        ",",
    ),
    (
        "tabela5457_quantidade_produzida.csv",
        "quantidade_produzida",
        "Variável - Quantidade produzida (Toneladas)",
        ";",
    ),
    (
        "tabela5457_rendimento_medio_da_producao.csv",
        "rendimento_medio_da_producao",
        "Variável - Rendimento médio da produção (Quilogramas por Hectare)",
        ";",
    ),
    (
        "tabela5457_valor_da_producao.csv",
        "valor_da_producao",
        "Variável - Valor da produção (Mil Reais)",
        ";",
    ),
)


def _ler_mapa_anos_culturas(
    anos_brutos: list[str], culturas_brutas: list[str], caminho: Path
) -> list[tuple[str, tuple[str, ...]]]:
    if len(anos_brutos) > LARGURA_IBGE:
        raise ValueError(
            f"{caminho}: cabeçalho de anos excede {LARGURA_IBGE} campos."
        )
    if len(culturas_brutas) != LARGURA_IBGE:
        raise ValueError(
            f"{caminho}: cabeçalho de culturas tem {len(culturas_brutas)} "
            f"campos; esperado: {LARGURA_IBGE}."
        )
    if anos_brutos[:COLUNA_INICIAL_MEDIDAS] != list(COLUNAS_IDENTIFICADORAS):
        raise ValueError(f"{caminho}: identificadores inesperados no cabeçalho de anos.")

    anos_brutos.extend([""] * (LARGURA_IBGE - len(anos_brutos)))
    posicoes_de_ano = {
        COLUNA_INICIAL_MEDIDAS + indice * len(PRODUTOS)
        for indice in range(len(ANOS_ESPERADOS))
    }
    ano_atual = ""
    pares: list[tuple[str, str]] = []

    for posicao in range(COLUNA_INICIAL_MEDIDAS, LARGURA_IBGE):
        campo_ano = anos_brutos[posicao]
        if posicao in posicoes_de_ano:
            ano_esperado = ANOS_ESPERADOS[
                (posicao - COLUNA_INICIAL_MEDIDAS) // len(PRODUTOS)
            ]
            if campo_ano != ano_esperado:
                raise ValueError(
                    f"{caminho}: ano inesperado na coluna {posicao}: "
                    f"{campo_ano!r}; esperado: {ano_esperado!r}."
                )
        elif campo_ano:
            raise ValueError(
                f"{caminho}: campo de ano inesperado na coluna {posicao}: "
                f"{campo_ano!r}."
            )
        if campo_ano:
            ano_atual = campo_ano
        if not ano_atual:
            raise ValueError(
                f"{caminho}: medida na coluna {posicao} sem ano associado."
            )
        pares.append((ano_atual, culturas_brutas[posicao]))

    grupos: list[tuple[str, tuple[str, ...]]] = []
    for inicio in range(0, len(pares), len(PRODUTOS)):
        grupo = pares[inicio : inicio + len(PRODUTOS)]
        if len(grupo) != len(PRODUTOS):
            raise ValueError(f"{caminho}: grupo incompleto de culturas.")
        anos_grupo = {ano for ano, _ in grupo}
        culturas_grupo = tuple(cultura for _, cultura in grupo)
        if len(anos_grupo) != 1:
            raise ValueError(f"{caminho}: um grupo de culturas contém anos distintos.")
        if culturas_grupo != PRODUTOS:
            raise ValueError(
                f"{caminho}: culturas inesperadas no ano {grupo[0][0]}."
            )
        grupos.append((grupo[0][0], culturas_grupo))

    anos_observados = tuple(ano for ano, _ in grupos)
    if anos_observados != ANOS_ESPERADOS:
        raise ValueError(
            f"{caminho}: esperado o intervalo de 2000 a 2025; "
            f"encontrado: {anos_observados}."
        )

    pares_observados = [(ano, cultura) for ano, cultura in pares]
    if len(pares_observados) != len(set(pares_observados)):
        raise ValueError(f"{caminho}: pares (ano, cultura) duplicados.")

    return grupos


def _ler_ibge(
    caminho: Path, descricao_esperada: str, delimitador: str
) -> pd.DataFrame:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.reader(arquivo, delimiter=delimitador)
        cabecalhos = []
        for numero in range(1, 6):
            try:
                cabecalhos.append(next(leitor))
            except StopIteration as erro:
                raise ValueError(
                    f"{caminho}: faltam registros de cabeçalho; "
                    f"não foi possível ler o registro {numero}."
                ) from erro

        descricao = cabecalhos[1]
        if (
            not descricao
            or descricao[0] != descricao_esperada
            or any(descricao[1:])
        ):
            raise ValueError(
                f"{caminho}: descrição inesperada: {descricao!r}; "
                f"esperada: {descricao_esperada!r}."
            )

        cabecalho_descritivo = cabecalhos[2]
        if cabecalho_descritivo[:3] != list(COLUNAS_IDENTIFICADORAS):
            raise ValueError(
                f"{caminho}: cabeçalho identificador inesperado: "
                f"{cabecalho_descritivo!r}."
            )

        grupos = _ler_mapa_anos_culturas(
            cabecalhos[3], cabecalhos[4], caminho
        )
        colunas = [*COLUNAS_IDENTIFICADORAS, "Ano", *PRODUTOS]
        registros: list[list[str | None]] = []
        codigos_municipais: set[str] = set()
        quantidade_brasil = 0
        encontrou_rodape = False

        for numero_registro, linha in enumerate(leitor, start=6):
            if linha and linha[0].startswith("Fonte:"):
                encontrou_rodape = True
                break
            if not linha or linha[0] not in {"MU", "BR"}:
                continue
            if len(linha) != LARGURA_IBGE:
                raise ValueError(
                    f"{caminho}: registro lógico {numero_registro} tem "
                    f"{len(linha)} campos; esperado: {LARGURA_IBGE}."
                )

            nivel, codigo = linha[0], linha[1]
            if nivel == "MU":
                if not codigo.isdigit():
                    raise ValueError(
                        f"{caminho}: código municipal inválido no registro "
                        f"{numero_registro}: {codigo!r}."
                    )
                if codigo in codigos_municipais:
                    raise ValueError(
                        f"{caminho}: código municipal duplicado no registro "
                        f"{numero_registro}: {codigo!r}."
                    )
                codigos_municipais.add(codigo)
            else:
                quantidade_brasil += 1
                if quantidade_brasil > 1:
                    raise ValueError(f"{caminho}: mais de um registro BR.")

            for indice_ano, (ano, _) in enumerate(grupos):
                inicio = COLUNA_INICIAL_MEDIDAS + indice_ano * len(PRODUTOS)
                valores = [
                    valor if valor != "" else None
                    for valor in linha[inicio : inicio + len(PRODUTOS)]
                ]
                registros.append(
                    [*linha[:3], ano, *valores]
                )

        if not encontrou_rodape:
            raise ValueError(f"{caminho}: linha Fonte: não encontrada.")
        if quantidade_brasil != 1:
            raise ValueError(
                f"{caminho}: esperado um registro BR; "
                f"encontrado: {quantidade_brasil}."
            )
        if not codigos_municipais:
            raise ValueError(f"{caminho}: nenhum registro MU encontrado.")

    return pd.DataFrame(registros, columns=colunas, dtype=str)


def _ler_municipios(caminho: Path) -> pd.DataFrame:
    return pd.read_csv(
        caminho,
        sep=";",
        encoding="latin-1",
        dtype=str,
        keep_default_na=False,
        na_values=[""],
    )


def _formatar_milhar(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    arquivos = [ARQUIVO_MUNICIPIOS, *(item[0] for item in ARQUIVOS_IBGE)]
    ausentes = [nome for nome in arquivos if not (PASTA_RAW / nome).is_file()]
    if ausentes:
        print(
            f"Arquivos ausentes em {PASTA_RAW}: {', '.join(ausentes)}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    con = conectar()
    try:
        criar_schema(con, SCHEMA)
        total = 0

        municipio_df = _ler_municipios(PASTA_RAW / ARQUIVO_MUNICIPIOS)
        quantidade = gravar(con, municipio_df, SCHEMA, "municipio")
        total += quantidade
        print(f"{SCHEMA}.municipio: {_formatar_milhar(quantidade)}")

        for nome_arquivo, nome_tabela, descricao, delimitador in ARQUIVOS_IBGE:
            df = _ler_ibge(
                PASTA_RAW / nome_arquivo, descricao, delimitador
            )
            quantidade = gravar(con, df, SCHEMA, nome_tabela)
            total += quantidade
            print(f"{SCHEMA}.{nome_tabela}: {_formatar_milhar(quantidade)}")

        print(f"Total: {_formatar_milhar(total)}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
