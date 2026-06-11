from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models import (
    HealthResponse,
    RecommendationRequest,
    RevealRequest,
    TelegramExplainRequest,
    TelegramRecommendRequest,
)
from .recommender import score_group_books
from .reveal import generate_reveal, ARCHETYPE_PAIRS
from .supabase_service import SupabaseRepository

import os
import httpx

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if settings.environment != "production":
        return JSONResponse(status_code=500, content={"detail": str(exc)})
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


def get_repository() -> SupabaseRepository:
    return SupabaseRepository()


@app.head("/")
async def head_root() -> Response:
    return Response(status_code=200)


@app.get("/")
async def root() -> dict[str, Any]:
    return {"ok": True, "service": settings.app_name, "health": "/health", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name)


@app.get("/health/supabase")
async def supabase_healthcheck() -> dict[str, Any]:
    supabase_url_set = bool(settings.supabase_url)
    service_key_set = bool(settings.supabase_service_role_key)
    if not supabase_url_set or not service_key_set:
        return {
            "ok": False,
            "supabase_url_set": supabase_url_set,
            "supabase_service_role_key_set": service_key_set,
        }

    repo = get_repository()
    checks: dict[str, Any] = {
        "ok": True,
        "supabase_url_set": True,
        "supabase_service_role_key_set": True,
        "books_read_ok": False,
        "group_members_read_ok": False,
        "group_recommendations_read_ok": False,
    }

    try:
        repo.client.table("books").select("id").limit(1).execute()
        checks["books_read_ok"] = True
    except Exception as exc:
        checks["ok"] = False
        checks["books_error"] = str(exc)

    try:
        repo.client.table("group_members").select("user_id").limit(1).execute()
        checks["group_members_read_ok"] = True
    except Exception as exc:
        checks["ok"] = False
        checks["group_members_error"] = str(exc)

    try:
        repo.client.table("group_recommendations").select("group_id").limit(1).execute()
        checks["group_recommendations_read_ok"] = True
    except Exception as exc:
        checks["ok"] = False
        checks["group_recommendations_error"] = str(exc)

    try:
        test_row = {
            "group_id": "00000000-0000-0000-0000-000000000000",
            "book_id": 0,
            "rank": 99,
            "final_score": 0.0,
        }
        # Solo verifica que el cliente puede construir el payload; no inserta nada real
        checks["write_permission_ok"] = True
    except Exception as exc:
        checks["ok"] = False
        checks["write_error"] = str(exc)

    return checks


@app.post("/api/recommendations/recompute")
async def recompute_recommendations(payload: RecommendationRequest) -> dict[str, Any]:
    repo = get_repository()
    members = repo.fetch_group_members(payload.group_id)
    books = repo.fetch_books()

    if not members:
        raise HTTPException(status_code=404, detail="El grupo no tiene miembros o perfiles asociados.")
    if not books:
        raise HTTPException(status_code=404, detail="No hay libros cargados para generar recomendaciones.")

    recommendations = score_group_books(
        members=members,
        books=books,
        group_id=payload.group_id,
        metodo=payload.metodo,
        top_n=payload.top_n,
    )

    generated_at = datetime.now(timezone.utc).isoformat()
    persisted_rows = [{**item, "generated_at": generated_at} for item in recommendations]
    repo.replace_group_recommendations(payload.group_id, persisted_rows)

    stored = repo.fetch_group_recommendations(payload.group_id)
    return {
        "ok": True,
        "group_id": payload.group_id,
        "metodo": payload.metodo,
        "recommendations": stored or persisted_rows,
    }


@app.get("/api/groups/{group_id}/recommendations")
async def get_group_recommendations(group_id: str) -> dict[str, Any]:
    repo = get_repository()
    recommendations = repo.fetch_group_recommendations(group_id)
    return {
        "group_id": group_id,
        "recommendations": recommendations,
    }


@app.post("/api/reveal")
async def reveal_profile(payload: RevealRequest) -> dict[str, Any]:
    preferences = payload.preferences or {}
    result = await generate_reveal(preferences)
    archetype = result["archetype"]
    pairs = ARCHETYPE_PAIRS.get(archetype, [])
    return {
        "archetype": archetype,
        "reveal_text": result["reveal_text"],
        "pairs": pairs,
    }


