-- 6. Diferença entre área plantada e colhida, agrupada por estado,
-- em hectares, para 2025. Considera somente registros municipais (MU).
-- Grão das CTEs e do resultado:
-- area_plantada: município em 2025.
-- area_colhida: município em 2025.
-- Resultado final: estado (UF), agregado de seus municípios em 2025.

WITH area_plantada AS (
    SELECT
        codigo_municipio_ibge,
        COALESCE(algodao_herbaceo_em_caroco, 0)
      + COALESCE(arroz_em_casca, 0)
      + COALESCE(cafe_em_grao_total, 0)
      + COALESCE(feijao_em_grao_total, 0)
      + COALESCE(milho_em_grao_total, 0)
      + COALESCE(soja_em_grao_total, 0)
      + COALESCE(trigo_em_grao_total, 0) AS total_hectares
    FROM refined.area_plantada_ou_destinada_a_colheita
    WHERE nivel = 'MU'
      AND ano = 2025
),
area_colhida AS (
    SELECT
        codigo_municipio_ibge,
        COALESCE(algodao_herbaceo_em_caroco, 0)
      + COALESCE(arroz_em_casca, 0)
      + COALESCE(cafe_em_grao_total, 0)
      + COALESCE(feijao_em_grao_total, 0)
      + COALESCE(milho_em_grao_total, 0)
      + COALESCE(soja_em_grao_total, 0)
      + COALESCE(trigo_em_grao_total, 0) AS total_hectares
    FROM refined.area_colhida
    WHERE nivel = 'MU'
      AND ano = 2025
)
SELECT
    m.uf,
    SUM(ap.total_hectares) AS area_plantada_total_hectares,
    SUM(ac.total_hectares) AS area_colhida_total_hectares,
    SUM(ap.total_hectares) - SUM(ac.total_hectares)
        AS diferenca_area_plantada_colhida_hectares
FROM area_plantada AS ap
JOIN area_colhida AS ac
    ON ac.codigo_municipio_ibge = ap.codigo_municipio_ibge
JOIN refined.municipio AS m
    ON m.codigo_municipio_ibge = ap.codigo_municipio_ibge
GROUP BY m.uf
ORDER BY diferenca_area_plantada_colhida_hectares DESC;
