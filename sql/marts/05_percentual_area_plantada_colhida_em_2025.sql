-- 5.Percentual total da área plantada que foi colhida em 2025: Calcular o valor
-- percentual total de area que foi destinada a ser plantada que foi efetivamente
-- colhida no ano de 2025, somando-se os valores de todas as culturas,
-- 'área colhida / área plantada × 100' | 'raw.area_colhida'['[cultura]']
--  + 'raw.area_plantada'['[cultura]'] .
-- Retorna os totais de área plantada e colhida, a diferença entre elas,
-- e os percentuais de área colhida e não colhida.
-- Bucar apenas em linhas de nível "BR", descartar linhas de nível "MU".
-- Grão das CTEs e do resultado:
-- area_colhida: total nacional de área colhida em 2025 (uma linha).
-- area_plantada: total nacional de área plantada em 2025 (uma linha).
-- Resultado final: total nacional de áreas em 2025 (uma linha).

WITH area_colhida AS (
    SELECT SUM(
        COALESCE(algodao_herbaceo_em_caroco, 0)
      + COALESCE(arroz_em_casca, 0)
      + COALESCE(cafe_em_grao_total, 0)
      + COALESCE(feijao_em_grao_total, 0)
      + COALESCE(milho_em_grao_total, 0)
      + COALESCE(soja_em_grao_total, 0)
      + COALESCE(trigo_em_grao_total, 0)
    ) AS total_hectares
    FROM refined.area_colhida
    WHERE nivel = 'BR'
      AND ano = 2025
),
area_plantada AS (
    SELECT SUM(
        COALESCE(algodao_herbaceo_em_caroco, 0)
      + COALESCE(arroz_em_casca, 0)
      + COALESCE(cafe_em_grao_total, 0)
      + COALESCE(feijao_em_grao_total, 0)
      + COALESCE(milho_em_grao_total, 0)
      + COALESCE(soja_em_grao_total, 0)
      + COALESCE(trigo_em_grao_total, 0)
    ) AS total_hectares
    FROM refined.area_plantada_ou_destinada_a_colheita
    WHERE nivel = 'BR'
      AND ano = 2025
)
SELECT
    area_plantada.total_hectares AS area_plantada_total_hectares,
    area_colhida.total_hectares AS area_colhida_total_hectares,
    area_plantada.total_hectares - area_colhida.total_hectares
        AS area_nao_colhida_total_hectares,
    100.0 * area_colhida.total_hectares
        / NULLIF(area_plantada.total_hectares, 0)
        AS percentual_area_plantada_colhida,
    100.0 * (
        area_plantada.total_hectares - area_colhida.total_hectares
    ) / NULLIF(area_plantada.total_hectares, 0)
        AS percentual_area_plantada_nao_colhida
FROM area_colhida
CROSS JOIN area_plantada;

-- NULLIF evita divisão por zero;
-- áreas nulas são consideradas zero no somatório.