-- 15. Concentração do valor da produção por cultura dentro de cada estado,
-- em 2025, usando as sete culturas do dataset e somente registros MU.
-- O índice Herfindahl-Hirschman (HHI) é a soma dos quadrados das participações
-- das culturas no valor total estadual: quanto mais próximo de 1, mais
-- concentrado o valor em poucas culturas. O número efetivo de culturas (1/HHI)
-- facilita a leitura: aproxima quantas culturas teriam pesos iguais para
-- produzir a mesma concentração. O indicador não mede toda a agricultura
-- estadual: considera apenas as sete culturas da tabela e valores brutos.

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
        valor_producao_mil_reais
            / NULLIF(
                SUM(valor_producao_mil_reais) OVER (PARTITION BY uf),
                0
            ) AS participacao_valor_estado
    FROM valor_por_estado_cultura
),
concentracao_por_estado AS (
    SELECT
        uf,
        MAX(valor_total_estado_mil_reais) AS valor_total_estado_mil_reais,
        SUM(POWER(participacao_valor_estado, 2))
            AS indice_concentracao_hhi,
        1.0 / NULLIF(SUM(POWER(participacao_valor_estado, 2)), 0)
            AS numero_efetivo_culturas
    FROM participacao_por_cultura
    GROUP BY uf
),
ranking_culturas AS (
    SELECT
        uf,
        cultura AS cultura_de_maior_valor,
        valor_producao_mil_reais AS valor_cultura_de_maior_valor_mil_reais,
        100.0 * participacao_valor_estado
            AS participacao_cultura_de_maior_valor_percentual,
        ROW_NUMBER() OVER (
            PARTITION BY uf
            ORDER BY valor_producao_mil_reais DESC, cultura
        ) AS posicao
    FROM participacao_por_cultura
)
SELECT
    c.uf,
    c.valor_total_estado_mil_reais,
    r.cultura_de_maior_valor,
    r.valor_cultura_de_maior_valor_mil_reais,
    r.participacao_cultura_de_maior_valor_percentual,
    c.indice_concentracao_hhi,
    c.numero_efetivo_culturas
FROM concentracao_por_estado AS c
JOIN ranking_culturas AS r
  ON r.uf = c.uf
 AND r.posicao = 1
ORDER BY c.indice_concentracao_hhi DESC, c.uf;
