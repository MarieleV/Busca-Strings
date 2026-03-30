# Comparação de Algoritmos de Busca em Strings
### Aplicação que permite explorar, visualizar e comparar diferentes algoritmos de busca em strings, analisando seu funcionamento passo a passo, desempenho e complexidade.
---
### Requisitos de Implementação
**Arquitetura:**
Utilização da Linguagem Python e padrão Strategy

SearchStrategy (interface)  ├── NaiveSearch  ├── RabinKarpSearch  ├── KMPSearch  ├── BoyerMooreSearch Interface (sugestão)
- Web (HTML + JS + backend opcional) ou desktop

**Elementos:**

1. Upload de arquivos
2. Input de string
3. Dropdown de algoritmo
4. Botão "Executar"
5. Botão "Passo a passo"
6. Área de visualização (log da execução)
---
### Requisitos Funcionais
#### Entrada de dados

- Upload de 1 ou N arquivos .txt
- Campo de entrada para a string a ser buscada
- Opção para escolher o algoritmo

#### Algoritmos obrigatórios
Implementação dos algoritmos:

- Busca Naive (força bruta)
- Rabin-Karp
- Knuth-Morris-Pratt (KMP)
- Boyer-Moore

#### Execução
**Executar o código:**

- Execução normal
- Execução passo a passo (step-by-step) - usar o debug da linguagem

**Durante o passo a passo, exibir:**

- Índices comparados
- Comparações realizadas
- Movimentação do padrão
- Estruturas auxiliares (ex: tabela LPS do KMP, tabela de saltos do Boyer-Moore)
- Métricas e análise
  
**Para cada execução:**

-Tempo de execução (ms ou ns)
- Número de comparações realizadas
- Tamanho do texto e do padrão

**Exibir também:**

Complexidade teórica:

- Naive → O(n * m)
- Rabin-Karp → O(n + m) (médio)
- KMP → O(n + m)
- Boyer-Moore → O(n / m) (melhor caso)

**Comparação entre:**

Tempo real vs complexidade esperada
