-- 11. Ranking do aumento percentual do rendimento médio por cultura,
-- comparando 2000 com 2025. Considera somente registros BR.
-- O rendimento é expresso em quilogramas por hectare.

WITH rendimento_por_cultura_ano AS (
    SELECT
        r.ano,
        c.cultura,
        c.rendimento_medio_kg_por_hectare
    FROM refined.rendimento_medio_da_producao AS r
    CROSS JOIN LATERAL (
        VALUES
            ('Algodão herbáceo (em caroço)', r.algodao_herbaceo_em_caroco),
            ('Arroz (em casca)',             r.arroz_em_casca),
            ('Café (em grão) Total',         r.cafe_em_grao_total),
            ('Feijão (em grão)',             r.feijao_em_grao_total),
            ('Milho (em grão)',              r.milho_em_grao_total),
            ('Soja (em grão)',               r.soja_em_grao_total),
            ('Trigo (em grão)',              r.trigo_em_grao_total)
    ) AS c(cultura, rendimento_medio_kg_por_hectare)
    WHERE r.nivel = 'BR'
      AND r.ano IN (2000, 2025)
),
comparacao AS (
    SELECT
        cultura,
        MAX(rendimento_medio_kg_por_hectare) FILTER (WHERE ano = 2000)
            AS rendimento_2000_kg_por_hectare,
        MAX(rendimento_medio_kg_por_hectare) FILTER (WHERE ano = 2025)
            AS rendimento_2025_kg_por_hectare
    FROM rendimento_por_cultura_ano
    GROUP BY cultura
    HAVING COUNT(DISTINCT ano) = 2
),
variacao AS (
    SELECT
        cultura,
        rendimento_2000_kg_por_hectare,
        rendimento_2025_kg_por_hectare,
        rendimento_2025_kg_por_hectare - rendimento_2000_kg_por_hectare
            AS aumento_rendimento_kg_por_hectare,
        100.0 * (
            rendimento_2025_kg_por_hectare - rendimento_2000_kg_por_hectare
        ) / NULLIF(rendimento_2000_kg_por_hectare, 0)
            AS aumento_percentual
    FROM comparacao
)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY aumento_percentual DESC NULLS LAST, cultura
    ) AS ranking_aumento,
    cultura,
    rendimento_2000_kg_por_hectare,
    rendimento_2025_kg_por_hectare,
    aumento_rendimento_kg_por_hectare,
    aumento_percentual
FROM variacao
ORDER BY aumento_percentual DESC NULLS LAST, cultura;
