"""Contrato de dados exigido pelo dashboard."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

COLUNAS_OBRIGATORIAS: dict[str, tuple[str, ...]] = {
    "ranking_valor_da_producao_muncipio_por_cultura": (
        "cultura",
        "municipio",
        "uf",
        "valor_total_producao_mil_reais",
    ),
    "20_municipios_maiores_produtores_em_2025": (
        "ranking",
        "municipio",
        "valor_total_producao_mil_reais",
        "quantidade_total_toneladas",
    ),
    "municipios_maior_expansao_area_plantada": (
        "ranking",
        "codigo_municipio_ibge",
        "municipio",
        "area_plantada_2000_hectares",
        "area_plantada_2025_hectares",
        "crescimento_area_hectares",
        "crescimento_area_percentual",
    ),
    "variacao_percentual_quantidade_produzida_por_cultura_2024_2025": (
        "cultura",
        "variacao_percentual",
    ),
    "percentual_area_plantada_colhida_em_2025": (
        "percentual_area_plantada_colhida",
        "percentual_area_plantada_nao_colhida",
    ),
    "diferenca_area_plantada_colhida_por_estado_2025": (
        "uf",
        "area_plantada_total_hectares",
        "area_colhida_total_hectares",
        "diferenca_area_plantada_colhida_hectares",
    ),
    "municipios_maior_aumento_quantidade_produzida_2000_2025": (
        "ranking_2025",
        "codigo_municipio_ibge",
        "municipio",
        "quantidade_2000_toneladas",
        "quantidade_2025_toneladas",
        "aumento_quantidade_toneladas",
    ),
    "evolucao_valor_producao_por_cultura_2000_2025": (
        "ano",
        "cultura",
        "valor_producao_mil_reais",
    ),
    "expansao_area_sem_aumento_producao_2000_2025": (
        "codigo_municipio_ibge",
        "municipio",
        "uf",
        "area_plantada_2000_hectares",
        "area_plantada_2025_hectares",
        "aumento_area_hectares",
        "quantidade_2000_toneladas",
        "quantidade_2025_toneladas",
        "variacao_quantidade_toneladas",
    ),
    "distribuicao_geografica_producao_por_estado_2000_2025": (
        "uf",
        "ano",
        "ranking_no_ano",
        "quantidade_produzida_toneladas",
        "participacao_nacional_percentual",
        "destaque",
    ),
    "ranking_aumento_rendimento_medio_por_cultura_2000_2025": (
        "ranking_aumento",
        "cultura",
        "rendimento_2000_kg_por_hectare",
        "rendimento_2025_kg_por_hectare",
        "aumento_rendimento_kg_por_hectare",
        "aumento_percentual",
    ),
    "resumo_totais_2025": (
        "receita_producao_mil_reais",
        "volume_total_toneladas",
        "area_total_hectares",
        "rendimento_medio_kg_por_hectare",
        "valor_producao_bilhoes_reais",
        "volume_milhoes_toneladas",
        "area_milhoes_hectares",
        "rendimento_toneladas_por_hectare",
    ),
    "ranking_valor_bruto_por_hectare_cultura_2025": (
        "cultura",
        "ranking_na_cultura",
        "municipio",
        "uf",
        "valor_producao_mil_reais",
        "area_colhida_hectares",
        "valor_bruto_por_hectare_mil_reais",
    ),
    "ranking_municipios_evolucao_rendimento_agregado_2000_2025": (
        "ranking",
        "codigo_municipio_ibge",
        "municipio",
        "uf",
        "rendimento_2000_kg_por_hectare",
        "rendimento_2025_kg_por_hectare",
        "aumento_rendimento_kg_por_hectare",
        "aumento_rendimento_percentual",
    ),
    "concentracao_valor_producao_por_cultura_estado_2025": (
        "uf",
        "cultura",
        "valor_producao_mil_reais",
        "valor_total_estado_mil_reais",
        "participacao_valor_estado_percentual",
        "ranking_no_estado",
        "indice_concentracao_hhi",
        "numero_efetivo_culturas",
    ),
}

CARDINALIDADE_EXATA: dict[str, int] = {
    "percentual_area_plantada_colhida_em_2025": 1,
    "resumo_totais_2025": 1,
}


def validar_marts(dados: Mapping[str, pd.DataFrame]) -> list[str]:
    """Valida presença, schema e cardinalidade dos marts usados no painel."""
    incompatibilidades: list[str] = []

    for nome, colunas_esperadas in COLUNAS_OBRIGATORIAS.items():
        frame = dados.get(nome)
        if frame is None:
            incompatibilidades.append(f"marts.{nome}: mart ausente")
            continue

        ausentes = sorted(set(colunas_esperadas) - set(frame.columns))
        if ausentes:
            incompatibilidades.append(
                f"marts.{nome}: colunas ausentes: {', '.join(ausentes)}"
            )

        cardinalidade_esperada = CARDINALIDADE_EXATA.get(nome)
        if cardinalidade_esperada is not None:
            if len(frame) != cardinalidade_esperada:
                incompatibilidades.append(
                    f"marts.{nome}: esperada(s) {cardinalidade_esperada} linha(s), "
                    f"recebida(s) {len(frame)}"
                )
        elif frame.empty:
            incompatibilidades.append(f"marts.{nome}: mart sem linhas")

    return incompatibilidades
