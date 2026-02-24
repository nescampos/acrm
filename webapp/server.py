from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Cookie, FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from loguru import logger
from markdownify import markdownify as md

from main import ElasticCRMApplication


@dataclass
class ChatRequest:
    message: str


def _extract_text(payload: Any) -> str:
    """
    Extrae el mensaje de la respuesta del agente de Kibana.
    
    La respuesta de Kibana tiene el formato:
    {
        "response": {
            "message": "contenido del mensaje"
        },
        ...
    }
    """
    if not isinstance(payload, dict):
        if isinstance(payload, str):
            return payload
        return json.dumps(payload, ensure_ascii=False, indent=2)
    
    # Buscar el mensaje en response.message (formato de Kibana)
    if "response" in payload and isinstance(payload["response"], dict):
        message = payload["response"].get("message")
        if isinstance(message, str):
            return message
    
    # Fallback: buscar message directo
    message = payload.get("message")
    if isinstance(message, str):
        return message
    
    # Si no hay mensaje, retornar el payload completo
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _markdown_to_html(text: str) -> str:
    """
    Convierte texto markdown a HTML para mostrar en la web.
    """
    if not text:
        return ""
    
    # Preprocesar el texto para asegurar formato correcto
    # Convertir dobles saltos de línea a <br> para preservar párrafos
    text = text.replace('\n\n', '<br><br>')
    
    # Convertir markdown a HTML
    html = md(text, 
              heading_style="ATX",
              bullets="*",
              strong_em_symbol="*",
              em_symbol="*",
              convert=['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                      'strong', 'em', 'u', 's', 'code', 'pre',
                      'ul', 'ol', 'li', 'blockquote', 'table', 'thead', 
                      'tbody', 'tr', 'th', 'td', 'hr', 'br'])
    
    # Limpiar y mejorar el HTML con estilos
    html = html.replace("<table>", '<table style="border-collapse: collapse; width: 100%; margin: 8px 0;">')
    html = html.replace("<th>", '<th style="border: 1px solid #223255; padding: 8px; text-align: left; background: #1b2a4d;">')
    html = html.replace("<td>", '<td style="border: 1px solid #223255; padding: 8px;">')
    html = html.replace("<ul>", '<ul style="margin: 8px 0; padding-left: 20px;">')
    html = html.replace("<ol>", '<ol style="margin: 8px 0; padding-left: 20px;">')
    html = html.replace("<li>", '<li style="margin: 4px 0;">')
    html = html.replace("<blockquote>", '<blockquote style="border-left: 3px solid #2a3c64; padding-left: 12px; margin: 8px 0; color: #9fb2d0;">')
    html = html.replace("<code>", '<code style="background: #1b2a4d; padding: 2px 6px; border-radius: 4px; font-family: monospace;">')
    html = html.replace("<pre>", '<pre style="background: #1b2a4d; padding: 12px; border-radius: 8px; overflow-x: auto; margin: 8px 0;">')
    html = html.replace("<hr>", '<hr style="border: 1px solid #223255; margin: 16px 0;">')
    html = html.replace("<p>", '<p style="margin: 8px 0;">')
    
    return html


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa una vez: índices + agentes Kibana + orquestador
    crm = ElasticCRMApplication()
    await crm.initialize()

    app.state.crm = crm
    # session_id -> { agent_name -> conversation_id }
    app.state.sessions: dict[str, dict[str, str]] = {}
    logger.info("Webapp initialized")
    try:
        yield
    finally:
        await crm.shutdown()
        logger.info("Webapp shutdown complete")


