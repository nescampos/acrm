# Elastic CRM - Multi-Agent System

Sistema multi-agente con orquestador para CRM agéntico. Gestiona clientes, ventas, soporte y marketing mediante agentes especializados coordinados por un orquestador central.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    CRM Orchestrator                         │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │  Registro   │  Tareas     │  Clientes   │  Estado     │ │
│  │  Agentes    │  Cola       │  (CRM)      │  Global     │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ SalesAgent  │ │SupportAgent │ │MarketingAgnt│
│ - Qualify   │ │ - Tickets   │ │ - Segment   │
│ - Follow-up │ │ - Classify  │ │ - Campaigns │
│ - Meetings  │ │ - Responses │ │ - Engagement│
└─────────────┘ └─────────────┘ └─────────────┘
```

## 📁 Estructura del Proyecto

```
Elastic/
├── agents/                 # Módulos de agentes
│   ├── base.py            # Clase base abstracta
│   ├── sales.py           # Agente de Ventas
│   ├── support.py         # Agente de Soporte
│   ├── marketing.py       # Agente de Marketing
│   └── specialized.py     # Exportaciones
├── orchestrator/          # Orquestador CRM
│   └── orchestrator.py    # CRMOrchestrator
├── config/                # Configuración
│   ├── __init__.py        # Config manager
│   └── config.yaml        # YAML config
├── tools/                 # Herramientas para agentes
│   └── tools.py           # BaseTool
├── utils/                 # Utilidades
│   └── logger.py          # Logging setup
├── main.py                # Punto de entrada
├── requirements.txt       # Dependencias
├── pyproject.toml         # Metadatos del proyecto
└── .env.example           # Variables de entorno ejemplo
```

## 🚀 Instalación

1. **Activar entorno virtual:**
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno:**
```bash
# Copiar archivo de ejemplo
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Editar .env con tus credenciales
```

## 💡 Uso Básico

### Ejecutar demostración:
```bash
python main.py
```

### Uso programático:
```python
import asyncio
from orchestrator import CRMOrchestrator
from agents.specialized import SalesAgent, SupportAgent, MarketingAgent

async def main():
    # Crear orquestador
    orchestrator = CRMOrchestrator()
    
    # Registrar agentes
    await orchestrator.register_agent(SalesAgent())
    await orchestrator.register_agent(SupportAgent())
    await orchestrator.register_agent(MarketingAgent())
    
    # Agregar cliente
    customer = orchestrator.add_customer({
        "name": "Juan Pérez",
        "email": "juan@example.com",
        "status": "lead"
    })
    
    # Ejecutar tarea con agente de ventas
    sales_agent = orchestrator.get_agent("sales_agent")
    result = await sales_agent.execute({
        "action": "qualify_lead",
        "customer_id": customer.customer_id,
        "data": {
            "budget": 5000,
            "has_authority": True,
            "need_score": 80,
            "timeline": "this_month"
        }
    })
    
    print(f"Calificación: {result.data}")
    
    # Limpiar
    await orchestrator.shutdown()

asyncio.run(main())
```

## 🤖 Agentes Disponibles

### SalesAgent (Ventas)
| Acción | Descripción |
|--------|-------------|
| `qualify_lead` | Califica leads usando criterios BANT |
| `follow_up` | Genera plan de seguimiento |
| `schedule_meeting` | Programa reuniones |
| `analyze` | Analiza probabilidad de cierre |

### SupportAgent (Soporte)
| Acción | Descripción |
|--------|-------------|
| `create_ticket` | Crea ticket de soporte |
| `classify` | Clasifica automáticamente incidencias |
| `suggest_response` | Sugiere respuestas basadas en categoría |
| `escalate` | Escala tickets a nivel superior |
| `resolve` | Marca tickets como resueltos |

### MarketingAgent (Marketing)
| Acción | Descripción |
|--------|-------------|
| `segment` | Segmenta audiencia por comportamiento |
| `create_campaign` | Crea campañas de marketing |
| `analyze_engagement` | Analiza nivel de engagement |
| `recommend_content` | Recomienda contenido personalizado |

## 📊 CRM Orchestrator

El orquestador proporciona:

- **Gestión de Agentes**: Registro, baja y monitoreo de agentes
- **CRM de Clientes**: Alta, actualización y listado de clientes
- **Cola de Tareas**: Distribución asíncrona de tareas a agentes
- **Estado Global**: Monitoreo centralizado del sistema

### Métodos principales:

```python
# Agentes
await orchestrator.register_agent(agent)
await orchestrator.unregister_agent("agent_name")
orchestrator.get_agent("agent_name")
orchestrator.list_agents()

# Clientes
orchestrator.add_customer({...})
orchestrator.get_customer(customer_id)
orchestrator.update_customer(customer_id, {...})
orchestrator.list_customers(status="lead")

# Tareas
await orchestrator.assign_task("sales_agent", {...}, priority=1)
await orchestrator.process_queue()  # Background

# Estado
orchestrator.get_status()
```

## ⚙️ Configuración

### config/config.yaml
```yaml
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7

agents:
  sales:
    enabled: true
    auto_qualify_leads: true
  support:
    enabled: true
    auto_classify_tickets: true
  marketing:
    enabled: true
    auto_segment: true

logging:
  level: INFO
  file: logs/app.log
```

### Variables de entorno (.env)
```env
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
TEMPERATURE=0.7
LOG_LEVEL=INFO
```

## 🧪 Desarrollo

### Instalar en modo desarrollo:
```bash
pip install -e ".[dev]"
```

### Ejecutar tests:
```bash
pytest tests/
```

### Linting:
```bash
ruff check .
black .
```

## 📝 Licencia

MIT License
