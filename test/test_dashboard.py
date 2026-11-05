import pandas as pd

import dashboard


def marts_validos():
    return {
        nome: pd.DataFrame([{coluna: 1 for coluna in colunas}])
        for nome, colunas in dashboard.COLUNAS_OBRIGATORIAS.items()
    }


def test_validar_marts_aceita_contrato_completo():
    assert dashboard.validar_marts(marts_validos()) == []


def test_validar_marts_identifica_colunas_consumidas_ausentes():
    dados = marts_validos()
    dados["resumo_totais_2025"] = dados["resumo_totais_2025"].drop(
        columns="valor_producao_bilhoes_reais"
    )
    dados["concentracao_valor_producao_por_cultura_estado_2025"] = dados[
        "concentracao_valor_producao_por_cultura_estado_2025"
    ].drop(columns=["valor_producao_mil_reais", "ranking_no_estado"])

    incompatibilidades = dashboard.validar_marts(dados)

    assert any("valor_producao_bilhoes_reais" in erro for erro in incompatibilidades)
    assert any("valor_producao_mil_reais" in erro for erro in incompatibilidades)
    assert any("ranking_no_estado" in erro for erro in incompatibilidades)


def test_validar_marts_identifica_tabela_ausente_e_tabela_vazia():
    dados = marts_validos()
    del dados["distribuicao_geografica_producao_por_estado_2000_2025"]
    dados["ranking_municipios_evolucao_rendimento_agregado_2000_2025"] = (
        dados["ranking_municipios_evolucao_rendimento_agregado_2000_2025"].iloc[:0]
    )

    incompatibilidades = dashboard.validar_marts(dados)

    assert any(
        "distribuicao_geografica_producao_por_estado_2000_2025: mart ausente" in erro
        for erro in incompatibilidades
    )
    assert any(
        "ranking_municipios_evolucao_rendimento_agregado_2000_2025: mart sem linhas"
        in erro
        for erro in incompatibilidades
    )


def test_validar_marts_exige_uma_linha_nos_resumos():
    dados = marts_validos()
    dados["resumo_totais_2025"] = pd.concat(
        [dados["resumo_totais_2025"], dados["resumo_totais_2025"]],
        ignore_index=True,
    )

    incompatibilidades = dashboard.validar_marts(dados)

    assert any(
        "resumo_totais_2025: esperada(s) 1 linha(s), recebida(s) 2" in erro
        for erro in incompatibilidades
    )
