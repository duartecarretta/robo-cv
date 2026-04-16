# Robo_CV – Pipeline Inteligente de Candidatura

Robo_CV é um protótipo de plataforma HRTech orientada ao **candidato**, que utiliza modelos de linguagem para analisar CVs e vagas e gerar um kit completo de candidatura altamente personalizado.

## Visão do Projeto

O Robo_CV automatiza a jornada de candidatura digital, ajudando o candidato a:

- Ler um CV em **DOCX ou PDF** e extrair um **perfil estruturado**.
- Analisar o texto de uma vaga (ou URL / PDF) para extrair requisitos e palavras-chave ATS.
- Selecionar as experiências mais relevantes do histórico do candidato para aquela vaga.
- Gerar:
  - CV otimizado em DOCX
  - Cover Letter em DOCX
  - Descrição profissional otimizada para ATS / LinkedIn
  - Mensagem curta para abordar recrutador
  - Guia de Entrevista em DOCX

O foco é **reduzir a assimetria técnica** entre candidatos e sistemas de recrutamento digitais, sem inventar experiência nem dados falsos.

---

## Requisitos

- Python 3.10+ (recomendado)
- Chave de API da OpenAI em variável de ambiente `OPENAI_API_KEY`

Dependências Python (via `requirements.txt`):

- fastapi
- uvicorn[standard]
- openai
- python-docx
- pdfminer.six
- python-dotenv
- requests
- beautifulsoup4

---

## Instalação

1. Clone ou copie o projeto para uma pasta local:

```bash
git clone https://github.com/duartecarretta/robo-cv.git
cd robo_cv
```

2. Crie e ative um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
# ou
.\.venv\Scripts\activate   # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure a variável de ambiente com sua chave da OpenAI:

```bash
export OPENAI_API_KEY="sua_chave_aqui"    # Linux / macOS
set OPENAI_API_KEY="sua_chave_aqui"       # Windows
```

Você também pode criar um arquivo `.env` na raiz do projeto com:

```env
OPENAI_API_KEY=sua_chave_aqui
```

---

## Como rodar a API

Após instalar as dependências e definir a variável `OPENAI_API_KEY`:

```bash
uvicorn api:app --reload
```

A API ficará disponível em:

- Documentação interativa OpenAPI: http://localhost:8000/docs
- Documentação alternativa ReDoc: http://localhost:8000/redoc

---

## Endpoints Principais

### 1. `POST /gerar-cv`

Gera um CV otimizado em DOCX.

**Form-data**:

- `arquivo_cv` (file, obrigatório): CV em `.docx` ou `.pdf`
- `vaga_input` (string, obrigatório): texto da vaga, URL de vaga ou caminho de PDF
- `empresa` (string, obrigatório): nome da empresa alvo
- `cargo` (string, obrigatório): nome do cargo alvo
- `idioma` (string, opcional, default `pt`): `pt` ou `en`
- `refinar` (bool, opcional, default `false`): se `true`, refina texto com IA

**Resposta**: arquivo DOCX (CV) para download.

### 2. `POST /gerar-cover-letter`

Gera uma Cover Letter em DOCX.

Parâmetros: iguais ao `/gerar-cv` (sem `refinar`).

**Resposta**: arquivo DOCX (Cover Letter).

### 3. `POST /gerar-descricao-ats`

Gera uma descrição profissional otimizada para ATS/LinkedIn.

**JSON body**:

```json
{
  "perfil": { ... },
  "vaga": { ... },
  "idioma": "pt"
}
```

**Resposta**:

```json
{
  "descricao_profissional": "Texto gerado..."
}
```

### 4. `POST /gerar-mensagem-recrutador`

Gera uma mensagem curta para abordar um recrutador.

**JSON body**: igual ao `/gerar-descricao-ats`.

**Resposta** (exemplo):

```json
{
  "linha1": "Mensagem linha 1",
  "linha2": "Mensagem linha 2",
  "linha3": "Mensagem linha 3",
  "mensagem_unica": "Mensagem linha 1\nMensagem linha 2\nMensagem linha 3"
}
```

### 5. `POST /gerar-guia-entrevista`

Gera um Guia de Entrevista em DOCX.

**Form-data**:

- `arquivo_cv` (file, obrigatório)
- `vaga_input` (string, obrigatório)
- `empresa` (string, obrigatório)
- `cargo` (string, obrigatório)
- `idioma` (string, opcional, default `pt`)
- `refinar` (bool, opcional, default `false`)

**Resposta**: arquivo DOCX (Guia de Entrevista).

---

## Exemplo rápido de uso (CLI + curl)

Assumindo que a API está rodando em `http://localhost:8000`:

```bash
curl -X POST "http://localhost:8000/gerar-cv" \
  -F "arquivo_cv=@meu_cv.pdf" \
  -F "vaga_input=texto da vaga aqui ou URL" \
  -F "empresa=Empresa Exemplo" \
  -F "cargo=Analista de Dados" \
  -F "idioma=pt" \
  -F "refinar=true" \
  -o CV_RoboCV.docx
```

---

## Observações e Limitações do Protótipo

- O Robo_CV depende da **API da OpenAI**, portanto:
  - Requer conexão com a internet.
  - Está sujeito a latência de rede e custos de uso da API.
- O parsing de PDFs de CV e vagas depende de texto selecionável:
  - PDFs totalmente escaneados (imagem) podem não ser lidos corretamente.
- O sistema não inventa experiências, cargos ou resultados:
  - Quando as informações são insuficientes, o texto gerado tende a ser mais genérico.
- O foco deste protótipo é **personalização de documentos** e **suporte à preparação**,
  não há persistência em banco de dados nem autenticação de usuários.

---

## Sugestão de Fluxo de Demonstração para a Banca

1. **Cenário**: candidato com um CV genérico em PDF e uma vaga real copiada do LinkedIn.
2. Passos:
   - Mostrar rapidamente o arquivo `robo_candidatura.py` destacando:
     - Extração de perfil, análise da vaga, seleção de experiências.
     - Funções `gerar_cv_end_to_end` e `gerar_guia_entrevista_end_to_end`.
   - Rodar a API com `uvicorn api:app --reload`.
   - Na documentação `/docs`, testar ao vivo:
     1. `/gerar-cv` com o CV do candidato e o texto da vaga.
     2. Baixar e abrir o DOCX gerado, mostrando:
        - Resumo focado na vaga.
        - Experiências mais relevantes selecionadas.
     3. `/gerar-cover-letter` usando os mesmos insumos e mostrar a carta pronta.
     4. `/gerar-guia-entrevista`: abrir o DOCX com perguntas, respostas sugeridas e roteiros.
   - Comentar brevemente como o pipeline garante:
     - Não invenção de dados.
     - Reutilização do mesmo perfil/vaga para todos os artefatos.

Isso demonstra o produto como uma **plataforma integrada de candidatura** e não como um gerador isolado de CV.
