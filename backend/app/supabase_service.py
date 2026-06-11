from __future__ import annotations

from typing import Any

from supabase import Client, create_client

from .config import settings


try:
    from postgrest.exceptions import APIError as PostgrestAPIError
except Exception:
    PostgrestAPIError = None


def get_supabase_client() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY son obligatorios")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


class SupabaseRepository:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase_client()

    def _raise_supabase_error(self, action: str, exc: Exception) -> None:
        if PostgrestAPIError and isinstance(exc, PostgrestAPIError):
            message = getattr(exc, "message", None) or str(exc)
            raise RuntimeError(f"Supabase error ({action}): {message}") from exc
        raise RuntimeError(f"Supabase error ({action}): {type(exc).__name__}") from exc

    def fetch_group_members(self, group_id: str) -> list[dict[str, Any]]:
        try:
            members_response = (
                self.client.table("group_members")
                .select("user_id, role, influence_weight")
                .eq("group_id", group_id)
                .execute()
            )
            members = members_response.data or []
            user_ids = [row.get("user_id") for row in members if row.get("user_id")]
            if not user_ids:
                return members

            preferences_response = (
                self.client.table("user_preferences")
                .select("user_id, favorite_genres, narrative_styles, group_values, depth_preference, openness_score, favorite_authors, preferred_languages, preferred_complexity")
                .in_("user_id", user_ids)
                .execute()
            )
            preferences_rows = preferences_response.data or []
            preferences_by_user_id = {row.get("user_id"): row for row in preferences_rows if row.get("user_id")}

            return [
                {
                    **member,
                    "user_preferences": preferences_by_user_id.get(member.get("user_id")) or {},
                }
                for member in members
            ]
        except Exception as exc:
            self._raise_supabase_error("fetch_group_members", exc)
            return []

    def fetch_books(self, limit: int = 1000) -> list[dict[str, Any]]:
        try:
            response = (
                self.client.table("books")
                .select(
                    "id, nombre_libro, autor, genero, "
                    "complejidad_narrativa, trope, tags, "
                    "popularity_score, content_vector, idiomas"
                )
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception as exc:
            self._raise_supabase_error("fetch_books", exc)
            return []

    def replace_group_recommendations(self, group_id: str, rows: list[dict[str, Any]]) -> None:
        try:
            (
                self.client.table("group_recommendations")
                .delete()
                .eq("group_id", group_id)
                .execute()
            )
            if rows:
                self.client.table("group_recommendations").insert(rows).execute()
        except Exception as exc:
            self._raise_supabase_error("replace_group_recommendations", exc)

    def fetch_group_recommendations(self, group_id: str) -> list[dict[str, Any]]:
        try:
            response = (
                self.client.table("group_recommendations")
                .select(
                    "group_id, book_id, rank, final_score, content_score, collaborative_score, popularity_score, fairness_score, member_coverage, per_member_scores, explanation, generated_at, books(nombre_libro, autor, genero)"
                )
                .eq("group_id", group_id)
                .order("rank")
                .execute()
            )
            return response.data or []
        except Exception as exc:
            self._raise_supabase_error("fetch_group_recommendations", exc)
            return []

    def fetch_user_preferences(self, user_id: str) -> dict[str, Any]:
        try:
            response = (
                self.client.table("user_preferences")
                .select("*")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            return response.data or {}
        except Exception as exc:
            self._raise_supabase_error("fetch_user_preferences", exc)
            return {}

    def update_group_telegram_chat(self, group_id: str, chat_id: str) -> None:
        try:
            (
                self.client.table("recommendation_groups")
                .update({"telegram_chat_id": chat_id})
                .eq("id", group_id)
                .execute()
            )
        except Exception as exc:
            self._raise_supabase_error("update_group_telegram_chat", exc)

    def fetch_group_by_telegram_chat(self, chat_id: str) -> dict[str, Any] | None:
        try:
            response = (
                self.client.table("recommendation_groups")
                .select("*")
                .eq("telegram_chat_id", chat_id)
                .limit(1)
                .execute()
            )
            data = response.data or []
            return data[0] if data else None
        except Exception as exc:
            self._raise_supabase_error("fetch_group_by_telegram_chat", exc)
            return None
