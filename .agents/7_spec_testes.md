CONTEXTO
Estou construindo um pipeline de dados em Python sobre o dataset público do IBGE
sobre Pesquisa Agrícola Municipal (PAM), tabela SIDRA 5457(2000-2025) e tabela de municípios do GOV.BR.
Trabalho com spec-driven development: a spec abaixo é a fonte da
verdade e o código é consequência dela. Não acrescente requisito que não
esteja escrito aqui. Se algo estiver ambíguo, pergunte antes de escrever código.

STACK
- Python 3.13, uv, DuckDB
- pytest e pytest-cov, já instalados com uv add --dev

O QUE JÁ EXISTE (leia tudo antes de escrever qualquer teste)
pipeline/db.py, pipeline/ingestao.py, pipeline/transformacao.py,
pipeline/marts.py, painel.py, relatorio.py, app.py e sql/marts/*.sql.
Cada módulo tem a sua spec na docstring do topo, com critérios de aceite.

ARTEFATOS A PRODUZIR
Pasta test/ na raiz, com um arquivo por módulo: test_db.py,
test_ingestao.py, test_transformacao.py, test_marts.py, test_painel.py,
test_relatorio.py. Executável com:
  uv run pytest --cov
Configuração no pyproject.toml:
  [tool.pytest.ini_options]
  testpaths = ["test"]
  pythonpath = ["."]
  [tool.coverage.run]
  source = ["."]
  omit = ["test/*", "app.py", "ui.py", ".venv/*"]
  [tool.coverage.report]
  fail_under = 60
  show_missing = true

SPEC
1. META
   60% de coverage de linhas no TOTAL do código Python do projeto:
   pipeline/, painel.py e relatorio.py. A meta é do total, não de cada
   arquivo. Arquivo que nenhum teste importa conta como 0%, e é isso que
   o source = ["."] garante.
   Ficam fora da medição: app.py, a tela do Streamlit, conferida no
   navegador no passo 4.4; e ui.py, que só abre a interface do DuckDB.
   Motivo: testar layout por coverage não prova nada.

2. NUNCA O BANCO NEM OS DADOS DO PROJETO
   Nenhum teste abre agrodata.duckdb nem lê os arquivos de raw/.
   Cada teste usa tmp_path: um DuckDB novo dentro dele e, quando precisar
   de CSV, arquivos .csv.gz pequenos escritos pelo próprio teste. Para o
   código encontrar esses arquivos, use monkeypatch.chdir(tmp_path) ou
   monkeypatch.setattr na constante de caminho do módulo.
   Motivo: o teste tem que rodar em qualquer máquina, sem o pipeline ter
   rodado, e não pode alterar o banco de ninguém.
   São testes unitários do código. Testes de qualidade sobre o dado real
   (chave única, domínio, totais que batem) ficam fora deste pedido.

3. DADO INVENTADO, RESULTADO DA REGRA
   Toda entrada é inventada pelo teste: poucas linhas, cada uma com um
   comentário dizendo por que está ali (pedido com dois itens, pedido
   cancelado, entrega às 15h do dia previsto, data nula, linha duplicada).
   O valor esperado sai da conta feita sobre essa entrada, nunca de um
   número medido no dado da Agrodata.
   Motivo: o dado real muda todo dia; a regra não.

4. O QUE TESTAR
   Os critérios de aceite das docstrings são a lista de partida: cada
   critério que descreve uma regra vira pelo menos um teste. Em especial:
   - ingestão: o CSV vira tabela com as mesmas linhas; arquivo faltando
     encerra com SystemExit.
   - transformação: duplicata exata sai; datas viram TIMESTAMP e dinheiro
     DECIMAL; valor que não converte encerra com SystemExit, sem virar nulo.
   - marts: arquivo sem prefixo NN_ para antes de executar; mart vazio
     encerra e deixa o schema marts como estava; arquivo apagado faz o
     mart sumir na execução seguinte. test_marts.py deve validar as
     fórmulas das 15 consultas
   - painel: reais, pct e numero com entradas inventadas; cada função de
     gráfico devolve uma figura com tantos pontos quantas linhas tem o
     DataFrame inventado.
   - relatorio: gera o arquivo dentro de tmp_path; rodar duas vezes muda
     só o rodapé.
   Caminho de erro que encerra com sys.exit: pytest.raises(SystemExit).

5. ESTILO
   pytest puro: funções test_* com assert. Fixtures, só tmp_path e
   monkeypatch. DuckDB de verdade, nunca mock do banco.
   O nome do teste é a frase que ele prova:
     test_nivel_br_fica_fora_de_calculo_por_municipio
   Proibido: teste sem assert, skip, xfail, try/except em volta do assert,
   pytest.approx em dinheiro. Motivo: cada um sobe o coverage sem provar
   nada.

6. NÃO ALTERE O CÓDIGO DO PROJETO
   Nenhum arquivo muda fora de test/ e do pyproject.toml. Se uma parte só
   for testável mudando o código, não mude: liste na entrega, com o motivo.

CRITÉRIOS DE ACEITE
- uv run pytest --cov termina sem falha, com TOTAL de 60% ou mais.
- Com agrodata.duckdb renomeado, o resultado é o mesmo.
- Rodar duas vezes seguidas imprime a mesma coisa.
- Uma busca por 5571, 144690 e 729021 dentro de test/ não encontra nada.
- git status mostra mudança só em test/ e no pyproject.toml.

ENTREGA
1. Os arquivos de teste.
2. A saída de uv run pytest --cov, com a tabela por arquivo.
3. As linhas que ficaram sem teste (coluna Missing) e por que não valeram
   o esforço agora.
4. Uma lista final do que você assumiu e que não estava na spec.