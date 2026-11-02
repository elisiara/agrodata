-- 13. Ranking dos municípios com maior valor bruto da produção por hectare
-- colhido, para cada cultura em 2025.
-- Cruza o valor da produção com a área colhida pela cultura e pelo município.
-- A métrica é expressa em mil reais por hectare; não representa lucro,
-- pois não desconta custos de produção. Considera somente registros MU.
-- Retorna os dez primeiros municípios em cada cultura e exclui áreas nulas
-- ou iguais a zero, para que o indicador seja calculável.

WITH valores_por_cultura AS (
    SELECT
        codigo_municipio_ibge,
        brasil_e_municipio AS municipio,
        cultura,
        valor_producao_mil_reais
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
    WHERE v.nivel = 'MU'
      AND v.ano = 2025
),
area_por_cultura AS (
    SELECT
        codigo_municipio_ibge,
        cultura,
        area_colhida_hectares
    FROM refined.area_colhida AS a
    CROSS JOIN LATERAL (
        VALUES
            ('Algodão herbáceo (em caroço)', a.algodao_herbaceo_em_caroco),
            ('Arroz (em casca)',             a.arroz_em_casca),
            ('Café (em grão) Total',         a.cafe_em_grao_total),
            ('Feijão (em grão)',             a.feijao_em_grao_total),
            ('Milho (em grão)',              a.milho_em_grao_total),
            ('Soja (em grão)',               a.soja_em_grao_total),
            ('Trigo (em grão)',              a.trigo_em_grao_total)
    ) AS c(cultura, area_colhida_hectares)
    WHERE a.nivel = 'MU'
      AND a.ano = 2025
),
indicadores AS (
    SELECT
        v.cultura,
        v.codigo_municipio_ibge,
        v.municipio,
        m.uf,
        v.valor_producao_mil_reais,
        a.area_colhida_hectares,
        v.valor_producao_mil_reais
            / NULLIF(a.area_colhida_hectares, 0)
            AS valor_bruto_por_hectare_mil_reais
    FROM valores_por_cultura AS v
    JOIN area_por_cultura AS a
      ON a.codigo_municipio_ibge = v.codigo_municipio_ibge
     AND a.cultura = v.cultura
    JOIN refined.municipio AS m
      ON m.codigo_municipio_ibge = v.codigo_municipio_ibge
    WHERE a.area_colhida_hectares > 0
      AND v.valor_producao_mil_reais IS NOT NULL
),
ranking AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY cultura
            ORDER BY
                valor_bruto_por_hectare_mil_reais DESC,
                codigo_municipio_ibge
        ) AS posicao
    FROM indicadores
)
SELECT
    cultura,
    posicao AS ranking_na_cultura,
    codigo_municipio_ibge,
    municipio,
    uf,
    valor_producao_mil_reais,
    area_colhida_hectares,
    valor_bruto_por_hectare_mil_reais
FROM ranking
WHERE posicao <= 10
ORDER BY cultura, posicao;
