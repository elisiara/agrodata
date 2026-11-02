-- 14. Evolução do rendimento agregado por município entre 2000 e 2025.
-- Cruza quantidade produzida e área colhida e calcula toneladas convertidas
-- em quilos por hectare (kg/ha), usando a área como ponderador implícito.
-- O agregado das sete culturas pode variar com a composição de culturas de
-- cada município; não deve ser interpretado como rendimento de uma cultura
-- específica. Considera somente registros MU e exige dados nos dois anos.
-- Lista os vinte maiores aumentos percentuais entre municípios com rendimento
-- inicial positivo e aumento efetivo.
-- Grão das CTEs e do resultado:
-- quantidade_por_municipio_ano: município × ano (2000 ou 2025).
-- area_colhida_por_municipio_ano: município × ano (2000 ou 2025).
-- rendimento_por_municipio_ano: município × ano com rendimento calculado.
-- comparacao: município com dados de rendimento nos dois anos.
-- variacao: município com rendimento inicial positivo e aumento efetivo.
-- Resultado final: município entre os 20 maiores aumentos percentuais.

WITH quantidade_por_municipio_ano AS (
    SELECT
        codigo_municipio_ibge,
        ano,
        COALESCE(algodao_herbaceo_em_caroco, 0)
      + COALESCE(arroz_em_casca, 0)
      + COALESCE(cafe_em_grao_total, 0)
      + COALESCE(feijao_em_grao_total, 0)
      + COALESCE(milho_em_grao_total, 0)
      + COALESCE(soja_em_grao_total, 0)
      + COALESCE(trigo_em_grao_total, 0) AS quantidade_total_toneladas
    FROM refined.quantidade_produzida
    WHERE nivel = 'MU'
      AND ano IN (2000, 2025)
),
area_colhida_por_municipio_ano AS (
    SELECT
        codigo_municipio_ibge,
        ano,
        COALESCE(algodao_herbaceo_em_caroco, 0)
      + COALESCE(arroz_em_casca, 0)
      + COALESCE(cafe_em_grao_total, 0)
      + COALESCE(feijao_em_grao_total, 0)
      + COALESCE(milho_em_grao_total, 0)
      + COALESCE(soja_em_grao_total, 0)
      + COALESCE(trigo_em_grao_total, 0) AS area_colhida_total_hectares
    FROM refined.area_colhida
    WHERE nivel = 'MU'
      AND ano IN (2000, 2025)
),
rendimento_por_municipio_ano AS (
    SELECT
        q.codigo_municipio_ibge,
        q.ano,
        q.quantidade_total_toneladas,
        a.area_colhida_total_hectares,
        1000.0 * q.quantidade_total_toneladas
            / NULLIF(a.area_colhida_total_hectares, 0)
            AS rendimento_agregado_kg_por_hectare
    FROM quantidade_por_municipio_ano AS q
    JOIN area_colhida_por_municipio_ano AS a
      ON a.codigo_municipio_ibge = q.codigo_municipio_ibge
     AND a.ano = q.ano
),
comparacao AS (
    SELECT
        codigo_municipio_ibge,
        MAX(quantidade_total_toneladas) FILTER (WHERE ano = 2000)
            AS quantidade_2000_toneladas,
        MAX(quantidade_total_toneladas) FILTER (WHERE ano = 2025)
            AS quantidade_2025_toneladas,
        MAX(area_colhida_total_hectares) FILTER (WHERE ano = 2000)
            AS area_colhida_2000_hectares,
        MAX(area_colhida_total_hectares) FILTER (WHERE ano = 2025)
            AS area_colhida_2025_hectares,
        MAX(rendimento_agregado_kg_por_hectare) FILTER (WHERE ano = 2000)
            AS rendimento_2000_kg_por_hectare,
        MAX(rendimento_agregado_kg_por_hectare) FILTER (WHERE ano = 2025)
            AS rendimento_2025_kg_por_hectare
    FROM rendimento_por_municipio_ano
    GROUP BY codigo_municipio_ibge
    HAVING COUNT(DISTINCT ano) = 2
),
variacao AS (
    SELECT
        *,
        rendimento_2025_kg_por_hectare - rendimento_2000_kg_por_hectare
            AS aumento_rendimento_kg_por_hectare,
        100.0 * (
            rendimento_2025_kg_por_hectare - rendimento_2000_kg_por_hectare
        ) / NULLIF(rendimento_2000_kg_por_hectare, 0)
            AS aumento_rendimento_percentual
    FROM comparacao
    WHERE rendimento_2000_kg_por_hectare > 0
      AND rendimento_2025_kg_por_hectare
            > rendimento_2000_kg_por_hectare
)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY aumento_rendimento_percentual DESC, c.codigo_municipio_ibge
    ) AS ranking,
    c.codigo_municipio_ibge,
    m.municipio_ibge AS municipio,
    m.uf,
    c.quantidade_2000_toneladas,
    c.quantidade_2025_toneladas,
    c.area_colhida_2000_hectares,
    c.area_colhida_2025_hectares,
    c.rendimento_2000_kg_por_hectare,
    c.rendimento_2025_kg_por_hectare,
    c.aumento_rendimento_kg_por_hectare,
    c.aumento_rendimento_percentual
FROM variacao AS c
JOIN refined.municipio AS m
  ON m.codigo_municipio_ibge = c.codigo_municipio_ibge
ORDER BY aumento_rendimento_percentual DESC, c.codigo_municipio_ibge
LIMIT 20;
