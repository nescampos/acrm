# Elastic CRM - Multi-Agent System with Elastic Agent Builder

Sistema multi-agente con orquestador para CRM agéntico, integrado con **Elasticsearch** y **Elastic Agent Builder**. Gestiona clientes, ventas, soporte y marketing mediante agentes especializados que utilizan búsqueda semántica y RAG sobre datos CRM almacenados en Elasticsearch.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRM Orchestrator                             │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐ │
│  │  Registro   │  Tareas     │  Clientes   │  Estado         │ │
│  │  Agentes    │  Cola       │  (Elastic)  │  Global         │ │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Elastic Agent Builder                              │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐ │
│  │  Semantic   │  RAG        │  Context    │  Tools          │ │
│  │  Search     │  Retrieval  │  Building   │  Integration    │ │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Elasticsearch Cluster                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ crm_customers│ │ crm_tickets  │ │ crm_         │            │
│  │              │ │              │ │ interactions │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐                                              │
│  │ crm_campaigns│                                              │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
Elastic/
├── agents/                 # Agentes base y especializados
│   ├── base.py            # Clase base abstracta
│   ├── sales.py           # Agente de Ventas (standard)
│   ├── support.py         # Agente de Soporte (standard)
│   ├── marketing.py       # Agente de Marketing (standard)
│   └── specialized.py     # Exportaciones
├── elastic/               # Integración con Elastic Stack
│   ├── __init__.py        # Módulo Elastic
│   ├── client.py          # Cliente Elasticsearch
│   ├── models.py          # Modelos de datos CRM
│   ├── repository.py      # Repositorios CRUD
│   └── agent_builder.py   # Elastic Agent Builder
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
├── .env.example           # Variables de entorno ejemplo
└── README.md              # Documentación
```

## 🚀 Instalación

### 1. Requisitos previos

- Python 3.10+
- Elasticsearch 8.x (local o Elastic Cloud)

### 2. Activar entorno virtual:
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno:
```bash
# Copiar archivo de ejemplo
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Editar `.env` con tu configuración de Elastic:
```env
# Elastic Stack Configuration
ELASTIC_HOST=http://localhost:9200
ELASTIC_USER=elastic
ELASTIC_PASSWORD=tu_password
ELASTIC_VERIFY_CERTS=false

# Kibana - Elastic Agent Builder API
KIBANA_HOST=http://localhost:5601
KIBANA_API_KEY=your_kibana_api_key
# KIBANA_SPACE=default

# LLM Configuration (para Elastic Agent Builder)
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
```

## 💡 Uso Básico

### Ejecutar demostración:
```bash
python main.py
```

### Uso programático:
```python
import asyncio
from elastic import (
    elastic_client,
    CustomerRepository,
    Customer,
    create_elastic_sales_agent,
)
from orchestrator import CRMOrchestrator

async def main():
    # Conectar a Elasticsearch
    await elastic_client.ping()
    
    # Crear repositorio
    customer_repo = CustomerRepository()
    await customer_repo.initialize()
    
    # Agregar cliente
    customer = Customer(
        name="Juan Pérez",
        email="juan@example.com",
        company="TechCorp",
        status="lead",
        lead_score=75,
    )
    await customer_repo.create(customer)
    
    # Búsqueda en Elastic
    results = await customer_repo.find_by_email("juan@example.com")
    print(f"Encontrado: {results.name}")
    
    # Crear agente Elastic
    orchestrator = CRMOrchestrator()
    agent = create_elastic_sales_agent()
    await orchestrator.register_agent(agent)
    
    # Analizar cliente con RAG
    result = await agent.execute({
        "action": "analyze",
        "customer_id": customer.customer_id,
    })
    print(f"Análisis: {result.data}")
    
    # Limpiar
    await orchestrator.shutdown()
    await elastic_client.close()

asyncio.run(main())
```

## 🤖 Elastic Agent Builder

El **Elastic Agent Builder** permite crear agentes que utilizan Elasticsearch para:

### Características

