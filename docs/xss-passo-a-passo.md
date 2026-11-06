# Correção 3 — textos não podem virar código HTML

1. **Origem do problema:** mensagens da API e textos do localStorage eram
   interpolados em innerHTML. O navegador interpretava tags e atributos
   recebidos como parte da página.
2. **Correção:** a função textoHTML, em frontend/api.js, converte `&`, `<`, `>`,
   aspas duplas e simples em entidades HTML. A conversão acontece ao exibir,
   preservando o texto original no banco e evitando conversões duplicadas.
3. **Onde foi aplicada:** alertas, contas (inclusive a página duplicada), metas,
   cofrinho, receitas, gastos, desperdício, orçamento e recorrências. Datas
   formatadas e identificadores em atributos entre aspas também são tratados.
4. **Uso futuro:** prefira textContent para inserir texto diretamente em um
   elemento. Em templates HTML existentes, use `${textoHTML(valor)}` para
   texto ou atributos entre aspas. Esta função não protege código JavaScript,
   CSS ou URLs; não use dados externos nesses contextos sem validação própria.
5. **Teste manual:** cadastre uma meta com o título `<b>Teste</b>`. Ele deve
   aparecer literalmente, sem ficar em negrito. Repita em descrições de receita
   e recorrência. Nomes com acentos, apóstrofos e `&` devem continuar normais.
6. **Teste automatizado:** execute `node --test tests/test_xss.cjs`. Verifica
   escape de tags e aspas, uso nas interpolações alteradas e sintaxe de todos
   os scripts. Não substitui um teste visual num navegador real.

HTML fixo da aplicação continua permitido para preservar ícones e layout.
O chat de IA já usa textContent para as mensagens. Não é necessário apagar
os textos antigos: a proteção também se aplica quando eles são exibidos.
