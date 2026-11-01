Você tem acesso ao meu banco agrodata.duckdb pelo MCP, em somente leitura.
Leia specs/transformacao.md: é a fonte da verdade.

Antes de escrever qualquer código:
1. Para cada tabela de entrada, escreva o SELECT que aplica a spec
   (nomes, tipos, duplicatas) e rode no banco, sem criar tabela.
2. Para cada uma, confira no banco e me mostre numa tabela:
   linhas que entram, linhas que saem, nulos por coluna antes e depois,
   e quantos valores falharam na conversão.
3. Se algum número não bater com a spec, pare e me explique.
   Não ajuste a spec nem o SELECT por conta própria.

Só depois que eu aprovar os números:
4. Escreva pipeline/transformacao.py usando exatamente esses SELECTs.
   O script é quem grava em refined; você não grava nada no banco.