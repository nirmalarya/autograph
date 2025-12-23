"""
Template-based and domain-specific diagram generation.

Features:
- #336: Template-based generation: use reference library
- #337: Domain-specific: fintech architecture patterns
- #338: Domain-specific: healthcare architecture
- #339: Domain-specific: e-commerce architecture
- #340: Domain-specific: DevOps pipeline
"""

from typing import Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DiagramDomain(str, Enum):
    """Supported domain-specific patterns."""
    FINTECH = "fintech"
    HEALTHCARE = "healthcare"
    ECOMMERCE = "e-commerce"
    DEVOPS = "devops"
    GENERAL = "general"


class DiagramTemplateLibrary:
    """
    Library of diagram templates for common patterns.
    
    Feature #336: Template-based generation
    """
    
    # Reference templates for common patterns
    TEMPLATES = {
        # General templates
        "three_tier_architecture": {
            "domain": DiagramDomain.GENERAL,
            "description": "Classic 3-tier architecture",
            "template": """graph TB
    Frontend[Frontend Layer<br/>Web/Mobile]
    Backend[Backend Layer<br/>Business Logic]
    Database[(Database Layer<br/>Data Storage)]
    
    Frontend -->|API Calls| Backend
    Backend -->|Queries| Database""",
            "components": ["Frontend", "Backend", "Database"],
            "keywords": ["3-tier", "three tier", "layered"]
        },
        
        "microservices": {
            "domain": DiagramDomain.GENERAL,
            "description": "Microservices architecture",
            "template": """graph TB
    Gateway[API Gateway]
    Service1[User Service]
    Service2[Product Service]
    Service3[Order Service]
    DB1[(User DB)]
    DB2[(Product DB)]
    DB3[(Order DB)]
    
    Gateway --> Service1
    Gateway --> Service2
    Gateway --> Service3
    Service1 --> DB1
    Service2 --> DB2
    Service3 --> DB3""",
            "components": ["Gateway", "Services", "Databases"],
            "keywords": ["microservice", "micro service", "distributed"]
        },
        
        # Feature #337: Fintech patterns
        "fintech_payment": {
            "domain": DiagramDomain.FINTECH,
            "description": "Fintech payment processing",
            "template": """graph TB
    Customer[Customer]
    Frontend[Payment Frontend]
    Gateway[Payment Gateway]
    Processor[Payment Processor]
    Bank[Bank API]
    Fraud[Fraud Detection]
    DB[(Transaction DB)]
    
    Customer -->|Initiate Payment| Frontend
    Frontend -->|Submit| Gateway
    Gateway -->|Validate| Fraud
    Gateway -->|Process| Processor
    Processor -->|Authorize| Bank
    Processor -->|Record| DB
    Bank -->|Response| Processor
    Processor -->|Confirm| Frontend""",
            "components": ["Payment Gateway", "Fraud Detection", "Bank Integration"],
            "keywords": ["payment", "transaction", "fintech", "banking"]
        },
        
        "fintech_trading": {
            "domain": DiagramDomain.FINTECH,
            "description": "Trading platform architecture",
            "template": """graph TB
    Trader[Trader]
    Platform[Trading Platform]
    OrderEngine[Order Engine]
    MarketData[Market Data Feed]
    RiskEngine[Risk Engine]
    Settlement[Settlement System]
    Database[(Trade DB)]
    
    Trader -->|Place Order| Platform
    Platform -->|Submit| OrderEngine
    MarketData -->|Real-time Prices| Platform
    OrderEngine -->|Check Risk| RiskEngine
    OrderEngine -->|Execute| Settlement
    Settlement -->|Record| Database""",
            "components": ["Order Engine", "Risk Engine", "Market Data"],
            "keywords": ["trading", "stock", "market", "fintech"]
        },
        
        # Feature #338: Healthcare patterns
        "healthcare_ehr": {
            "domain": DiagramDomain.HEALTHCARE,
            "description": "Electronic Health Records system",
            "template": """graph TB
    Patient[Patient Portal]
    Doctor[Doctor Dashboard]
    EHR[EHR System]
    FHIR[FHIR API]
    Records[(Medical Records)]
    Lab[Lab Integration]
    Pharmacy[Pharmacy System]
    
    Patient -->|Access Records| EHR
    Doctor -->|Update Records| EHR
    EHR -->|Store| Records
    EHR -->|FHIR Standard| FHIR
    FHIR -->|Results| Lab
    FHIR -->|Prescriptions| Pharmacy""",
            "components": ["EHR", "FHIR API", "Patient Portal"],
            "keywords": ["ehr", "health record", "medical", "healthcare", "fhir"]
        },
        
        "healthcare_telemedicine": {
            "domain": DiagramDomain.HEALTHCARE,
            "description": "Telemedicine platform",
            "template": """graph TB
    Patient[Patient App]
    Doctor[Doctor App]
    Video[Video Service]
    Scheduler[Appointment Scheduler]
    Records[Medical Records]
    Billing[Billing System]
    Pharmacy[E-Prescription]
    
    Patient -->|Book Appointment| Scheduler
    Doctor -->|View Schedule| Scheduler
    Patient -->|Video Call| Video
    Doctor -->|Video Call| Video
    Doctor -->|Access| Records
    Doctor -->|Prescribe| Pharmacy
    Scheduler -->|Generate Invoice| Billing""",
            "components": ["Video Service", "Scheduler", "E-Prescription"],
            "keywords": ["telemedicine", "telehealth", "remote", "healthcare"]
        },
        
        # Feature #339: E-commerce patterns
        "ecommerce_basic": {
            "domain": DiagramDomain.ECOMMERCE,
            "description": "Basic e-commerce platform",
            "template": """graph TB
    User[Customer]
    Frontend[Storefront]
    Products[Product Catalog]
    Cart[Shopping Cart]
    Checkout[Checkout Service]
    Payment[Payment Gateway]
    Orders[Order Management]
    Inventory[Inventory System]
    Database[(Database)]
    
    User -->|Browse| Frontend
    Frontend -->|Display| Products
    User -->|Add Items| Cart
    Cart -->|Proceed| Checkout
    Checkout -->|Process| Payment
    Checkout -->|Create| Orders
    Orders -->|Update| Inventory
    Products --> Database
    Orders --> Database""",
            "components": ["Product Catalog", "Cart", "Payment", "Inventory"],
            "keywords": ["ecommerce", "e-commerce", "shopping", "retail", "store"]
        },
        
        "ecommerce_advanced": {
            "domain": DiagramDomain.ECOMMERCE,
            "description": "Advanced e-commerce with recommendations",
            "template": """graph TB
    Customer[Customer]
    Web[Web Frontend]
    Mobile[Mobile App]
    Gateway[API Gateway]
    Products[Product Service]
    Recommendations[Recommendation Engine]
    Cart[Cart Service]
    Orders[Order Service]
    Payment[Payment Service]
    Search[Search Engine]
    Cache[Redis Cache]
    DB[(Database)]
    
    Customer -->|Browse| Web
    Customer -->|Browse| Mobile
    Web --> Gateway
    Mobile --> Gateway
    Gateway --> Products
    Gateway --> Recommendations
    Gateway --> Cart
    Gateway --> Orders
    Orders --> Payment
    Products --> Search
    Products --> Cache
    Products --> DB""",
            "components": ["Recommendation Engine", "Search", "Multiple Services"],
            "keywords": ["ecommerce", "recommendations", "search", "advanced"]
        },
        
        # Feature #340: DevOps patterns
        "devops_cicd": {
            "domain": DiagramDomain.DEVOPS,
            "description": "CI/CD pipeline",
            "template": """graph LR
    Code[Source Code]
    Git[Git Repository]
    CI[CI Server]
    Build[Build]
    Test[Test]
    Security[Security Scan]
    Registry[Container Registry]
    CD[CD Server]
    Staging[Staging Environment]
    Production[Production Environment]
    
    Code -->|Push| Git
    Git -->|Trigger| CI
    CI -->|Compile| Build
    Build -->|Run| Test
    Test -->|Scan| Security
    Security -->|Push| Registry
    Registry -->|Deploy| CD
    CD -->|Release| Staging
    Staging -->|Promote| Production""",
            "components": ["CI/CD", "Testing", "Security Scan", "Deployment"],
            "keywords": ["cicd", "ci/cd", "pipeline", "devops", "deployment"]
        },
        
        "devops_monitoring": {
            "domain": DiagramDomain.DEVOPS,
            "description": "Monitoring and observability",
            "template": """graph TB
    Services[Microservices]
    Metrics[Metrics Collection]
    Logs[Log Aggregation]
    Traces[Distributed Tracing]
    Prometheus[Prometheus]
    Grafana[Grafana Dashboards]
    ELK[ELK Stack]
    Alerting[Alert Manager]
    PagerDuty[PagerDuty]
    
    Services -->|Metrics| Metrics
    Services -->|Logs| Logs
    Services -->|Traces| Traces
    Metrics --> Prometheus
    Prometheus --> Grafana
    Logs --> ELK
    Prometheus -->|Alerts| Alerting
    Alerting -->|Notify| PagerDuty""",
            "components": ["Prometheus", "Grafana", "ELK", "Tracing"],
            "keywords": ["monitoring", "observability", "metrics", "devops"]
        },
        
        "devops_infrastructure": {
            "domain": DiagramDomain.DEVOPS,
            "description": "Infrastructure as Code",
            "template": """graph TB
    Code[IaC Code]
    Git[Git Repository]
    Terraform[Terraform]
    Cloud[Cloud Provider]
    K8s[Kubernetes Cluster]
    Helm[Helm Charts]
    Apps[Applications]
    Monitoring[Monitoring Stack]
    
    Code -->|Push| Git
    Git -->|Plan/Apply| Terraform
    Terraform -->|Provision| Cloud
    Cloud -->|Create| K8s
    Helm -->|Deploy| K8s
    K8s -->|Run| Apps
    K8s -->|Metrics| Monitoring""",
            "components": ["Terraform", "Kubernetes", "Helm", "IaC"],
            "keywords": ["infrastructure", "iac", "terraform", "kubernetes", "devops"]
        }
    }
    
    @staticmethod
    def detect_domain(prompt: str) -> DiagramDomain:
        """
        Detect domain from prompt.
        
        Features #337-340: Domain detection
        """
        prompt_lower = prompt.lower()
        
        # Fintech keywords (#337)
        if any(word in prompt_lower for word in [
            "payment", "transaction", "banking", "fintech", "trading", 
            "stock", "crypto", "wallet", "ledger"
        ]):
            return DiagramDomain.FINTECH
        
        # Healthcare keywords (#338)
        if any(word in prompt_lower for word in [
            "health", "medical", "patient", "doctor", "hospital", "ehr", 
            "fhir", "telemedicine", "telehealth", "clinic"
        ]):
            return DiagramDomain.HEALTHCARE
        
        # E-commerce keywords (#339)
        if any(word in prompt_lower for word in [
            "ecommerce", "e-commerce", "shopping", "cart", "store", 
            "retail", "product", "checkout", "inventory"
        ]):
            return DiagramDomain.ECOMMERCE
        
        # DevOps keywords (#340)
        if any(word in prompt_lower for word in [
            "devops", "cicd", "ci/cd", "pipeline", "deploy", "kubernetes", 
            "docker", "terraform", "monitoring", "observability"
        ]):
            return DiagramDomain.DEVOPS
        
        return DiagramDomain.GENERAL
    
    @staticmethod
    def find_matching_template(prompt: str) -> Optional[Dict]:
        """
        Find best matching template for prompt.
        
        Feature #336: Template matching
        """
        prompt_lower = prompt.lower()
        
        # Try exact keyword match first
        for template_id, template in DiagramTemplateLibrary.TEMPLATES.items():
            keywords = template.get("keywords", [])
            if any(keyword in prompt_lower for keyword in keywords):
                logger.info(f"Found matching template: {template_id}")
                return {
                    "id": template_id,
                    **template
                }
        
        # Try domain match
        domain = DiagramTemplateLibrary.detect_domain(prompt)
        if domain != DiagramDomain.GENERAL:
            for template_id, template in DiagramTemplateLibrary.TEMPLATES.items():
                if template.get("domain") == domain:
                    logger.info(
                        f"Found domain template: {template_id} for {domain}"
                    )
                    return {
                        "id": template_id,
                        **template
                    }
        
        return None
    
    @staticmethod
    def enhance_prompt_with_template(prompt: str, template: Dict) -> str:
        """
        Enhance prompt with template reference.
        
        Feature #336: Template-based generation
        """
        enhanced = f"""Create a diagram based on this request: {prompt}

Use this template as a starting point:

{template['template']}

Key components from template:
{', '.join(template['components'])}

Adapt the template to match the specific requirements in the request.
Maintain the overall structure but customize:
- Component names to match the domain
- Add or remove components as needed
- Adjust connections for the specific use case
- Keep the same diagram style and format"""
        
        return enhanced
    
    @staticmethod
    def get_domain_specific_guidance(domain: DiagramDomain) -> str:
        """
        Get domain-specific generation guidance.
        
        Features #337-340: Domain-specific patterns
        """
        guidance = {
            DiagramDomain.FINTECH: """
Fintech-specific considerations:
- Include fraud detection and security layers
- Show payment gateway integration
- Include compliance/audit trails
- Handle transaction rollback flows
- Show real-time data processing
- Include risk management components""",
            
            DiagramDomain.HEALTHCARE: """
Healthcare-specific considerations:
- Follow HIPAA compliance (secure data handling)
- Use FHIR standards where applicable
- Include patient privacy protections
- Show secure communication channels
- Include audit logging for medical records
- Handle emergency access scenarios""",
            
            DiagramDomain.ECOMMERCE: """
E-commerce-specific considerations:
- Include product catalog and search
- Show cart and checkout flow
- Include payment processing
- Show inventory management
- Include recommendation engine
- Handle high traffic scenarios""",
            
            DiagramDomain.DEVOPS: """
DevOps-specific considerations:
- Show CI/CD pipeline stages
- Include testing and quality gates
- Show monitoring and alerting
- Include infrastructure as code
- Show deployment strategies
- Include rollback capabilities"""
        }
        
        return guidance.get(domain, "")
    
    @staticmethod
    def list_templates_by_domain(domain: Optional[DiagramDomain] = None) -> List[Dict]:
        """List all templates, optionally filtered by domain."""
        templates = []
        
        for template_id, template in DiagramTemplateLibrary.TEMPLATES.items():
            if domain is None or template.get("domain") == domain:
                templates.append({
                    "id": template_id,
                    "description": template["description"],
                    "domain": template["domain"],
                    "components": template["components"]
                })
        
        return templates