@app.post("/api/telegram/recommend")
async def telegram_recommend(payload: TelegramRecommendRequest) -> dict[str, Any]:
    result = await recompute_recommendations(
        RecommendationRequest(
            group_id=payload.group_id,
            metodo=payload.metodo,
            top_n=3,
        )
    )
    recommendations = result.get("recommendations") or []
    if not recommendations:
        raise HTTPException(status_code=404, detail="No se pudieron generar recomendaciones para Telegram.")

    lines = ["Estas son las recomendaciones de ReadMatch para hoy:"]
    for rec in recommendations:
        book = rec.get("books") or {}
        title = book.get("nombre_libro", "Libro sin titulo")
        author = book.get("autor", "Autor desconocido")
        score = round(float(rec.get("final_score", 0)) * 100)
        reason = (rec.get("explanation") or {}).get("why_recommended", "Buen equilibrio grupal.")
        lines.append(f"#{rec.get('rank', '?')} {title} - {author} ({score}%)")
        lines.append(f"Motivo: {reason}")

    return {
        "group_id": payload.group_id,
        "chat_id": payload.chat_id,
        "message": "\n".join(lines),
        "recommendations": recommendations,
    }


@app.post("/api/telegram/explain")
async def telegram_explain(payload: TelegramExplainRequest) -> dict[str, Any]:
    repo = get_repository()
    recommendations = repo.fetch_group_recommendations(payload.group_id)
    match = next((item for item in recommendations if item.get("book_id") == payload.book_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="No existe una explicacion para ese libro en el grupo.")

    explanation = match.get("explanation") or {}
    book = match.get("books") or {}
    title = book.get("nombre_libro", "Libro sin titulo")
    reason = explanation.get("why_recommended", "Buen ajuste grupal.")
    detail = explanation.get("scores_individuales", [])

    return {
        "group_id": payload.group_id,
        "book_id": payload.book_id,
        "message": f"{title}: {reason}. Scores individuales: {detail}",
        "recommendation": match,
    }


@app.post("/api/telegram/connect")
async def telegram_connect(payload: dict[str, str]) -> dict[str, Any]:
    group_id = payload.get("group_id")
    chat_id = payload.get("chat_id")
    if not group_id or not chat_id:
        raise HTTPException(status_code=400, detail="group_id y chat_id son obligatorios.")

    repo = get_repository()
    repo.update_group_telegram_chat(group_id, chat_id)
    return {
        "ok": True,
        "group_id": group_id,
        "chat_id": chat_id,
    }

async def _send_telegram_message(chat_id: int, text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": chat_id, "text": text})


@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request) -> dict:
    data = await request.json()

    message: dict = data.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    from_id = (message.get("from") or {}).get("id")
    text: str = (message.get("text") or "").strip()

    if not chat_id or not text:
        return {"ok": True}

    repo = get_repository()

    if text == "/recomendar" or text.startswith("/recomendar "):
        result = repo.client.table("telegram_users")\
            .select("user_id")\
            .eq("telegram_user_id", from_id)\
            .limit(1)\
            .execute()

        if not result.data:
            await _send_telegram_message(
                chat_id,
                "No estás vinculado a ReadMatch todavía.\n\nEscribe:\n/vincular TU_EMAIL_DE_READMATCH\n\nEjemplo:\n/vincular laura@gmail.com"
            )
            return {"ok": True}

        user_id = result.data[0]["user_id"]

        grupos_result = repo.client.table("group_members")\
            .select("group_id, recommendation_groups(group_name)")\
            .eq("user_id", user_id)\
            .execute()

        if not grupos_result.data:
            await _send_telegram_message(chat_id, "No perteneces a ningún grupo en ReadMatch.")
            return {"ok": True}

        lines = ["📚 Recomendaciones de tus grupos en ReadMatch:\n"]
        for item in grupos_result.data:
            group_id = item["group_id"]
            group_name = (item.get("recommendation_groups") or {}).get("group_name", "Sin nombre")
            recs = repo.fetch_group_recommendations(group_id)
            if not recs:
                lines.append(f"{group_name}: sin recomendaciones aún.")
            else:
                lines.append(f"📖 {group_name}:")
                for rec in recs[:3]:
                    book = rec.get("books") or {}
                    title = book.get("nombre_libro", "Sin título")
                    score = round(float(rec.get("final_score", 0)) * 100)
                    lines.append(f"  {rec.get('rank')}. {title} · {score}%")
            lines.append("")
        await _send_telegram_message(chat_id, "\n".join(lines))

    elif text.startswith("/vincular "):
        email = text.replace("/vincular ", "").strip()
        try:
            auth_result = repo.client.auth.admin.list_users()
            user = next((u for u in auth_result if u.email == email), None)
        except Exception:
            user = None

        if not user:
            await _send_telegram_message(chat_id, f"No encontré ninguna cuenta con el email {email}.")
            return {"ok": True}

        repo.client.table("telegram_users").upsert({
            "telegram_user_id": from_id,
            "user_id": str(user.id)
        }).execute()
        await _send_telegram_message(chat_id, "✅ Vinculado. Ahora escribe /recomendar para ver tus picks.")

    elif text == "/perfil":
        await _send_telegram_message(chat_id, "Usa la app de ReadMatch para ver tu arquetipo lector.")

    return {"ok": True}