| Característica | Descripción |
|---------------|-------------|
| **Semantic Search** | Búsqueda full-text con fuzzy matching en todos los índices CRM |
| **RAG** | Retrieval Augmented Generation con contexto de Elastic |
| **Aggregations** | Análisis de datos con agregaciones de Elasticsearch |
| **Context Building** | Construcción automática de contexto para LLMs |

### Acciones disponibles:

```python
# Búsqueda semántica
result = await agent.execute({
    "action": "search",
    "query": "cliente enterprise interesado",
    "index": "customers",
    "top_k": 5,
})

# Análisis de cliente con contexto
result = await agent.execute({
    "action": "analyze",
    "customer_id": "customer-123",
    "include_interactions": True,
    "include_tickets": True,
})

# Agregaciones
result = await agent.execute({
    "action": "aggregate",
    "index": "customers",
    "aggregation_type": "terms",
    "field": "status",
})

# Recuperar contexto para RAG
result = await agent.execute({
    "action": "retrieve_context",
    "query": "historial de compras del cliente",
    "context_types": ["customers", "interactions", "tickets"],
})
```

### Crear agentes personalizados:

```python
from elastic import ElasticAgentBuilder, ElasticAgentConfig
from elastic import CustomerRepository, TicketRepository

config = ElasticAgentConfig(
    enable_semantic_search=True,
    enable_rag=True,
    top_k_results=10,
)

agent = ElasticAgentBuilder("mi_agente") \
    .with_config(config) \
    .with_repository("customers", CustomerRepository()) \
    .with_repository("tickets", TicketRepository()) \
    .with_description("Mi agente personalizado") \
    .build()
```

### API de Kibana (Elastic Agent Builder)

El proyecto integra la [API REST de Elastic Agent Builder en Kibana](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/kibana-api) para gestionar agentes, tools y conversaciones de forma programática.

**Configuración** (en `.env` o `config/config.yaml`):

```env
KIBANA_HOST=http://localhost:5601
KIBANA_API_KEY=tu_api_key_de_kibana
# KIBANA_SPACE=default   # opcional, para espacios no por defecto
```

**Cliente y gestión de agentes/tools:**

```python
from elastic import (
    get_kibana_client,
    KibanaAgentBuilderClient,
    KibanaAgentWrapper,
    create_kibana_agent_wrapper,
    build_crm_agent_payload,
)

# Cliente (None si no hay KIBANA_HOST + KIBANA_API_KEY)
client = get_kibana_client()
if client:
    # Listar agentes y tools
    agents = await client.list_agents()
    tools = await client.list_tools()

    # Crear un agente CRM en Kibana
    payload = build_crm_agent_payload(
        agent_id="crm-sales-agent",
        name="Ventas CRM",
        description="Ayuda a buscar y analizar clientes en índices crm_*",
        instructions="Eres un asistente de ventas. Usa las herramientas de búsqueda para consultar índices crm_customers, crm_tickets, crm_interactions.",
    )
    await client.create_agent(payload)

    # Chat con el agente (converse)
    response = await client.converse(
        agent_id="crm-sales-agent",
        input_text="¿Cuántos clientes hay en estado lead?",
    )
```

**Wrapper para el orquestador:** usar un agente de Kibana como un agente más del CRM:

```python
from elastic import create_kibana_agent_wrapper
from orchestrator import CRMOrchestrator

wrapper = create_kibana_agent_wrapper(
    kibana_agent_id="elastic-ai-agent",
    name="kibana_elastic_agent",
    description="Agente Elastic AI vía Kibana",
)
if wrapper:
    orchestrator = CRMOrchestrator()
    await orchestrator.register_agent(wrapper)
    result = await wrapper.execute({
        "input": "Busca en crm_customers los clientes con status prospect",
    })
```

**Endpoints utilizados:** `GET/POST/PUT/DELETE` para tools y agents, `POST /api/agent_builder/converse` para chat, y listado/obtención/borrado de conversaciones.

## 📊 Modelos de Datos

