"""Icon intelligence for AI diagram generation."""
import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IconCategory(str, Enum):
    """Icon categories."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DATABASE = "database"
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    TOOL = "tool"
    GENERAL = "general"


class IconIntelligence:
    """
    Icon intelligence system that maps service names to appropriate icons.
    
    Features:
    - #324: 'EC2' → aws-ec2 icon
    - #325: 'Postgres' → postgresql icon  
    - #326: Context-aware selection
    """
    
    # Icon mapping database
    ICON_MAP = {
        # AWS Services (#324)
        "ec2": ("aws-ec2", IconCategory.AWS),
        "s3": ("aws-s3", IconCategory.AWS),
        "lambda": ("aws-lambda", IconCategory.AWS),
        "rds": ("aws-rds", IconCategory.AWS),
        "dynamodb": ("aws-dynamodb", IconCategory.AWS),
        "sqs": ("aws-sqs", IconCategory.AWS),
        "sns": ("aws-sns", IconCategory.AWS),
        "cloudfront": ("aws-cloudfront", IconCategory.AWS),
        "route53": ("aws-route53", IconCategory.AWS),
        "elb": ("aws-elb", IconCategory.AWS),
        "alb": ("aws-alb", IconCategory.AWS),
        "ecs": ("aws-ecs", IconCategory.AWS),
        "eks": ("aws-eks", IconCategory.AWS),
        "api gateway": ("aws-api-gateway", IconCategory.AWS),
        "cognito": ("aws-cognito", IconCategory.AWS),
        "cloudwatch": ("aws-cloudwatch", IconCategory.AWS),
        "vpc": ("aws-vpc", IconCategory.AWS),
        "iam": ("aws-iam", IconCategory.AWS),
        "cloudformation": ("aws-cloudformation", IconCategory.AWS),
        "kinesis": ("aws-kinesis", IconCategory.AWS),
        "redshift": ("aws-redshift", IconCategory.AWS),
        "elasticache": ("aws-elasticache", IconCategory.AWS),
        "aurora": ("aws-aurora", IconCategory.AWS),
        
        # Azure Services
        "virtual machine": ("azure-vm", IconCategory.AZURE),
        "app service": ("azure-app-service", IconCategory.AZURE),
        "functions": ("azure-functions", IconCategory.AZURE),
        "storage": ("azure-storage", IconCategory.AZURE),
        "cosmos db": ("azure-cosmos", IconCategory.AZURE),
        "sql database": ("azure-sql", IconCategory.AZURE),
        "service bus": ("azure-service-bus", IconCategory.AZURE),
        "event hub": ("azure-event-hub", IconCategory.AZURE),
        "key vault": ("azure-key-vault", IconCategory.AZURE),
        "active directory": ("azure-ad", IconCategory.AZURE),
        "kubernetes": ("azure-kubernetes", IconCategory.AZURE),
        "devops": ("azure-devops", IconCategory.AZURE),
        "container instances": ("azure-container", IconCategory.AZURE),
        "api management": ("azure-api", IconCategory.AZURE),
        
        # GCP Services
        "compute engine": ("gcp-compute", IconCategory.GCP),
        "app engine": ("gcp-app-engine", IconCategory.GCP),
        "cloud functions": ("gcp-functions", IconCategory.GCP),
        "cloud storage": ("gcp-storage", IconCategory.GCP),
        "bigquery": ("gcp-bigquery", IconCategory.GCP),
        "cloud sql": ("gcp-sql", IconCategory.GCP),
        "pub/sub": ("gcp-pubsub", IconCategory.GCP),
        "cloud run": ("gcp-run", IconCategory.GCP),
        "gke": ("gcp-kubernetes", IconCategory.GCP),
        "firestore": ("gcp-firestore", IconCategory.GCP),
        "cloud cdn": ("gcp-cdn", IconCategory.GCP),
        "load balancer": ("gcp-lb", IconCategory.GCP),
        
        # Databases (#325)
        "postgresql": ("postgresql", IconCategory.DATABASE),
        "postgres": ("postgresql", IconCategory.DATABASE),
        "mysql": ("mysql", IconCategory.DATABASE),
        "mongodb": ("mongodb", IconCategory.DATABASE),
        "redis": ("redis", IconCategory.DATABASE),
        "cassandra": ("cassandra", IconCategory.DATABASE),
        "elasticsearch": ("elasticsearch", IconCategory.DATABASE),
        "mariadb": ("mariadb", IconCategory.DATABASE),
        "oracle": ("oracle", IconCategory.DATABASE),
        "sql server": ("mssql", IconCategory.DATABASE),
        "sqlite": ("sqlite", IconCategory.DATABASE),
        "couchdb": ("couchdb", IconCategory.DATABASE),
        "influxdb": ("influxdb", IconCategory.DATABASE),
        "neo4j": ("neo4j", IconCategory.DATABASE),
        
        # Languages
        "python": ("python", IconCategory.LANGUAGE),
        "javascript": ("javascript", IconCategory.LANGUAGE),
        "typescript": ("typescript", IconCategory.LANGUAGE),
        "java": ("java", IconCategory.LANGUAGE),
        "go": ("go", IconCategory.LANGUAGE),
        "rust": ("rust", IconCategory.LANGUAGE),
        "c++": ("cpp", IconCategory.LANGUAGE),
        "c#": ("csharp", IconCategory.LANGUAGE),
        "ruby": ("ruby", IconCategory.LANGUAGE),
        "php": ("php", IconCategory.LANGUAGE),
        "swift": ("swift", IconCategory.LANGUAGE),
        "kotlin": ("kotlin", IconCategory.LANGUAGE),
        
        # Frameworks
        "react": ("react", IconCategory.FRAMEWORK),
        "vue": ("vue", IconCategory.FRAMEWORK),
        "angular": ("angular", IconCategory.FRAMEWORK),
        "django": ("django", IconCategory.FRAMEWORK),
        "flask": ("flask", IconCategory.FRAMEWORK),
        "spring": ("spring", IconCategory.FRAMEWORK),
        "express": ("express", IconCategory.FRAMEWORK),
        "fastapi": ("fastapi", IconCategory.FRAMEWORK),
        "nest": ("nestjs", IconCategory.FRAMEWORK),
        "next": ("nextjs", IconCategory.FRAMEWORK),
        "laravel": ("laravel", IconCategory.FRAMEWORK),
        "rails": ("rails", IconCategory.FRAMEWORK),
        
        # Tools
        "docker": ("docker", IconCategory.TOOL),
        "kubernetes": ("kubernetes", IconCategory.TOOL),
        "jenkins": ("jenkins", IconCategory.TOOL),
        "github": ("github", IconCategory.TOOL),
        "gitlab": ("gitlab", IconCategory.TOOL),
        "terraform": ("terraform", IconCategory.TOOL),
        "ansible": ("ansible", IconCategory.TOOL),
        "nginx": ("nginx", IconCategory.TOOL),
        "apache": ("apache", IconCategory.TOOL),
        "prometheus": ("prometheus", IconCategory.TOOL),
        "grafana": ("grafana", IconCategory.TOOL),
        "kafka": ("kafka", IconCategory.TOOL),
        "rabbitmq": ("rabbitmq", IconCategory.TOOL),
        
        # General
        "api": ("api", IconCategory.GENERAL),
        "web": ("web", IconCategory.GENERAL),
        "mobile": ("mobile", IconCategory.GENERAL),
        "user": ("user", IconCategory.GENERAL),
        "server": ("server", IconCategory.GENERAL),
        "client": ("client", IconCategory.GENERAL),
        "frontend": ("frontend", IconCategory.GENERAL),
        "backend": ("backend", IconCategory.GENERAL),
        "cache": ("cache", IconCategory.GENERAL),
        "queue": ("queue", IconCategory.GENERAL),
        "load balancer": ("load-balancer", IconCategory.GENERAL),
    }
    
    # Context keywords for better matching
    CONTEXT_KEYWORDS = {
        "aws": IconCategory.AWS,
        "amazon": IconCategory.AWS,
        "azure": IconCategory.AZURE,
        "microsoft": IconCategory.AZURE,
        "gcp": IconCategory.GCP,
        "google cloud": IconCategory.GCP,
        "database": IconCategory.DATABASE,
        "db": IconCategory.DATABASE,
        "storage": IconCategory.DATABASE,
    }
    
    @staticmethod
    def map_service_to_icon(service_name: str, context: str = "") -> Optional[str]:
        """
        Map a service name to an icon.
        
        Args:
            service_name: Name of the service (e.g., "EC2", "Postgres")
            context: Additional context for better matching
        
        Returns:
            Icon identifier or None
        
        Examples:
            - 'EC2' → 'aws-ec2'
            - 'Postgres' → 'postgresql'
            - 'Lambda function' → 'aws-lambda'
        """
        # Normalize input
        service_lower = service_name.lower().strip()
        context_lower = context.lower()
        
        # Direct match
        if service_lower in IconIntelligence.ICON_MAP:
            icon, category = IconIntelligence.ICON_MAP[service_lower]
            logger.debug(f"Direct match: {service_name} → {icon}")
            return icon
        
        # Partial match
        for key, (icon, category) in IconIntelligence.ICON_MAP.items():
            if key in service_lower or service_lower in key:
                # Check context if available
                if context_lower:
                    context_category = IconIntelligence._detect_context_category(context_lower)
                    if context_category and context_category != category:
                        continue
                
                logger.debug(f"Partial match: {service_name} → {icon}")
                return icon
        
        # Fuzzy match with context
        if context_lower:
            category = IconIntelligence._detect_context_category(context_lower)
            if category:
                # Find icons in this category
                for key, (icon, cat) in IconIntelligence.ICON_MAP.items():
                    if cat == category and (key in service_lower or service_lower in key):
                        logger.debug(f"Context match: {service_name} → {icon} (category: {category})")
                        return icon
        
        logger.debug(f"No icon match for: {service_name}")
        return None
    
    @staticmethod
    def _detect_context_category(context: str) -> Optional[IconCategory]:
        """Detect category from context keywords."""
        for keyword, category in IconIntelligence.CONTEXT_KEYWORDS.items():
            if keyword in context:
                return category
        return None
    
    @staticmethod
    def enhance_mermaid_with_icons(mermaid_code: str, context: str = "") -> str:
        """
        Enhance Mermaid diagram with appropriate icons.
        
        Analyzes node labels and adds icon references where appropriate.
        
        Feature #326: Context-aware icon selection
        """
        lines = mermaid_code.split('\n')
        enhanced_lines = []
        
        for line in lines:
            # Look for node definitions: NodeId[Label] or NodeId(Label)
            match = re.search(r'(\w+)\[([^\]]+)\]', line)
            if match:
                node_id = match.group(1)
                label = match.group(2)
                
                # Try to find icon for this label
                icon = IconIntelligence.map_service_to_icon(label, context)
                
                if icon:
                    # Add icon to label (fa: prefix for Font Awesome style)
                    enhanced_label = f"fa:{icon} {label}"
                    enhanced_line = line.replace(f"[{label}]", f"[{enhanced_label}]")
                    enhanced_lines.append(enhanced_line)
                    logger.info(f"Enhanced node: {label} → {icon}")
                else:
                    enhanced_lines.append(line)
            else:
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    @staticmethod
    def suggest_icons(prompt: str) -> List[Tuple[str, str]]:
        """
        Suggest icons based on prompt content.
        
        Returns list of (service_name, icon) tuples.
        """
        suggestions = []
        prompt_lower = prompt.lower()
        
        # Find all matching services in prompt
        for service, (icon, category) in IconIntelligence.ICON_MAP.items():
            if service in prompt_lower:
                suggestions.append((service, icon))
        
        return suggestions
    
    @staticmethod
    def get_icon_by_category(category: IconCategory) -> List[str]:
        """Get all icons in a specific category."""
        return [
            icon for icon, cat in IconIntelligence.ICON_MAP.values()
            if cat == category
        ]
    
    @staticmethod
    def validate_icon_usage(mermaid_code: str) -> Dict[str, any]:
        """
        Validate icon usage in Mermaid diagram.
        
        Returns metrics about icon coverage and appropriateness.
        """
        lines = mermaid_code.split('\n')
        
        total_nodes = 0
        nodes_with_icons = 0
        icon_suggestions = []
        
        for line in lines:
            match = re.search(r'(\w+)\[([^\]]+)\]', line)
            if match:
                total_nodes += 1
                label = match.group(2)
                
                # Check if already has icon
                if "fa:" in label or "icon:" in label:
                    nodes_with_icons += 1
                else:
                    # Suggest icon
                    icon = IconIntelligence.map_service_to_icon(label)
                    if icon:
                        icon_suggestions.append({
                            "label": label,
                            "suggested_icon": icon
                        })
        
        coverage = (nodes_with_icons / total_nodes * 100) if total_nodes > 0 else 0
        
        return {
            "total_nodes": total_nodes,
            "nodes_with_icons": nodes_with_icons,
            "coverage_percent": coverage,
            "suggestions": icon_suggestions
        }
