-- 3. Expansão da área agrícola, 10 municipios destaques em expansão entre
-- 2000 e 2025:	10 Municípios com maior crescimento de área plantada.
-- Identificar a expansão das areas plantadas de cada municipio no periodo
-- de 26 anos, e rankear de forma decrescente apartir do que mais expandiu
-- sua área plantada. Somar os valores de áreas de todas as culturas
-- plantadas. Bucar apenas em linhas de nível "MU", descartar linhas de
-- nível "BR"
-- A consulta abaixo mede a expansão como a diferença entre a área plantada
-- em 2025 e 2000, somando as sete culturas em cada município.
-- Retorna os 10 municípios com crescimento positivo; a área é apresentada em hectares.
-- Grão das CTEs e do resultado:
-- area_por_municipio_ano: município × ano (2000 ou 2025).
-- variacao_por_municipio: município com dados nos dois anos.
-- expansao: município com aumento de área entre os dois anos.
-- Resultado final: município entre os 10 maiores aumentos de área.

WITH area_por_municipio_ano AS (
    SELECT
        codigo_municipio_ibge,
        brasil_e_municipio,
        ano,
        COALESCE(algodao_herbaceo_em_caroco, 0)
          + COALESCE(arroz_em_casca, 0)
          + COALESCE(cafe_em_grao_total, 0)
          + COALESCE(feijao_em_grao_total, 0)
          + COALESCE(milho_em_grao_total, 0)
          + COALESCE(soja_em_grao_total, 0)
          + COALESCE(trigo_em_grao_total, 0)
            AS area_plantada_total_hectares
    FROM refined.area_plantada_ou_destinada_a_colheita
    WHERE nivel = 'MU'
      AND ano IN (2000, 2025)
),
variacao_por_municipio AS (
    SELECT
        codigo_municipio_ibge,
        brasil_e_municipio AS municipio,
        SUM(
            CASE WHEN ano = 2000
                 THEN area_plantada_total_hectares
                 ELSE 0
            END
        ) AS area_plantada_2000_hectares,
        SUM(
            CASE WHEN ano = 2025
                 THEN area_plantada_total_hectares
                 ELSE 0
            END
        ) AS area_plantada_2025_hectares
    FROM area_por_municipio_ano
    GROUP BY
        codigo_municipio_ibge,
        brasil_e_municipio
    HAVING COUNT(DISTINCT ano) = 2
),
expansao AS (
    SELECT
        codigo_municipio_ibge,
        municipio,
        area_plantada_2000_hectares,
        area_plantada_2025_hectares,
        area_plantada_2025_hectares - area_plantada_2000_hectares
            AS crescimento_area_hectares
    FROM variacao_por_municipio
    WHERE area_plantada_2025_hectares > area_plantada_2000_hectares
)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY crescimento_area_hectares DESC, codigo_municipio_ibge
    ) AS ranking,
    codigo_municipio_ibge,
    municipio,
    area_plantada_2000_hectares,
    area_plantada_2025_hectares,
    crescimento_area_hectares,
    100.0 * crescimento_area_hectares
        / NULLIF(area_plantada_2000_hectares, 0)
        AS crescimento_area_percentual
FROM expansao
ORDER BY crescimento_area_hectares DESC, codigo_municipio_ibge
LIMIT 10;

-- O filtro COUNT(DISTINCT ano) = 2 exige dados para os dois anos comparados.
-- WHERE area_plantada_2025_hectares > area_plantada_2000_hectares limita
-- o resultado a municípios que realmente expandiram a área. O percentual
-- usa a área de 2000 como base; NULLIF evita divisão por zero.