-- 15. Composição e concentração do valor da produção por cultura e estado,
-- em 2025, usando as sete culturas do dataset e somente registros MU.
-- As participações percentuais somam 100% por estado, considerando as sete
-- culturas. O índice Herfindahl-Hirschman (HHI) é a soma dos quadrados das
-- participações em proporção (entre 0 e 1): quanto mais próximo de 1, mais
-- concentrado o valor em poucas culturas. O número efetivo de culturas (1/HHI)
-- aproxima quantas culturas teriam pesos iguais para produzir a mesma
-- concentração. Esses indicadores não representam toda a agricultura estadual:
-- consideram apenas as sete culturas da tabela e valores brutos.
--
-- Grão de cada CTE:
-- valor_por_estado_cultura: uma linha por estado (UF) × cultura em 2025.
-- participacao_por_cultura: uma linha por estado (UF) × cultura, com a
--   participação de cada cultura no valor total estadual.
-- concentracao_por_estado: uma linha por estado (UF), com valor total,
--   HHI e número efetivo de culturas.
-- ranking_culturas: uma linha por estado (UF) × cultura, com a posição da
--   cultura no ranking de valor daquele estado.
-- Grão do SELECT final: uma linha por estado (UF) × cultura em 2025,
--   contendo o valor e a participação da cultura, sua posição no ranking
--   estadual e os indicadores de concentração do estado.

WITH valor_por_estado_cultura AS (
    SELECT
        m.uf,
        c.cultura,
        SUM(COALESCE(c.valor_producao_mil_reais, 0))
            AS valor_producao_mil_reais
    FROM refined.valor_da_producao AS v
    JOIN refined.municipio AS m
      ON m.codigo_municipio_ibge = v.codigo_municipio_ibge
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
    GROUP BY m.uf, c.cultura
),
participacao_por_cultura AS (
    SELECT
        uf,
        cultura,
        valor_producao_mil_reais,
        SUM(valor_producao_mil_reais) OVER (PARTITION BY uf)
            AS valor_total_estado_mil_reais,
        100.0 * valor_producao_mil_reais
            / NULLIF(
                SUM(valor_producao_mil_reais) OVER (PARTITION BY uf),
                0
            ) AS participacao_valor_estado_percentual
    FROM valor_por_estado_cultura
),
concentracao_por_estado AS (
    SELECT
        uf,
        MAX(valor_total_estado_mil_reais) AS valor_total_estado_mil_reais,
        SUM(POWER(participacao_valor_estado_percentual / 100.0, 2))
            AS indice_concentracao_hhi,
        1.0 / NULLIF(
            SUM(POWER(participacao_valor_estado_percentual / 100.0, 2)),
            0
        )
            AS numero_efetivo_culturas
    FROM participacao_por_cultura
    GROUP BY uf
),
ranking_culturas AS (
    SELECT
        uf,
        cultura,
        ROW_NUMBER() OVER (
            PARTITION BY uf
            ORDER BY valor_producao_mil_reais DESC, cultura
        ) AS ranking_no_estado
    FROM valor_por_estado_cultura
)
SELECT
    p.uf,
    p.cultura,
    p.valor_producao_mil_reais,
    p.valor_total_estado_mil_reais,
    p.participacao_valor_estado_percentual,
    r.ranking_no_estado,
    c.indice_concentracao_hhi,
    c.numero_efetivo_culturas
FROM participacao_por_cultura AS p
JOIN concentracao_por_estado AS c
  ON c.uf = p.uf
JOIN ranking_culturas AS r
  ON r.uf = p.uf
 AND r.cultura = p.cultura
ORDER BY p.uf, r.ranking_no_estado;
