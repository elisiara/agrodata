-- 2. Quais os 20 maiores municipios produtores agrícolas, por valor da produção.
-- Para o ano de 2025:	Ranking dos municipios por valor de produção( somando-se
-- os o valor de produção de todas as culturas produzidas no municipio).
-- Calcular também a Quantidade produzida (Toneladas) total para cada um,
-- em toneladas. Total de 20 linhas , uma por municipio,
-- ordenando do maior produtor pro menor(em valor da produção) para todo o periodo.
-- O valor da produção permanece na unidade da tabela: mil reais.
-- Municípios empatados são ordenados pelo código IBGE.
-- A consulta abaixo interpreta o pedido como um ranking apenas para 2025.
-- Soma as sete culturas de cada município, mantém somente linhas MU e
-- retorna a quantidade total sem conversão, em toneladas.
-- Grão das CTEs e do resultado:
-- valor_por_municipio: município em 2025.
-- quantidade_por_municipio: município em 2025.
-- ranking: município em 2025, com posição no ranking nacional.
-- Resultado final: município entre as 20 primeiras posições.

WITH valor_por_municipio AS (
    SELECT
        codigo_municipio_ibge,
        brasil_e_municipio,
        COALESCE(algodao_herbaceo_em_caroco, 0)
          + COALESCE(arroz_em_casca, 0)
          + COALESCE(cafe_em_grao_total, 0)
          + COALESCE(feijao_em_grao_total, 0)
          + COALESCE(milho_em_grao_total, 0)
          + COALESCE(soja_em_grao_total, 0)
          + COALESCE(trigo_em_grao_total, 0)
            AS valor_total_producao_mil_reais
    FROM refined.valor_da_producao
    WHERE nivel = 'MU'
      AND ano = 2025
),
quantidade_por_municipio AS (
    SELECT
        codigo_municipio_ibge,
        COALESCE(algodao_herbaceo_em_caroco, 0)
          + COALESCE(arroz_em_casca, 0)
          + COALESCE(cafe_em_grao_total, 0)
          + COALESCE(feijao_em_grao_total, 0)
          + COALESCE(milho_em_grao_total, 0)
          + COALESCE(soja_em_grao_total, 0)
          + COALESCE(trigo_em_grao_total, 0)
            AS quantidade_total_toneladas
    FROM refined.quantidade_produzida
    WHERE nivel = 'MU'
      AND ano = 2025
),
ranking AS (
    SELECT
        v.codigo_municipio_ibge,
        v.brasil_e_municipio AS municipio,
        v.valor_total_producao_mil_reais,
        q.quantidade_total_toneladas,
        ROW_NUMBER() OVER (
            ORDER BY
                v.valor_total_producao_mil_reais DESC,
                v.codigo_municipio_ibge
        ) AS posicao
    FROM valor_por_municipio AS v
    LEFT JOIN quantidade_por_municipio AS q
        ON q.codigo_municipio_ibge = v.codigo_municipio_ibge
)
SELECT
    posicao AS ranking,
    codigo_municipio_ibge,
    municipio,
    valor_total_producao_mil_reais,
    quantidade_total_toneladas
FROM ranking
WHERE posicao <= 20
ORDER BY posicao;