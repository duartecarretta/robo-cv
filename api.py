from __future__ import annotations

from datetime import datetime, timezone

import os
import shutil
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from robo_candidatura import (
    carregar_texto_vaga,
    gerar_cv_end_to_end,
    gerar_cover_letter_end_to_end,
    gerar_descricao_profissional_ats,
    gerar_mensagem_recrutador,
    gerar_guia_entrevista_end_to_end,
)

app = FastAPI(
    title="RoboCV API",
    description=(
        "API oficial do RoboCV: gera CV, Cover Letter, descrição ATS/LinkedIn, "
        "mensagem para recrutador e guia de entrevista a partir de CV e vaga."
    ),
    version="1.0.0",
)



@app.get("/health", summary="Health check da API")
def health_check():
    return {
        "status": "ok",
        "service": "RoboCV API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

UPLOAD_DIR = Path("api_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".docx", ".pdf"}
DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class PerfilEVagaInput(BaseModel):
    """
    Payload para endpoints que recebem perfil e vaga já estruturados.
    Utilizado para descrição ATS e mensagem para recrutador.
    """
    perfil: dict = Field(..., description="Perfil estruturado do candidato")
    vaga: dict = Field(..., description="Vaga estruturada")
    idioma: str = Field(default="pt", description="Idioma da saída (pt ou en)")


def salvar_upload_temporario(arquivo_cv: UploadFile) -> Path:
    """
    Salva o UploadFile em disco com um nome único e valida extensão.
    """
    if not arquivo_cv.filename:
        raise ValueError("Nenhum arquivo enviado.")

    extensao = Path(arquivo_cv.filename).suffix.lower()
    if extensao not in ALLOWED_EXTENSIONS:
        raise ValueError("arquivocv deve ser .docx ou .pdf.")

    nome_temp = f"{uuid.uuid4()}{extensao}"
    caminho_temp = UPLOAD_DIR / nome_temp

    with caminho_temp.open("wb") as buffer:
        shutil.copyfileobj(arquivo_cv.file, buffer)

    return caminho_temp


def validar_entrada_vaga(vaga_input: str) -> str:
    """
    Converte vaga em texto consolidado, aceitando:
    - texto colado
    - URL de vaga
    - caminho de PDF local
    """
    texto_vaga = carregar_texto_vaga(vaga_input or "")
    if not texto_vaga:
        raise ValueError("Não foi possível interpretar a vaga. Verifique o texto, URL ou PDF enviado.")
    return texto_vaga


def resposta_erro(exc: Exception, status_code: int = 500) -> JSONResponse:
    """
    Retorna erro em JSON de forma padronizada.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "erro": str(exc),
        },
    )


@app.post("/gerar-cv", summary="Gerar CV otimizado em DOCX")
async def api_gerar_cv(
    arquivo_cv: UploadFile = File(..., description="Arquivo de CV em .docx ou .pdf"),
    vaga_input: str = Form(..., description="Texto da vaga, URL ou caminho de PDF"),
    empresa: str = Form(..., description="Nome da empresa alvo"),
    cargo: str = Form(..., description="Nome do cargo alvo"),
    idioma: str = Form("pt", description="Idioma de saída (pt ou en)"),
    refinar: bool = Form(False, description="Se True, refina texto com IA"),
):
    """
    Gera um CV em DOCX totalmente personalizado para a vaga informada.
    """
    try:
        caminho_temp_cv = salvar_upload_temporario(arquivo_cv)
        texto_vaga = validar_entrada_vaga(vaga_input)

        caminho_resultado = gerar_cv_end_to_end(
            caminho_cv=caminho_temp_cv,
            texto_vaga=texto_vaga,
            empresa_alvo=empresa,
            cargo_alvo=cargo,
            idioma=idioma,
            refinar_texto=refinar,
            interativo=False,
        )

        return FileResponse(
            caminho_resultado,
            filename=os.path.basename(caminho_resultado),
            media_type=DOCX_MEDIA_TYPE,
        )
    except ValueError as exc:
        return resposta_erro(exc, 400)
    except Exception as exc:
        return resposta_erro(exc, 500)


@app.post("/gerar-cover-letter", summary="Gerar Cover Letter em DOCX")
async def api_gerar_cover_letter(
    arquivo_cv: UploadFile = File(..., description="Arquivo de CV em .docx ou .pdf"),
    vaga_input: str = Form(..., description="Texto da vaga, URL ou caminho de PDF"),
    empresa: str = Form(..., description="Nome da empresa alvo"),
    cargo: str = Form(..., description="Nome do cargo alvo"),
    idioma: str = Form("pt", description="Idioma de saída (pt ou en)"),
):
    """
    Gera uma Cover Letter em DOCX, alinhada ao CV e à vaga.
    """
    try:
        caminho_temp_cv = salvar_upload_temporario(arquivo_cv)
        texto_vaga = validar_entrada_vaga(vaga_input)

        caminho_resultado = gerar_cover_letter_end_to_end(
            caminho_cv=caminho_temp_cv,
            texto_vaga=texto_vaga,
            empresa_alvo=empresa,
            cargo_alvo=cargo,
            idioma=idioma,
            interativo=False,
        )

        return FileResponse(
            caminho_resultado,
            filename=os.path.basename(caminho_resultado),
            media_type=DOCX_MEDIA_TYPE,
        )
    except ValueError as exc:
        return resposta_erro(exc, 400)
    except Exception as exc:
        return resposta_erro(exc, 500)


@app.post("/gerar-descricao-ats", summary="Gerar descrição profissional ATS/LinkedIn")
def api_gerar_descricao_ats(payload: PerfilEVagaInput):
    """
    Gera um texto de descrição profissional otimizado para ATS/LinkedIn,
    a partir de um perfil e uma vaga já estruturados.
    """
    try:
        descricao = gerar_descricao_profissional_ats(
            perfil=payload.perfil,
            vaga=payload.vaga,
            idioma=payload.idioma,
        )
        return {"descricao_profissional": descricao}
    except ValueError as exc:
        return resposta_erro(exc, 400)
    except Exception as exc:
        return resposta_erro(exc, 500)


@app.post("/gerar-mensagem-recrutador", summary="Gerar mensagem curta para recrutador")
def api_gerar_mensagem_recrutador(payload: PerfilEVagaInput):
    """
    Gera uma mensagem curta (3 linhas) para abordar um recrutador
    sobre uma vaga específica, a partir de perfil e vaga estruturados.
    """
    try:
        mensagem = gerar_mensagem_recrutador(
            perfil=payload.perfil,
            vaga=payload.vaga,
            idioma=payload.idioma,
        )
        return mensagem
    except ValueError as exc:
        return resposta_erro(exc, 400)
    except Exception as exc:
        return resposta_erro(exc, 500)


@app.post("/gerar-guia-entrevista", summary="Gerar Guia de Entrevista em DOCX")
async def api_gerar_guia_entrevista(
    arquivo_cv: UploadFile = File(..., description="Arquivo de CV em .docx ou .pdf"),
    vaga_input: str = Form(..., description="Texto da vaga, URL ou caminho de PDF"),
    empresa: str = Form(..., description="Nome da empresa alvo"),
    cargo: str = Form(..., description="Nome do cargo alvo"),
    idioma: str = Form("pt", description="Idioma de saída (pt ou en)"),
    refinar: bool = Form(False, description="Se True, refina texto do CV antes do guia"),
):
    """
    Gera um Guia de Entrevista em DOCX com perguntas prováveis,
    respostas sugeridas e orientações sobre os bullets do CV.
    """
    try:
        caminho_temp_cv = salvar_upload_temporario(arquivo_cv)
        texto_vaga = validar_entrada_vaga(vaga_input)

        caminho_resultado = gerar_guia_entrevista_end_to_end(
            caminho_cv=caminho_temp_cv,
            texto_vaga=texto_vaga,
            empresa_alvo=empresa,
            cargo_alvo=cargo,
            idioma=idioma,
            refinar_texto=refinar,
        )

        return FileResponse(
            caminho_resultado,
            filename=os.path.basename(caminho_resultado),
            media_type=DOCX_MEDIA_TYPE,
        )
    except ValueError as exc:
        return resposta_erro(exc, 400)
    except Exception as exc:
        return resposta_erro(exc, 500)


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)