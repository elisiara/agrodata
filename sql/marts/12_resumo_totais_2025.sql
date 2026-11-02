-- 12. Total do Valor da produção, volume total de quantidade
-- produzida(Toneladas colhidas), total de Área colhida (Hectares),
-- Rendimento médio da produção (Quilogramas por Hectare),
-- somando-se todas as culturas no Brasil pro ano de 2025.
-- Ler somente a linha onde o nível for "BR" e o ano for "2025".
-- Retonar uma linha com o somatório dos valores de todas as culturas,
-- uma coluna para o valor da receita da produção, uma coluna
-- para o valor que representa o volume total de tonelas colhidas,
-- uma coluna que representa o valor total de area em hectare de
-- area colhida.
-- Grão das CTEs e do resultado:
-- valor: total nacional do valor da produção em 2025 (uma linha).
-- quantidade: total nacional produzido em 2025 (uma linha).
-- area: total nacional de área colhida em 2025 (uma linha).
-- Resultado final: resumo dos totais nacionais de 2025 (uma linha).

WITH valor AS (
    SELECT SUM(
        COALESCE(algodao_herbaceo_em_caroco, 0)
        + COALESCE(arroz_em_casca, 0)
        + COALESCE(cafe_em_grao_total, 0)
        + COALESCE(feijao_em_grao_total, 0)
        + COALESCE(milho_em_grao_total, 0)
        + COALESCE(soja_em_grao_total, 0)
        + COALESCE(trigo_em_grao_total, 0)
    ) AS receita_producao_mil_reais
    FROM refined.valor_da_producao
    WHERE nivel = 'BR'
      AND ano = 2025
),
quantidade AS (
    SELECT SUM(
        COALESCE(algodao_herbaceo_em_caroco, 0)
        + COALESCE(arroz_em_casca, 0)
        + COALESCE(cafe_em_grao_total, 0)
        + COALESCE(feijao_em_grao_total, 0)
        + COALESCE(milho_em_grao_total, 0)
        + COALESCE(soja_em_grao_total, 0)
        + COALESCE(trigo_em_grao_total, 0)
    ) AS volume_total_toneladas
    FROM refined.quantidade_produzida
    WHERE nivel = 'BR'
      AND ano = 2025
),
area AS (
    SELECT SUM(
        COALESCE(algodao_herbaceo_em_caroco, 0)
        + COALESCE(arroz_em_casca, 0)
        + COALESCE(cafe_em_grao_total, 0)
        + COALESCE(feijao_em_grao_total, 0)
        + COALESCE(milho_em_grao_total, 0)
        + COALESCE(soja_em_grao_total, 0)
        + COALESCE(trigo_em_grao_total, 0)
    ) AS area_total_hectares
    FROM refined.area_colhida
    WHERE nivel = 'BR'
      AND ano = 2025
)
SELECT
    valor.receita_producao_mil_reais,
    quantidade.volume_total_toneladas,
    area.area_total_hectares,
    1000.0 * quantidade.volume_total_toneladas
        / NULLIF(area.area_total_hectares, 0)
        AS rendimento_medio_kg_por_hectare
FROM valor
CROSS JOIN quantidade
CROSS JOIN area;
-- O valor da produção está em mil reais, conforme a unidade da tabela.
--Incluí o rendimento como média ponderada: toneladas totais convertidas
--em quilos divididas pela área total — somar os rendimentos das
--culturas não seria adequado.