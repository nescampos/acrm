"""
Datos de demostración para el sistema Elastic CRM.
Contiene datos de ejemplo para clientes, tickets, interacciones y campañas.
"""

from datetime import datetime, timedelta
from elastic.models import Customer, Ticket, Interaction, Campaign


def get_demo_customers() -> list[Customer]:
    """Retorna datos de demo para clientes."""
    return [
        Customer(
            name="Juan Pérez",
            email="juan.perez@techcorp.com",
            phone="+1234567890",
            company="TechCorp",
            status="lead",
            source="website",
            lead_score=75,
            engagement_score=45,
            tags=["enterprise", "hot_lead", "technology"],
            custom_fields={"industry": "Software", "employees": 500},
        ),
        Customer(
            name="María García",
            email="maria.garcia@datasoft.com",
            phone="+0987654321",
            company="DataSoft",
            status="prospect",
            source="campaign",
            lead_score=60,
            engagement_score=65,
            tags=["smb", "warm", "analytics"],
            custom_fields={"industry": "Data Analytics", "employees": 150},
        ),
        Customer(
            name="Carlos López",
            email="carlos.lopez@cloudinc.com",
            phone="+1122334455",
            company="CloudInc",
            status="customer",
            source="referral",
            lead_score=95,
            engagement_score=85,
            lifetime_value=15000.0,
            tags=["enterprise", "champion", "cloud"],
            custom_fields={"industry": "Cloud Services", "employees": 1000},
            converted_at=datetime.now() - timedelta(days=90),
        ),
        Customer(
            name="Ana Martínez",
            email="ana.martinez@startupxyz.com",
            phone="+5544332211",
            company="StartupXYZ",
            status="lead",
            source="direct",
            lead_score=45,
            engagement_score=30,
            tags=["startup", "early_stage", "mobile"],
            custom_fields={"industry": "Mobile Apps", "employees": 25},
        ),
        Customer(
            name="Roberto Silva",
            email="roberto.silva@enterprise.com",
            phone="+6677889900",
            company="Enterprise Solutions",
            status="prospect",
            source="website",
            lead_score=80,
            engagement_score=70,
            tags=["enterprise", "fortune_500", "consulting"],
            custom_fields={"industry": "Consulting", "employees": 5000},
        ),
        Customer(
            name="Laura Fernández",
            email="laura.fernandez@retail.com",
            phone="+3322114455",
            company="RetailCorp",
            status="customer",
            source="campaign",
            lead_score=90,
            engagement_score=75,
            lifetime_value=8500.0,
            tags=["retail", "ecommerce", "repeat_customer"],
            custom_fields={"industry": "Retail", "employees": 200},
            converted_at=datetime.now() - timedelta(days=45),
        ),
        Customer(
            name="Diego Herrera",
            email="diego.herrera@fintech.com",
            phone="+9988776655",
            company="FinTech Innovations",
            status="inactive",
            source="referral",
            lead_score=30,
            engagement_score=15,
            tags=["fintech", "cold_lead", "banking"],
            custom_fields={"industry": "Financial Technology", "employees": 100},
            last_contacted_at=datetime.now() - timedelta(days=120),
        ),
        Customer(
            name="Sofia Castro",
            email="sofia.castro@healthcare.com",
            phone="+1111222333",
            company="HealthTech Solutions",
            status="champion",
            source="direct",
            lead_score=100,
            engagement_score=95,
            lifetime_value=25000.0,
            tags=["healthcare", "champion", "advocate"],
            custom_fields={"industry": "Healthcare", "employees": 300},
            converted_at=datetime.now() - timedelta(days=180),
        ),
    ]


def get_demo_tickets() -> list[Ticket]:
    """Retorna datos de demo para tickets de soporte."""
    return [
        Ticket(
            subject="Problema con login",
            description="El cliente no puede acceder a su cuenta usando credenciales correctas",
            status="open",
            priority="high",
            category="access_management",
            channel="email",
        ),
        Ticket(
            subject="Consulta sobre pricing enterprise",
            description="Cliente interesado en planes enterprise para 500 usuarios",
            status="in_progress",
            priority="medium",
            category="sales",
            channel="phone",
        ),
        Ticket(
            subject="Error en integración API",
            description="La API retorna error 500 al sincronizar datos",
            status="resolved",
            priority="critical",
            category="technical_support",
            channel="chat",
        ),
        Ticket(
            subject="Solicitud de nueva funcionalidad",
            description="Cliente solicita dashboard personalizado con métricas avanzadas",
            status="pending",
            priority="low",
            category="feature_request",
            channel="email",
        ),
        Ticket(
            subject="Problema de rendimiento",
            description="Sistema lento al cargar reportes con grandes volúmenes de datos",
            status="open",
            priority="medium",
            category="performance",
            channel="phone",
        ),
        Ticket(
            subject="Facturación incorrecta",
            description="Cargo duplicado en factura del mes actual",
            status="resolved",
            priority="high",
            category="billing",
            channel="email",
        ),
    ]