### Customer (crm_customers)
```python
Customer(
    customer_id="uuid",
    name="Juan Pérez",
    email="juan@example.com",
    company="TechCorp",
    status="lead",  # lead, prospect, customer, inactive, champion
    lead_score=75,
    engagement_score=60,
    lifetime_value=0.0,
    tags=["enterprise", "hot_lead"],
)
```

### Ticket (crm_tickets)
```python
Ticket(
    ticket_id="uuid",
    customer_id="customer-uuid",
    subject="Problema con login",
    description="...",
    status="open",  # open, in_progress, pending, resolved, closed
    priority="medium",  # low, medium, high, critical
    category="access_management",
    channel="email",
)
```

### Interaction (crm_interactions)
```python
Interaction(
    interaction_id="uuid",
    customer_id="customer-uuid",
    interaction_type="email",  # email, call, meeting, chat, social
    direction="inbound",  # inbound, outbound
    subject="Re: Consulta",
    content="...",
    outcome="interested",
    next_action="schedule_demo",
)
```

### Campaign (crm_campaigns)
```python
Campaign(
    campaign_id="uuid",
    name="Q1 Email Campaign",
    campaign_type="email",
    status="active",  # draft, active, paused, completed
    target_segment="enterprise",
    sent_count=100,
    opened_count=45,
    clicked_count=12,
)
```

## 🔍 Búsquedas en Elasticsearch

### Repositorio de Clientes:
```python
repo = CustomerRepository()

# Búsqueda por email
customer = await repo.find_by_email("juan@example.com")

# Búsqueda por estado
leads = await repo.find_by_status("lead")

# Búsqueda fuzzy por nombre
results = await repo.search_by_name("Juan Peres")

# Búsqueda custom
results = await repo.search({
    "bool": {
        "must": [{"match": {"company": "TechCorp"}}],
        "filter": [{"range": {"lead_score": {"gte": 50}}}]
    }
})
```

### Repositorio de Tickets:
```python
repo = TicketRepository()

# Tickets de un cliente
tickets = await repo.find_by_customer("customer-uuid")

# Tickets abiertos
open_tickets = await repo.find_open_tickets()

# Tickets con SLA vencido
overdue = await repo.find_overdue_tickets()
```

### Repositorio de Interacciones:
```python
repo = InteractionRepository()

# Historial de un cliente
history = await repo.find_by_customer("customer-uuid")

# Interacciones recientes (últimos 7 días)
recent = await repo.find_recent("customer-uuid", days=7)
```

## ⚙️ Configuración

### config/config.yaml
```yaml
# Elastic Stack
elastic:
  host: http://localhost:9200
  user: elastic
  password: changeme
  verify_certs: false
  indices:
    customers: crm_customers
    tickets: crm_tickets
    interactions: crm_interactions
    campaigns: crm_campaigns

# LLM para Elastic Agent Builder
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7

# Agentes
agents:
  sales:
    type: elastic  # elastic o standard
    semantic_search: true
    rag_enabled: true
```

### Elastic Cloud (alternativa):
```env
ELASTIC_CLOUD_ID=your_cloud_id:region
ELASTIC_CLOUD_API_KEY=your_api_key
```

## 📈 Casos de Uso

### 1. Ventas - Calificación de Leads con contexto
```python
agent = create_elastic_sales_agent()
result = await agent.execute({
    "action": "analyze",
    "customer_id": customer_id,
})
# Retorna: health_score, recommendations, historial completo
```

### 2. Soporte - Búsqueda de tickets similares
```python
agent = create_elastic_support_agent()
result = await agent.execute({
    "action": "search",
    "query": "problema login contraseña incorrecta",
    "index": "tickets",
})
# Retorna: tickets similares para resolución rápida
```

### 3. Marketing - Segmentación con agregaciones
```python
repo = CustomerRepository()
segments = await repo.aggregate({
    "status_breakdown": {
        "terms": {"field": "status"}
    },
    "avg_engagement_by_status": {
        "terms": {"field": "status"},
        "aggs": {
            "avg_engagement": {"avg": {"field": "engagement_score"}}
        }
    }
})
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

### Docker para Elasticsearch local:
```bash
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.11.0
```

## 📝 Licencia

MIT License
