# Redator

Projeto Python para coletar proposições de deputados federais do Rio Grande do Sul, resumir indicadores da base e gerar um boletim em Markdown e PDF. O boletim pode usar a API do Gemini para reescrever ementas em linguagem mais acessível.

## Estrutura atual

- `redator1.py`: consulta a API da Câmara e gera o CSV principal.
- `analisador_dados.py`: lê o CSV, mostra indicadores no terminal e solicita o PDF de análise.
- `gerador_boletim.py`: seleciona proposições, solicita resumos ao Gemini e gera o boletim em Markdown e PDF.
- `relatorios.py`: concentra a formatação e exportação dos PDFs.
- `teste_gemini.py`: envia uma requisição curta para verificar a conexão com o Gemini.
- `projetos_assinados_parlamentares_rs.csv`: base CSV disponível atualmente no projeto; a coleta pode regenerá-la.
- `requirements.txt`: dependências Python.
- `.gitignore`: exclui `.env`, `.venv`, arquivos compilados e PDFs gerados.

Os arquivos `analise_dados.pdf`, `boletim_parlamentar.md` e `boletim_parlamentar.pdf` são saídas dos scripts e só aparecem depois de executar as respectivas etapas.

## Fluxo de dados

### Coleta

`redator1.py` consulta a API Dados Abertos da Câmara. Ele percorre as páginas de deputados do RS indicadas pela API e, para cada deputado, solicita até cinco proposições recentes associadas ao autor. Para cada proposição, consulta o detalhe para obter o status quando disponível.

O CSV gerado usa as colunas `Deputado(a)`, `Partido`, `Tipo`, `Número`, `Ano`, `Último Status` e `Ementa/Resumo`. As consultas têm timeout, até quatro tentativas em falhas temporárias, espera progressiva e um intervalo mínimo entre requisições.

### Análise

`analisador_dados.py` valida as colunas essenciais do CSV e exibe total de registros, deputados e partidos com mais ocorrências, status mais frequentes e destaques de PLs e PECs. Também gera `analise_dados.pdf` com tabelas formatadas.

### Boletim

`gerador_boletim.py` valida o CSV, ordena PLs e PECs por ano e número, seleciona até 20 itens e gera `boletim_parlamentar.md` e `boletim_parlamentar.pdf`. O Gemini simplifica as ementas; se não houver chave ou uma chamada falhar, o texto original é usado. As chamadas incluem timeout, até quatro tentativas com espera progressiva e uma pausa entre solicitações.

## Requisitos

- Python 3.10 ou superior
- pandas
- requests
- python-dotenv
- reportlab

## Instalação

Na raiz do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuração do Gemini

Copie `.env.example` para `.env` na raiz do projeto e preencha sua chave:

```env
GEMINI_API_KEY=sua_chave_aqui
```

O arquivo `.env` está excluído pelo `.gitignore`; `.env.example` contém apenas o modelo sem credenciais. O gerador usa a chave no cabeçalho `x-goog-api-key`. O modelo configurado no código é `gemini-3.5-flash-lite`.

## Como executar

Execute os comandos a partir da raiz do projeto. O comando principal roda as três etapas na ordem: coleta, análise e geração do boletim.

1. Executar o pipeline completo:

   ```bash
   python redator1.py
   ```

   Isso atualiza o CSV e gera `analise_dados.pdf`, `boletim_parlamentar.md` e `boletim_parlamentar.pdf`. A chave do Gemini é opcional: sem ela, o boletim usa as ementas originais.

2. Executar somente a análise do CSV existente:

   ```bash
   python analisador_dados.py
   ```

3. Executar somente a geração do boletim a partir do CSV existente:

   ```bash
   python gerador_boletim.py
   ```

4. Verificar a conexão com o Gemini:

   ```bash
   python teste_gemini.py
   ```

## Estado da verificação

Os cinco scripts Python foram compilados para verificar a sintaxe. Essa verificação não executa chamadas à API da Câmara ou ao Gemini nem confirma a geração real dos relatórios. O funcionamento integrado depende da rede, das APIs externas e, para resumos por IA, de uma chave válida.

Não há testes automatizados configurados no repositório.

## Melhorias futuras

- adicionar testes automatizados com respostas simuladas das APIs;
- permitir filtrar por deputado, partido, tema e período;
- acrescentar gráficos e exportação para formatos adicionais;
- melhorar os critérios editoriais usados para selecionar os destaques.