app = FastAPI(title="Elastic CRM Web", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def index():
    # UI mínima (sin dependencias externas)
    return HTMLResponse(
        """
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Elastic CRM Chat</title>
    <style>
      :root { color-scheme: light; }
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 0; background: #0b1220; color: #e6edf7; }
      .wrap { max-width: 920px; margin: 0 auto; padding: 24px; }
      .card { background: #121b2f; border: 1px solid #223255; border-radius: 14px; padding: 18px; }
      h1 { font-size: 18px; margin: 0 0 12px; }
      .sub { color: #9fb2d0; font-size: 13px; margin: 0 0 14px; }
      #log { height: 55vh; overflow: auto; padding: 12px; background: #0e1730; border: 1px solid #223255; border-radius: 12px; }
      .msg { margin: 10px 0; line-height: 1.35; }
      .me { color: #d7e3ff; }
      .bot { color: #c7f0d8; }
      .meta { color: #94a6c6; font-size: 12px; margin-bottom: 4px; }
      .row { display: flex; gap: 10px; margin-top: 12px; }
      textarea { flex: 1; resize: none; height: 70px; padding: 10px; border-radius: 12px; border: 1px solid #223255; background: #0e1730; color: #e6edf7; }
      button { width: 140px; border-radius: 12px; border: 1px solid #2a3c64; background: #1b2a4d; color: #e6edf7; font-weight: 600; cursor: pointer; }
      button:disabled { opacity: 0.6; cursor: not-allowed; }
      .bar { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: 10px; }
      .pill { font-size: 12px; padding: 6px 10px; border-radius: 999px; border: 1px solid #223255; background: #0e1730; color: #9fb2d0; }
      a { color: #9fc2ff; text-decoration: none; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>Elastic CRM Chat</h1>
        <p class="sub">Router (OpenAI) → Kibana agent (Agent Builder). Commands: <span class="pill">/agents</span></p>
        <div id="log"></div>
        <div class="row">
          <textarea id="input" placeholder="Write your request…"></textarea>
          <button id="send">Send</button>
        </div>
        <div class="bar">
          <span class="pill" id="status">Ready</span>
          <a href="/docs" target="_blank">API docs</a>
        </div>
      </div>
    </div>
    <script>
      const log = document.getElementById('log');
      const input = document.getElementById('input');
      const send = document.getElementById('send');
      const status = document.getElementById('status');

      function addMsg(who, meta, content, isHtml = false) {
        const div = document.createElement('div');
        div.className = 'msg ' + (who === 'me' ? 'me' : 'bot');
        
        if (isHtml) {
          div.innerHTML = `<div class="meta">${meta}</div><div>${content}</div>`;
        } else {
          div.innerHTML = `<div class="meta">${meta}</div><div style="white-space: pre-wrap">${content}</div>`;
        }
        
        log.appendChild(div);
        log.scrollTop = log.scrollHeight;
      }

      async function postChat(message) {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message})
        });
        return await res.json();
      }

      async function handleSend() {
        const message = input.value.trim();
        if (!message) return;
        input.value = '';
        addMsg('me', 'Tú', message);
        send.disabled = true;
        status.textContent = 'Procesando…';
        try {
          if (message === '/agents') {
            const res = await fetch('/api/agents');
            const data = await res.json();
            addMsg('bot', 'Sistema', JSON.stringify(data, null, 2));
            return;
          }
          const data = await postChat(message);
          if (data.ok) {
            console.log('Debug info:', data.debug);
            console.log('All data:', data);
            addMsg('bot', `Agente: ${data.agent}`, data.html || data.text, true);
          } else {
            addMsg('bot', 'Error', data.error || 'Error desconocido');
          }
        } catch (e) {
          addMsg('bot', 'Error', String(e));
        } finally {
          send.disabled = false;
          status.textContent = 'Ready';
        }
      }

      send.addEventListener('click', handleSend);
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
          handleSend();
        }
      });
    </script>
  </body>
</html>
        """.strip()
    )


@app.get("/api/agents")
async def api_agents(request: Request):
    crm: ElasticCRMApplication = request.app.state.crm
    return JSONResponse(crm.orchestrator.list_agents())  # type: ignore[union-attr]


@app.post("/api/chat")
async def api_chat(
    request: Request,
    response: Response,
    payload: dict,
    crm_session: Optional[str] = Cookie(default=None),
):
    crm: ElasticCRMApplication = request.app.state.crm
    orchestrator = crm.orchestrator
    if orchestrator is None:
        return JSONResponse({"ok": False, "error": "Orchestrator not initialized"}, status_code=500)

    message = (payload.get("message") or "").strip()
    if not message:
        return JSONResponse({"ok": False, "error": "Missing message"}, status_code=400)

    session_id = crm_session or str(uuid.uuid4())
    if crm_session is None:
        response.set_cookie("crm_session", session_id, httponly=True, samesite="lax")

    sessions: dict[str, dict[str, str]] = request.app.state.sessions
    session_state = sessions.setdefault(session_id, {})

    try:
        route = await orchestrator.route_agent(message)
        agent_name = route.agent_name
        conv_id = session_state.get(agent_name)

        result = await orchestrator.execute_on_agent(
            agent_name=agent_name,
            user_input=message,
            conversation_id=conv_id,
        )

        if result.success and isinstance(result.data, dict):
            new_conv = result.data.get("conversation_id") or result.data.get("conversationId")
            if isinstance(new_conv, str) and new_conv:
                session_state[agent_name] = new_conv

        if not result.success:
            return JSONResponse(
                {"ok": False, "agent": agent_name, "error": result.error},
                status_code=500,
            )

        return JSONResponse(
            {
                "ok": True,
                "agent": agent_name,
                "reasoning": route.reasoning,
                "text": _extract_text(result.data),
                "html": _markdown_to_html(_extract_text(result.data)),
                "debug": {
                    "raw_text": _extract_text(result.data),
                    "text_length": len(_extract_text(result.data)),
                    "html_length": len(_markdown_to_html(_extract_text(result.data)))
                },
                "raw": result.data,
            }
        )
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

