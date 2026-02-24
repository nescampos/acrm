# aCRM - Agentic CRM System with Elastic Agent Builder

A sophisticated multi-agent CRM system integrated with **Elasticsearch** and **Elastic Agent Builder**. Manages customers, sales, support, and marketing through specialized agents leveraging semantic search and RAG capabilities on CRM data stored in Elasticsearch.

This platform use **OpenAI SDK** for routing between agents, verifying the user's intent and delegating the request to the appropriate agent.

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                    CRM Orchestrator                                  │
│  ┌─────────────┬─────────────┬─────────────┬───────────────────────┐ │
│  │  Agent      │  Task       │  Customer   │  Global               │ │
│  │  Registry   │  Queue      │  (Elastic)  │  State (to implement) │ │
│  └─────────────┴─────────────┴─────────────┴───────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌────────────────────────────────────────────────────────────────┐
│              Elastic Agent Builder                             │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐ │
│  │  Semantic   │  RAG        │  Context    │  Tools          │ │
│  │  Search     │  Retrieval  │  Building   │  Integration    │ │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘ │
└────────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│                    Elasticsearch Cluster                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ crm_customers│ │ crm_tickets  │ │ crm_         │            │
│  │              │ │              │ │ interactions │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐                                              │
│  │ crm_campaigns│                                              │
│  └──────────────┘                                              │
└────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **CRM Orchestrator**
- **Agent Registry**: Manages registration and discovery of all agents
- **Task Queue**: Routes requests to appropriate agents based on OpenAI routing
- **Customer Management**: Centralized customer data access via Elasticsearch
- **Global State** (to implement): Maintains conversation context and agent states

#### 2. **Elastic Agent Builder**
- **Semantic Search**: Full-text search with fuzzy matching across all CRM indices
- **RAG (Retrieval Augmented Generation)**: Context-aware responses using Elastic data
- **Context Building**: Automatic context assembly for LLM queries
- **Tools Integration**: Native integration with Elasticsearch tools

#### 3. **Specialized Agents**
- **Sales Agent**: Lead qualification, opportunity analysis, customer scoring
- **Support Agent**: Ticket management, knowledge base search, issue resolution
- **Marketing Agent**: Campaign analysis, customer segmentation, performance metrics

## 🚀 Installation

### Prerequisites
- Python 3.10+
- Elastic Cloud (serverless project)
- OpenAI API key (for routing requests to agents)

### 1. Setup Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy environment template
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Edit `.env` with your configuration:
```env
OPENAI_API_KEY=your_openai_api_key_here

# Model configuration
LLM_MODEL=gpt-4o
TEMPERATURE=0.7


# Elastic Cloud Configuration
ELASTIC_HOST=
KIBANA_HOST=
ELASTIC_CLOUD_API_KEY=
```


## 💻 Usage Modes

### 1. Demo Mode
Runs a comprehensive demonstration with sample data:

```bash
python main.py --demo
```

**Demo Features:**
- Creates 8 sample customers with diverse profiles
- Generates 6 support tickets with various priorities
- Adds 8 customer interactions (email, calls, meetings)
- Creates 5 marketing campaigns with performance metrics
- Demonstrates all agent capabilities
- Shows advanced Elasticsearch aggregations
- Semantic search examples

### 2. Interactive Chat Mode
Command-line interface with intelligent agent routing:

```bash
python main.py --chat
```

**Chat Features:**
- OpenAI-powered agent routing
- Conversation persistence per agent
- Real-time agent responses
- Commands:
  - `/agents` - List available agents
  - `/exit` - Exit chat

**Example Chat Session:**
```
crm> Show me enterprise customers with high engagement
[crm_sales_agent] Found 3 enterprise customers with engagement scores above 80:
1. Carlos López (CloudInc) - Score: 85, Status: Customer
2. Sofia Castro (HealthTech Solutions) - Score: 95, Status: Champion
3. Roberto Silva (Enterprise Solutions) - Score: 70, Status: Prospect

crm> What marketing campaigns are currently active?
[crm_marketing_agent] Currently active campaigns:
1. "Q1 Email Campaign - Enterprise Leads" - 38.8% open rate
2. "Webinar Series - Cloud Solutions" - 39.3% open rate
```

### 3. Web Interface
Modern web UI with markdown rendering:

```bash
uvicorn webapp.server:app --reload --port 8000
```

**Web Features:**
- Real-time chat interface
- Markdown-formatted responses
- Agent routing visualization
- Session management
- Responsive dark theme
- HTML rendering of tables, lists, and formatted text

**Access:** `http://localhost:8000`

## 🤖 Elastic Agent Builder Integration


### Custom Agent Creation

```python
from elastic import ElasticAgentBuilder, ElasticAgentConfig

config = ElasticAgentConfig(
    enable_semantic_search=True,
    enable_rag=True,
    top_k_results=10,
)

agent = ElasticAgentBuilder("custom_agent") \
    .with_config(config) \
    .with_repository("customers", CustomerRepository()) \
    .with_repository("tickets", TicketRepository()) \
    .with_description("Custom agent for specific tasks") \
    .build()
```

## 📊 Data Models

### Customer Model
```python
Customer(
    customer_id="uuid",
    name="John Doe",
    email="john@example.com",
    company="TechCorp",
    status="lead",  # lead, prospect, customer, inactive, champion
    lead_score=75,
    engagement_score=60,
    lifetime_value=15000.0,
    tags=["enterprise", "hot_lead"],
    custom_fields={"industry": "Software", "employees": 500},
    created_at=datetime.now(),
    last_contacted_at=datetime.now(),
)
```

### Ticket Model
```python
Ticket(
    ticket_id="uuid",
    customer_id="customer-uuid",
    subject="Login issue",
    description="Cannot access account",
    status="open",  # open, in_progress, pending, resolved, closed
    priority="high",  # low, medium, high, critical
    category="access_management",
    channel="email",
)
```

### Interaction Model
```python
Interaction(
    interaction_id="uuid",
    customer_id="customer-uuid",
    interaction_type="email",  # email, call, meeting, chat, social
    direction="inbound",  # inbound, outbound
    subject="Product inquiry",
    content="Customer interested in enterprise features",
    outcome="interested",
    next_action="schedule_demo",
)
```

### Campaign Model
```python
Campaign(
    campaign_id="uuid",
    name="Q1 Email Campaign",
    campaign_type="email",
    status="active",  # draft, active, paused, completed
    target_segment="enterprise",
    sent_count=1000,
    opened_count=388,
    clicked_count=97,
    converted_count=15,
)
```


## ⚙️ Configuration

### Elastic Cloud Configuration
```env
ELASTIC_CLOUD_ID=your_cloud_id:region
ELASTIC_CLOUD_API_KEY=your_api_key
```

## 📈 Use Cases
1. Sales - Lead Qualification
2. Support - Ticket Resolution
3. Marketing - Campaign Analysis
4. Customer 360 View


## 🔧 API Reference

### REST API Endpoints

#### Chat Interface
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Show me enterprise customers with high engagement"
}

Response:
{
  "ok": true,
  "agent": "crm_sales_agent",
  "text": "Found 3 enterprise customers...",
  "html": "<h3>Enterprise Customers</h3><ul>...",
  "reasoning": "User is asking about enterprise customers..."
}
```


## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
