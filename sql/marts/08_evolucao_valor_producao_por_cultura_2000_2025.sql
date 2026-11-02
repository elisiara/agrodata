-- 8. Evolução anual do valor da produção por cultura.
-- O dataset cobre 2000 a 2025; para 2000, a variação anual é NULL porque
-- não há ano anterior no intervalo disponível. Valores monetários em mil reais.
-- Grão das CTEs e do resultado:
-- valores_anuais: ano × cultura.
-- evolucao: ano × cultura, com o valor do ano anterior.
-- Resultado final: ano × cultura.

WITH valores_anuais AS (
    SELECT
        v.ano,
        c.cultura,
        c.valor_producao_mil_reais
    FROM refined.valor_da_producao AS v
    CROSS JOIN LATERAL (
        VALUES
            ('Algodão herbáceo (em caroço)', v.algodao_herbaceo_em_caroco),
            ('Arroz (em casca)',             v.arroz_em_casca),
            ('Café (em grão) Total',         v.cafe_em_grao_total),
            ('Feijão (em grão)',             v.feijao_em_grao_total),
            ('Milho (em grão)',              v.milho_em_grao_total),
            ('Soja (em grão)',               v.soja_em_grao_total),
            ('Trigo (em grão)',              v.trigo_em_grao_total)
    ) AS c(cultura, valor_producao_mil_reais)
    WHERE v.nivel = 'BR'
      AND v.ano BETWEEN 2000 AND 2025
),
evolucao AS (
    SELECT
        ano,
        cultura,
        valor_producao_mil_reais,
        LAG(valor_producao_mil_reais) OVER (
            PARTITION BY cultura
            ORDER BY ano
        ) AS valor_ano_anterior_mil_reais
    FROM valores_anuais
)
SELECT
    ano,
    cultura,
    valor_producao_mil_reais,
    valor_ano_anterior_mil_reais,
    valor_producao_mil_reais - valor_ano_anterior_mil_reais
        AS variacao_valor_mil_reais,
    100.0 * (valor_producao_mil_reais - valor_ano_anterior_mil_reais)
        / NULLIF(valor_ano_anterior_mil_reais, 0)
        AS variacao_percentual
FROM evolucao
ORDER BY ano, cultura;
