-- 4. Variação anual da quantidade produzida por cultura(2024 - 2025) :
-- Variação anual da quantidade produzida de cada cultura, em percentual,
-- comparando o ano de 2025 com o anterior(2024) para a mesma unidade e
-- cultura. Resultado 7 linhas, uma para cada cultura, cada uma contendo
-- um resultado percentual que represente a variação total da quantidade
-- produzida da cultura no periodo 2024 a 2025.
-- Bucar apenas em linhas de nível "BR", descartar linhas de nível "MU"

WITH quantidade_por_cultura AS (
    SELECT
        c.cultura,
        v.ano,
        c.quantidade_toneladas
    FROM refined.quantidade_produzida AS v
    CROSS JOIN LATERAL (
        VALUES
            ('Algodão herbáceo (em caroço)', v.algodao_herbaceo_em_caroco),
            ('Arroz (em casca)',             v.arroz_em_casca),
            ('Café (em grão) Total',         v.cafe_em_grao_total),
            ('Feijão (em grão)',             v.feijao_em_grao_total),
            ('Milho (em grão)',              v.milho_em_grao_total),
            ('Soja (em grão)',               v.soja_em_grao_total),
            ('Trigo (em grão)',              v.trigo_em_grao_total)
    ) AS c(cultura, quantidade_toneladas)
    WHERE v.nivel = 'BR'
      AND v.ano IN (2024, 2025)
),
totais AS (
    SELECT
        cultura,
        MAX(quantidade_toneladas) FILTER (WHERE ano = 2024)
            AS quantidade_2024_toneladas,
        MAX(quantidade_toneladas) FILTER (WHERE ano = 2025)
            AS quantidade_2025_toneladas
    FROM quantidade_por_cultura
    GROUP BY cultura
)
SELECT
    cultura,
    quantidade_2024_toneladas,
    quantidade_2025_toneladas,
    100.0 * (quantidade_2025_toneladas - quantidade_2024_toneladas)
        / NULLIF(quantidade_2024_toneladas, 0)
        AS variacao_percentual
FROM totais
ORDER BY cultura;

-- A variação é calculada como (quantidade de 2025 − quantidade de 2024)
-- / quantidade de 2024 × 100. O resultado percentual fica NULL caso a
-- quantidade de 2024 seja nula ou zero, pois não há base válida para
-- a divisão.