"""
Cliente para la API de Elastic Agent Builder en Kibana.

Ref: https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/kibana-api
Ref: https://www.elastic.co/docs/api/doc/kibana/group/endpoint-agent-builder

Permite gestionar tools, agentes y conversaciones de forma programática.
"""

import asyncio
from typing import Any, Optional

import aiohttp
from loguru import logger


class KibanaAgentBuilderClient:
    """
    Cliente asíncrono para la API REST de Elastic Agent Builder (Kibana).

    Requiere KIBANA_HOST y KIBANA_API_KEY. Opcionalmente KIBANA_SPACE para espacios.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        space: str = "",
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.space = (space or "").strip()
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    def _path(self, path: str) -> str:
        """Construye la URL base con espacio si aplica."""
        if self.space:
            return f"{self.base_url}/s/{self.space}/api/agent_builder{path}"
        return f"{self.base_url}/api/agent_builder{path}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"ApiKey {self.api_key}",
            "kbn-xsrf": "true",
            "Content-Type": "application/json",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        **kwargs: Any,
    ) -> tuple[int, Any]:
        session = await self._get_session()
        url = self._path(path)
        headers = self._headers()
        try:
            async with session.request(
                method, url, headers=headers, json=json, **kwargs
            ) as resp:
                data = None
                if resp.content_type and "application/json" in resp.content_type:
                    try:
                        data = await resp.json()
                    except Exception:
                        data = await resp.text()
                else:
                    data = await resp.text()
                return resp.status, data
        except asyncio.TimeoutError:
            logger.error("Kibana Agent Builder API timeout")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Kibana Agent Builder API error: {e}")
            raise

    async def close(self) -> None:
        """Cierra la sesión HTTP."""
        if self._session and not self._session.closed:
            await self._session.close()

    # ---------- Tools ----------

    async def list_tools(self) -> list[dict]:
        """GET /api/agent_builder/tools - Lista todas las tools."""
        status, data = await self._request("GET", "/tools")
        if status != 200:
            raise RuntimeError(f"list_tools failed: {status} {data}")
        return data if isinstance(data, list) else (data.get("tools") or [])

    async def get_tool(self, tool_id: str) -> dict:
        """GET /api/agent_builder/tools/{id}."""
        status, data = await self._request("GET", f"/tools/{tool_id}")
        if status != 200:
            raise RuntimeError(f"get_tool failed: {status} {data}")
        return data if isinstance(data, dict) else {}

    async def create_tool(self, body: dict) -> dict:
        """POST /api/agent_builder/tools - Crea una tool."""
        status, data = await self._request("POST", "/tools", json=body)
        if status not in (200, 201):
            raise RuntimeError(f"create_tool failed: {status} {data}")
        return data if isinstance(data, dict) else {}

    async def update_tool(self, tool_id: str, body: dict) -> dict:
        """PUT /api/agent_builder/tools/{id}."""
        status, data = await self._request("PUT", f"/tools/{tool_id}", json=body)
        if status != 200:
            raise RuntimeError(f"update_tool failed: {status} {data}")
        return data if isinstance(data, dict) else {}

    async def delete_tool(self, tool_id: str) -> None:
        """DELETE /api/agent_builder/tools/{id}."""
        status, data = await self._request("DELETE", f"/tools/{tool_id}")
        if status not in (200, 204):
            raise RuntimeError(f"delete_tool failed: {status} {data}")

    async def execute_tool(self, tool_id: str, tool_params: dict) -> dict:
        """POST /api/agent_builder/tools/_execute."""
        status, data = await self._request(
            "POST",
            "/tools/_execute",
            json={"tool_id": tool_id, "tool_params": tool_params},
        )
        if status != 200:
            raise RuntimeError(f"execute_tool failed: {status} {data}")
        return data if isinstance(data, dict) else {}

    # ---------- Agents ----------

    async def list_agents(self) -> list[dict]:
        """GET /api/agent_builder/agents."""
        status, data = await self._request("GET", "/agents")
        if status != 200:
            raise RuntimeError(f"list_agents failed: {status} {data}")
        return data if isinstance(data, list) else (data.get("agents") or [])

    async def get_agent(self, agent_id: str) -> Optional[dict]:
        """
        GET /api/agent_builder/agents/{id}.

        Devuelve:
          - dict con los datos del agente si existe (200)
          - None si el agente no existe (404)
        Lanza RuntimeError para otros códigos de estado.
        """
        status, data = await self._request("GET", f"/agents/{agent_id}")
        if status == 404:
            return None
        if status != 200:
            raise RuntimeError(f"get_agent failed: {status} {data}")
        return data if isinstance(data, dict) else {}

    async def create_agent(self, body: dict) -> dict:
        """POST /api/agent_builder/agents."""
        status, data = await self._request("POST", "/agents", json=body)
        if status not in (200, 201):
            raise RuntimeError(f"create_agent failed: {status} {data}")
        return data if isinstance(data, dict) else {}

    async def update_agent(self, agent_id: str, body: dict) -> dict:
        """PUT /api/agent_builder/agents/{id}."""
        status, data = await self._request("PUT", f"/agents/{agent_id}", json=body)
        if status != 200:
            raise RuntimeError(f"update_agent failed: {status} {data}")
        return data if isinstance(data, dict) else {}

    async def delete_agent(self, agent_id: str) -> None:
        """DELETE /api/agent_builder/agents/{id}."""
        status, data = await self._request("DELETE", f"/agents/{agent_id}")
        if status not in (200, 204):
            raise RuntimeError(f"delete_agent failed: {status} {data}")

    # ---------- Chat / Converse ----------

    async def converse(
        self,
        agent_id: str,
        input_text: str,
        conversation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> dict:
        """
        POST /api/agent_builder/converse - Envía un mensaje y recibe la respuesta completa.
        """
        body: dict = {"agent_id": agent_id, "input": input_text}
        if conversation_id:
            body["conversation_id"] = conversation_id
        body.update(kwargs)
        status, data = await self._request("POST", "/converse", json=body)
        if status != 200:
            raise RuntimeError(f"converse failed: {status} {data}")
        return data if isinstance(data, dict) else {"raw": data}

    async def converse_async(
        self,
        agent_id: str,
        input_text: str,
        conversation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> dict:
        """POST /api/agent_builder/converse/async - Chat con streaming."""
        body = {"agent_id": agent_id, "input": input_text}
        if conversation_id:
            body["conversation_id"] = conversation_id
        body.update(kwargs)
        status, data = await self._request("POST", "/converse/async", json=body)
        if status not in (200, 201):
            raise RuntimeError(f"converse_async failed: {status} {data}")
        return data if isinstance(data, dict) else {"raw": data}

    # ---------- Conversations ----------

    async def list_conversations(self) -> list[dict]:
        """GET /api/agent_builder/conversations."""
        status, data = await self._request("GET", "/conversations")
        if status != 200:
            raise RuntimeError(f"list_conversations failed: {status} {data}")
        return data if isinstance(data, list) else (data.get("conversations") or [])

    async def get_conversation(self, conversation_id: str) -> dict:
        """GET /api/agent_builder/conversations/{id}."""
        status, data = await self._request(
            "GET", f"/conversations/{conversation_id}"
        )
        if status != 200:
            raise RuntimeError(f"get_conversation failed: {status} {data}")
        return data if isinstance(data, dict) else {}

    async def delete_conversation(self, conversation_id: str) -> None:
        """DELETE /api/agent_builder/conversations/{id}."""
        status, data = await self._request(
            "DELETE", f"/conversations/{conversation_id}"
        )
        if status not in (200, 204):
            raise RuntimeError(f"delete_conversation failed: {status} {data}")

    # ---------- A2A ----------

    async def get_a2a_config(self, agent_id: str) -> dict:
        """GET /api/agent_builder/a2a/{agentId}.json - Configuración A2A del agente."""
        status, data = await self._request("GET", f"/a2a/{agent_id}.json")
        if status != 200:
            raise RuntimeError(f"get_a2a_config failed: {status} {data}")
        return data if isinstance(data, dict) else {}