def get_demo_interactions() -> list[Interaction]:
    """Retorna datos de demo para interacciones con clientes."""
    return [
        Interaction(
            interaction_type="email",
            direction="outbound",
            subject="Bienvenida al servicio",
            content="Gracias por registrarte. Aquí están los primeros pasos para comenzar...",
            outcome="delivered",
            next_action="follow_up_call",
        ),
        Interaction(
            interaction_type="call",
            direction="inbound",
            subject="Consulta sobre pricing",
            content="Cliente llamó para询问 precios de planes enterprise",
            outcome="interested",
            next_action="schedule_demo",
        ),
        Interaction(
            interaction_type="meeting",
            direction="outbound",
            subject="Demo de producto",
            content="Sesión de demostración para equipo de 10 personas",
            outcome="positive",
            next_action="send_proposal",
        ),
        Interaction(
            interaction_type="chat",
            direction="inbound",
            subject="Soporte técnico",
            content="Cliente necesita ayuda con configuración de integración",
            outcome="resolved",
            next_action="none",
        ),
        Interaction(
            interaction_type="email",
            direction="outbound",
            subject="Seguimiento post-demo",
            content="Espero que la demo haya sido útil. ¿Tienes alguna pregunta?",
            outcome="awaiting_response",
            next_action="call_if_no_reply",
        ),
        Interaction(
            interaction_type="social",
            direction="inbound",
            subject="Feedback positivo",
            content="Cliente compartió experiencia positiva en LinkedIn",
            outcome="advocate",
            next_action="request_testimonial",
        ),
        Interaction(
            interaction_type="call",
            direction="outbound",
            subject="Renovación de servicio",
            content="Contacto para renovación anual del contrato",
            outcome="renewed",
            next_action="update_contract",
        ),
        Interaction(
            interaction_type="email",
            direction="inbound",
            subject="Queja sobre servicio",
            content="Cliente reporta problemas con tiempo de respuesta",
            outcome="escalated",
            next_action="priority_support",
        ),
    ]


def get_demo_campaigns() -> list[Campaign]:
    """Retorna datos de demo para campañas de marketing."""
    return [
        Campaign(
            name="Q1 Email Campaign - Enterprise Leads",
            description="Campaña de email segmentada para leads enterprise",
            campaign_type="email",
            status="active",
            target_segment="enterprise",
            subject="Transforma tu negocio con nuestras soluciones enterprise",
            content={
                "template": "enterprise_template",
                "personalization": True,
                "tracking_enabled": True
            },
            sent_count=500,
            delivered_count=485,
            opened_count=194,
            clicked_count=58,
            converted_count=12,
            started_at=datetime.now() - timedelta(days=15),
        ),
        Campaign(
            name="Webinar Series - Cloud Solutions",
            description="Serie de webinars sobre migración a la nube",
            campaign_type="multi-channel",
            status="active",
            target_segment="prospects",
            subject="Aprende a migrar tus sistemas a la nube",
            content={
                "webinar_dates": ["2024-03-15", "2024-03-22", "2024-03-29"],
                "topics": ["Cloud Migration", "Security", "Cost Optimization"]
            },
            sent_count=300,
            delivered_count=295,
            opened_count=118,
            clicked_count=35,
            converted_count=8,
            started_at=datetime.now() - timedelta(days=7),
        ),
        Campaign(
            name="Nuevas Funcionalidades - Q2 2024",
            description="Anuncio de nuevas funcionalidades del producto",
            campaign_type="email",
            status="completed",
            target_segment="customers",
            subject="Descubre las nuevas funcionalidades que hemos lanzado",
            content={
                "features": ["AI Dashboard", "Advanced Analytics", "Mobile App"],
                "video_demo": True
            },
            sent_count=1200,
            delivered_count=1180,
            opened_count=590,
            clicked_count=177,
            converted_count=45,
            started_at=datetime.now() - timedelta(days=45),
            completed_at=datetime.now() - timedelta(days=30),
        ),
        Campaign(
            name="Reactivación de Clientes Inactivos",
            description="Campaña para reactivar clientes sin actividad reciente",
            campaign_type="email",
            status="paused",
            target_segment="inactive",
            subject="Te extrañamos. Aquí tienes un 20% de descuento",
            content={
                "discount": "20%",
                "valid_until": "2024-04-30",
                "special_offer": True
            },
            sent_count=200,
            delivered_count=195,
            opened_count=78,
            clicked_count=23,
            converted_count=5,
            started_at=datetime.now() - timedelta(days=20),
        ),
        Campaign(
            name="Referidos - Programa de Partners",
            description="Campaña para expandir programa de referidos",
            campaign_type="social",
            status="draft",
            target_segment="champions",
            subject="Conviértete en nuestro partner y gana comisiones",
            content={
                "commission_rate": "15%",
                "benefits": ["Monthly commissions", "Exclusive access", "Marketing support"],
                "signup_link": "https://partner.example.com"
            },
            scheduled_at=datetime.now() + timedelta(days=5),
        ),
    ]


def get_all_demo_data() -> tuple[list[Customer], list[Ticket], list[Interaction], list[Campaign]]:
    """Retorna todos los datos de demo."""
    return (
        get_demo_customers(),
        get_demo_tickets(),
        get_demo_interactions(),
        get_demo_campaigns()
    )
