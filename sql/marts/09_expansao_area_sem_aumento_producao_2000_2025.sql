-- 9. Municípios onde o aumento da área plantada entre 2000 e 2025
-- não foi acompanhado por aumento da quantidade produzida.
-- Soma as sete culturas, considera apenas registros MU e inclui a UF.

WITH area_plantada AS (
    SELECT
        codigo_municipio_ibge,
        ano,
        COALESCE(algodao_herbaceo_em_caroco, 0)
      + COALESCE(arroz_em_casca, 0)
      + COALESCE(cafe_em_grao_total, 0)
      + COALESCE(feijao_em_grao_total, 0)
      + COALESCE(milho_em_grao_total, 0)
      + COALESCE(soja_em_grao_total, 0)
      + COALESCE(trigo_em_grao_total, 0) AS total_hectares
    FROM refined.area_plantada_ou_destinada_a_colheita
    WHERE nivel = 'MU'
      AND ano IN (2000, 2025)
),
quantidade_produzida AS (
    SELECT
        codigo_municipio_ibge,
        ano,
        COALESCE(algodao_herbaceo_em_caroco, 0)
      + COALESCE(arroz_em_casca, 0)
      + COALESCE(cafe_em_grao_total, 0)
      + COALESCE(feijao_em_grao_total, 0)
      + COALESCE(milho_em_grao_total, 0)
      + COALESCE(soja_em_grao_total, 0)
      + COALESCE(trigo_em_grao_total, 0) AS total_toneladas
    FROM refined.quantidade_produzida
    WHERE nivel = 'MU'
      AND ano IN (2000, 2025)
),
totais_comparaveis AS (
    SELECT
        a.codigo_municipio_ibge,
        a.ano,
        a.total_hectares,
        q.total_toneladas
    FROM area_plantada AS a
    JOIN quantidade_produzida AS q
      ON q.codigo_municipio_ibge = a.codigo_municipio_ibge
     AND q.ano = a.ano
),
comparacao AS (
    SELECT
        codigo_municipio_ibge,
        MAX(total_hectares) FILTER (WHERE ano = 2000)
            AS area_plantada_2000_hectares,
        MAX(total_hectares) FILTER (WHERE ano = 2025)
            AS area_plantada_2025_hectares,
        MAX(total_toneladas) FILTER (WHERE ano = 2000)
            AS quantidade_2000_toneladas,
        MAX(total_toneladas) FILTER (WHERE ano = 2025)
            AS quantidade_2025_toneladas
    FROM totais_comparaveis
    GROUP BY codigo_municipio_ibge
    HAVING COUNT(DISTINCT ano) = 2
)
SELECT
    c.codigo_municipio_ibge,
    m.municipio_ibge AS municipio,
    m.uf,
    c.area_plantada_2000_hectares,
    c.area_plantada_2025_hectares,
    c.area_plantada_2025_hectares - c.area_plantada_2000_hectares
        AS aumento_area_hectares,
    c.quantidade_2000_toneladas,
    c.quantidade_2025_toneladas,
    c.quantidade_2025_toneladas - c.quantidade_2000_toneladas
        AS variacao_quantidade_toneladas
FROM comparacao AS c
JOIN refined.municipio AS m
  ON m.codigo_municipio_ibge = c.codigo_municipio_ibge
WHERE c.area_plantada_2025_hectares > c.area_plantada_2000_hectares
  AND c.quantidade_2025_toneladas <= c.quantidade_2000_toneladas
ORDER BY aumento_area_hectares DESC, c.codigo_municipio_ibge;
