"""
Router LLM para seleccionar el agente correcto.

Este módulo implementa un "agente inicial" (punto de contacto) que, dado un
mensaje del usuario, decide a qué agente (Kibana Agent Builder) delegar.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from loguru import logger
from openai import AsyncOpenAI


@dataclass(frozen=True)
class RouteResult:
    agent_name: str
    reasoning: Optional[str] = None


class OpenAIRouter:
    """
    Router basado en OpenAI.

    Usa `response_format={"type":"json_object"}` para forzar una salida parseable.
    """

    def __init__(self, api_key: str, model: str, temperature: float = 0.0):
        if not api_key:
            raise ValueError("Missing OpenAI API key")
        if not model:
            raise ValueError("Missing OpenAI model")
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._temperature = temperature

    async def route(self, user_input: str, agents: list[dict]) -> RouteResult:
        """
        Decide el `agent_name` basándose en el texto del usuario y los agentes disponibles.

        agents: lista de dicts con al menos {"name": "...", "description": "..."}
        """
        allowed = [a.get("name") for a in agents if isinstance(a, dict) and a.get("name")]
        if not allowed:
            raise RuntimeError("No agents available to route to")

        agents_block = "\n".join(
            f'- {a.get("name")}: {a.get("description","")}'
            for a in agents
            if isinstance(a, dict) and a.get("name")
        )

        system = (
            "You are a request router for an agentic CRM. "
            "You must choose exactly ONE agent from the list to handle the user's order.\n\n"
            "Rules:\n"
            f"- Values allowed for agent_name: {', '.join(allowed)}\n"
            "- Respond ONLY valid JSON, without additional text.\n"
            "- If there is ambiguity, choose the most probable agent (do not ask questions).\n"
        )

        user = (
            "AVAILABLE AGENTS:\n"
            f"{agents_block}\n\n"
            "USER MESSAGE:\n"
            f"{user_input}\n\n"
            "Return JSON with this format:\n"
            '{"agent_name":"<one of the allowed>","reasoning":"brief"}'
        )

        # Preferimos Responses API (openai>=2), con fallback a chat.completions si fuese necesario
        try:
            resp = await self._client.responses.create(
                model=self._model,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self._temperature,
                response_format={"type": "json_object"},
            )
            text = getattr(resp, "output_text", None) or ""
        except Exception as e:
            logger.warning(f"OpenAI responses.create failed, falling back. Error: {e}")
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self._temperature,
                response_format={"type": "json_object"},
            )
            text = (resp.choices[0].message.content or "").strip()

        try:
            data = json.loads(text)
        except Exception:
            logger.error(f"Router returned non-JSON: {text!r}")
            # Fallback conservador: primer agente
            return RouteResult(agent_name=allowed[0], reasoning="fallback_non_json")

        agent_name = data.get("agent_name")
        if agent_name not in allowed:
            logger.warning(f"Router picked invalid agent_name={agent_name!r}. Allowed={allowed}")
            agent_name = allowed[0]

        return RouteResult(agent_name=agent_name, reasoning=data.get("reasoning"))

