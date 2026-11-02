-- 7. Municípios com maior aumento da quantidade produzida entre 2000 e 2025.
-- Soma as sete culturas por município e ano, considera somente registros MU
-- e ordena os dez maiores aumentos pela quantidade produzida em 2025.
-- Grão das CTEs e do resultado:
-- quantidade_por_municipio_ano: município × ano (2000 ou 2025).
-- variacao_por_municipio: município com dados nos dois anos.
-- maiores_aumentos: município, com aumento calculado e posição por aumento.
-- Resultado final: município entre os 10 maiores aumentos.

WITH quantidade_por_municipio_ano AS (
    SELECT
        codigo_municipio_ibge,
        brasil_e_municipio AS municipio,
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
variacao_por_municipio AS (
    SELECT
        codigo_municipio_ibge,
        municipio,
        MAX(quantidade_total_toneladas) FILTER (WHERE ano = 2000)
            AS quantidade_2000_toneladas,
        MAX(quantidade_total_toneladas) FILTER (WHERE ano = 2025)
            AS quantidade_2025_toneladas
    FROM quantidade_por_municipio_ano
    GROUP BY codigo_municipio_ibge, municipio
    HAVING COUNT(DISTINCT ano) = 2
),
maiores_aumentos AS (
    SELECT
        *,
        quantidade_2025_toneladas - quantidade_2000_toneladas
            AS aumento_quantidade_toneladas,
        ROW_NUMBER() OVER (
            ORDER BY
                quantidade_2025_toneladas - quantidade_2000_toneladas DESC,
                codigo_municipio_ibge
        ) AS ranking_aumento
    FROM variacao_por_municipio
)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY quantidade_2025_toneladas DESC, codigo_municipio_ibge
    ) AS ranking_2025,
    codigo_municipio_ibge,
    municipio,
    quantidade_2000_toneladas,
    quantidade_2025_toneladas,
    aumento_quantidade_toneladas
FROM maiores_aumentos
WHERE ranking_aumento <= 10
ORDER BY quantidade_2025_toneladas DESC, codigo_municipio_ibge;
