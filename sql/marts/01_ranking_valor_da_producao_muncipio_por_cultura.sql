-- 1. Ranking municipal de maior valor da produção por cultura:
-- Municípios com maior valor da produção de cada cultura.
-- Ler valores de tabela valor_da_producao. Um municipio por cultura
-- para o periodo de 2000 a 2025. Total a retornar são 7 linhas.
-- Considerar apenas as linhas de nivel "MU", desconsiderar linhas
-- de nível "BR".

WITH valores_por_cultura AS (
    SELECT
        codigo_municipio_ibge,
        brasil_e_municipio,
        cultura,
        valor_producao
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
    ) AS c(cultura, valor_producao)
    WHERE v.nivel = 'MU'
      AND v.ano BETWEEN 2000 AND 2025
),
totais_por_municipio AS (
    SELECT
        codigo_municipio_ibge,
        brasil_e_municipio,
        cultura,
        SUM(valor_producao) AS valor_total_producao_mil_reais
    FROM valores_por_cultura
    GROUP BY
        codigo_municipio_ibge,
        brasil_e_municipio,
        cultura
),
ranking AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY cultura
            ORDER BY
                valor_total_producao_mil_reais DESC NULLS LAST,
                codigo_municipio_ibge
        ) AS posicao
    FROM totais_por_municipio
)
SELECT
    r.cultura,
    r.codigo_municipio_ibge,
    r.brasil_e_municipio AS municipio,
    m.uf,
    r.valor_total_producao_mil_reais
FROM ranking AS r
JOIN refined.municipio AS m
  ON m.codigo_municipio_ibge = r.codigo_municipio_ibge
WHERE r.posicao = 1
ORDER BY r.cultura;
-- O valor retornado está em mil reais, unidade da tabela. A ordenação por código desempata de
-- forma determinística quando municípios têm o mesmo total.