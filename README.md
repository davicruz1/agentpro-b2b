# AgentPro B2B

Aplicacao web para encontrar empresas locais sem site cadastrado, validar os resultados na web e gerar mensagens de prospeccao com o Google Gemini.

## Como funciona

1. Busca estabelecimentos por cidade e nicho na API Overpass do OpenStreetMap.
2. Descarta estabelecimentos sem telefone ou que ja tenham um site indicado no OpenStreetMap.
3. Pesquisa na web para evitar tratar como lead uma empresa que ja tenha um site.
4. Gera uma sugestao de mensagem com o Google Gemini e apresenta os resultados no dashboard Flask.

Os dados encontrados sao gravados localmente em `leads_extraidos/`. Essa pasta e ignorada pelo Git para evitar publicar dados de prospeccao.

## Requisitos

- Python 3.10 ou superior
- Uma chave de API do Google Gemini

## Configuracao

1. Clone o repositorio:

   ```bash
   git clone https://github.com/SEU_USUARIO/agentpro-b2b.git
   cd agentpro-b2b
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python -m venv .venv
   ```

   Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

3. Instale as dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Copie `.env.example` para `.env` e preencha `GEMINI_API_KEY` com sua chave. Nunca publique o arquivo `.env`.

5. Inicie o servidor:

   ```bash
   python app.py
   ```

6. Abra http://127.0.0.1:5000 no navegador.

## Uso responsavel

Use os dados obtidos de acordo com os termos dos servicos consultados e com as leis de privacidade e prospeccao aplicaveis. Revise as mensagens geradas antes de entrar em contato com qualquer empresa.
