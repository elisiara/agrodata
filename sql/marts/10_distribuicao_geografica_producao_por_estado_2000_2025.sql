-- 10. Distribuição geográfica da produção agrícola de 2000 a 2025.
-- Produção medida em toneladas, somando as sete culturas por estado.
-- Considera registros municipais (MU); BR é excluído para evitar dupla contagem.
-- Grão das CTEs e do resultado:
-- producao_por_estado_ano: estado (UF) × ano (2000 a 2025).
-- distribuicao: estado × ano, com participação e posição no respectivo ano.
-- Resultado final: estado (UF) × ano.

WITH producao_por_estado_ano AS (
    SELECT
        m.uf,
        q.ano,
        SUM(
            COALESCE(q.algodao_herbaceo_em_caroco, 0)
          + COALESCE(q.arroz_em_casca, 0)
          + COALESCE(q.cafe_em_grao_total, 0)
          + COALESCE(q.feijao_em_grao_total, 0)
          + COALESCE(q.milho_em_grao_total, 0)
          + COALESCE(q.soja_em_grao_total, 0)
          + COALESCE(q.trigo_em_grao_total, 0)
        ) AS quantidade_produzida_toneladas
    FROM refined.quantidade_produzida AS q
    JOIN refined.municipio AS m
      ON m.codigo_municipio_ibge = q.codigo_municipio_ibge
    WHERE q.nivel = 'MU'
      AND q.ano BETWEEN 2000 AND 2025
    GROUP BY m.uf, q.ano
),
distribuicao AS (
    SELECT
        uf,
        ano,
        quantidade_produzida_toneladas,
        100.0 * quantidade_produzida_toneladas
            / NULLIF(SUM(quantidade_produzida_toneladas) OVER (PARTITION BY ano), 0)
            AS participacao_nacional_percentual,
        ROW_NUMBER() OVER (
            PARTITION BY ano
            ORDER BY quantidade_produzida_toneladas DESC, uf
        ) AS ranking_no_ano
    FROM producao_por_estado_ano
)
SELECT
    uf,
    ano,
    ranking_no_ano,
    quantidade_produzida_toneladas,
    participacao_nacional_percentual,
    CASE WHEN ranking_no_ano = 1 THEN 'Maior produtor no ano' END
        AS destaque
FROM distribuicao
ORDER BY uf, ano;
