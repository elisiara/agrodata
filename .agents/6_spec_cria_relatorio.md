Leia a docstring de painel.py: é a spec do painel e continua valendo.

ARTEFATO A PRODUZIR
relatorio.py, na raiz, executável com:
  uv run python relatorio.py

SPEC
1. Lê os marts com painel.ler(), formata com painel.reais/pct/numero e
   monta os gráficos com as mesmas funções de painel.py. Não importa
   streamlit. Não desenha nenhum gráfico que não esteja em painel.py.
2. Escreve relatorio.html na raiz: um arquivo só, com  13 métricas em cartões
  (4 nacionais, 3 estaduais, 3 municipais e 3 de composição por UF) do app.py,
  na mesma ordem. Cartões em HTML simples, numa grade.
   Gráficos com figura.to_html(full_html=False); a biblioteca do plotly
   vem do CDN uma vez só, no primeiro gráfico (include_plotlyjs="cdn"),
   e nos outros include_plotlyjs=False. Cada gráfico com div_id fixo
   ("g01", "g02"...). Motivo: sem ele o plotly sorteia um id novo a cada
   execução, e o arquivo muda sem o dado mudar.
3. Sem filtro: cada gráfico mostra o período padrão do app.py,
   2000 a 2025, ou 2024 à 2025, ou sómente 2025, e o título diz o período.
4. Rodapé com a data e a hora em que o arquivo foi gerado:
   "Dados de 02/11/2026 14:03". Motivo: o arquivo não fala com o banco;
   quem lê precisa saber de quando é o número.
5. Imprime o caminho do arquivo e o tamanho em KB. stdout em utf-8.

CRITÉRIOS DE ACEITE
- Abrir relatorio.html com dois cliques mostra os sete cartões com os
  mesmos valores do app.py.
- O arquivo tem menos de 200 KB.
- Rodar duas vezes muda só a data do rodapé.