"""Git Service - Git integration, Eraserbot, and Azure DevOps."""
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import httpx
import logging
import json
import traceback
from dotenv import load_dotenv

from .database import get_db
from .models import AzureDevOpsConnection, AzureDevOpsWorkItem
from .azure_devops import AzureDevOpsHandler

load_dotenv()

# Configure structured logging
class StructuredLogger:
    """Structured logger with JSON output for distributed tracing."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)

        # Set log level from environment variable (default: INFO)
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        self.logger.setLevel(log_level)

        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

    def log(self, level: str, message: str, correlation_id: str = None, **kwargs):
        """Log structured message with correlation ID."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "level": level.upper(),
            "message": message,
            "correlation_id": correlation_id,
            **kwargs
        }

        # Use appropriate logging method based on level
        level_upper = level.upper()
        if level_upper == "DEBUG":
            self.logger.debug(json.dumps(log_data))
        elif level_upper == "WARNING":
            self.logger.warning(json.dumps(log_data))
        elif level_upper == "ERROR":
            self.logger.error(json.dumps(log_data))
        else:  # INFO or any other level
            self.logger.info(json.dumps(log_data))

    def debug(self, message: str, correlation_id: str = None, **kwargs):
        self.log("debug", message, correlation_id, **kwargs)

    def info(self, message: str, correlation_id: str = None, **kwargs):
        self.log("info", message, correlation_id, **kwargs)

    def error(self, message: str, correlation_id: str = None, exc: Exception = None, **kwargs):
        """Log error message with optional exception and stack trace."""
        if exc is not None:
            kwargs['error_type'] = type(exc).__name__
            kwargs['error_message'] = str(exc)
            kwargs['stack_trace'] = traceback.format_exc()
        self.log("error", message, correlation_id, **kwargs)

    def warning(self, message: str, correlation_id: str = None, **kwargs):
        self.log("warning", message, correlation_id, **kwargs)

logger = StructuredLogger("git-service")

app = FastAPI(
    title="AutoGraph v3 Git Service",
    description="Git integration, Eraserbot, and Azure DevOps service",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Azure DevOps handler
azure_devops = AzureDevOpsHandler()


# Pydantic models
class AzureDevOpsConnectionCreate(BaseModel):
    """Azure DevOps connection creation request."""
    organization: str = Field(..., description="Azure DevOps organization (e.g., 'bayer')")
    project: str = Field(..., description="Project name (e.g., 'PHCom')")
    personal_access_token: str = Field(..., description="Personal Access Token for authentication")
    area_path: Optional[str] = Field(None, description="Area path filter (e.g., 'PHCom/IDP')")
    iteration_path: Optional[str] = Field(None, description="Iteration/sprint filter")
    auto_sync: bool = Field(False, description="Enable automatic synchronization")
    sync_frequency: str = Field("manual", description="Sync frequency: manual, hourly, daily")


class AzureDevOpsConnectionUpdate(BaseModel):
    """Azure DevOps connection update request."""
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    auto_sync: Optional[bool] = None
    sync_frequency: Optional[str] = None


class WorkItemQuery(BaseModel):
    """Work item query parameters."""
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    work_item_type: Optional[str] = None
    state: Optional[str] = None
    max_items: int = Field(100, ge=1, le=500)


class WorkItemUpdate(BaseModel):
    """Work item update request."""
    state: Optional[str] = None
    comment: Optional[str] = None
    fields: Optional[Dict[str, Any]] = None


class DiagramGenerationRequest(BaseModel):
    """Diagram generation from work item request."""
    work_item_id: int
    diagram_type: str = Field("flowchart", description="Type of diagram to generate")
    use_ai: bool = Field(True, description="Use AI for enhanced generation")


class CommitLinkRequest(BaseModel):
    """Link commit to work item request."""
    work_item_id: int
    commit_url: str
    comment: Optional[str] = None


# Utility functions
async def verify_token(authorization: str = Header(...)) -> str:
    """Verify JWT token and extract user ID."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    # Verify token with auth service
    try:
        # Use localhost for development, Docker hostname for production
        auth_host = os.getenv("AUTH_SERVICE_HOST", "localhost")
        auth_port = os.getenv("AUTH_SERVICE_PORT", "8085")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{auth_host}:{auth_port}/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            
            user_data = response.json()
            return user_data.get("user_id")
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Token verification failed")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "git-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# ========================================
# Azure DevOps Connection Endpoints
# ========================================

@app.post("/azure-devops/connections", status_code=201)
async def create_azure_devops_connection(
    connection: AzureDevOpsConnectionCreate,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Create a new Azure DevOps connection.
    
    Tests the connection before saving.
    """
    try:
        # Test connection first
        test_result = await azure_devops.test_connection(
            connection.organization,
            connection.project,
            connection.personal_access_token
        )
        
        if not test_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=f"Connection test failed: {test_result.get('error')}"
            )
        
        # Create connection record
        db_connection = AzureDevOpsConnection(
            user_id=user_id,
            organization=connection.organization,
            project=connection.project,
            personal_access_token=connection.personal_access_token,
            area_path=connection.area_path,
            iteration_path=connection.iteration_path,
            auto_sync=connection.auto_sync,
            sync_frequency=connection.sync_frequency,
            last_sync_status="connected"
        )
        
        db.add(db_connection)
        db.commit()
        db.refresh(db_connection)
        
        logger.info(f"Created Azure DevOps connection for user {user_id}: {connection.organization}/{connection.project}")
        
        return {
            "id": db_connection.id,
            "organization": db_connection.organization,
            "project": db_connection.project,
            "area_path": db_connection.area_path,
            "iteration_path": db_connection.iteration_path,
            "auto_sync": db_connection.auto_sync,
            "sync_frequency": db_connection.sync_frequency,
            "last_sync_status": db_connection.last_sync_status,
            "created_at": db_connection.created_at.isoformat(),
            "project_info": test_result.get("project")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create Azure DevOps connection: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/azure-devops/connections")
async def list_azure_devops_connections(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """List all Azure DevOps connections for the current user."""
    connections = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.user_id == user_id
    ).all()
    
    return {
        "connections": [
            {
                "id": conn.id,
                "organization": conn.organization,
                "project": conn.project,
                "area_path": conn.area_path,
                "iteration_path": conn.iteration_path,
                "auto_sync": conn.auto_sync,
                "sync_frequency": conn.sync_frequency,
                "last_sync_at": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
                "last_sync_status": conn.last_sync_status,
                "created_at": conn.created_at.isoformat()
            }
            for conn in connections
        ],
        "total": len(connections)
    }


@app.get("/azure-devops/connections/{connection_id}")
async def get_azure_devops_connection(
    connection_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get details of a specific Azure DevOps connection."""
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return {
        "id": connection.id,
        "organization": connection.organization,
        "project": connection.project,
        "area_path": connection.area_path,
        "iteration_path": connection.iteration_path,
        "auto_sync": connection.auto_sync,
        "sync_frequency": connection.sync_frequency,
        "last_sync_at": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
        "last_sync_status": connection.last_sync_status,
        "created_at": connection.created_at.isoformat(),
        "updated_at": connection.updated_at.isoformat()
    }


@app.put("/azure-devops/connections/{connection_id}")
async def update_azure_devops_connection(
    connection_id: str,
    update: AzureDevOpsConnectionUpdate,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update an Azure DevOps connection."""
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    if update.area_path is not None:
        connection.area_path = update.area_path
    if update.iteration_path is not None:
        connection.iteration_path = update.iteration_path
    if update.auto_sync is not None:
        connection.auto_sync = update.auto_sync
    if update.sync_frequency is not None:
        connection.sync_frequency = update.sync_frequency
    
    db.commit()
    db.refresh(connection)
    
    return {
        "id": connection.id,
        "organization": connection.organization,
        "project": connection.project,
        "area_path": connection.area_path,
        "iteration_path": connection.iteration_path,
        "auto_sync": connection.auto_sync,
        "sync_frequency": connection.sync_frequency,
        "updated_at": connection.updated_at.isoformat()
    }


@app.delete("/azure-devops/connections/{connection_id}")
async def delete_azure_devops_connection(
    connection_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete an Azure DevOps connection."""
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    db.delete(connection)
    db.commit()
    
    logger.info(f"Deleted Azure DevOps connection {connection_id} for user {user_id}")
    
    return {"message": "Connection deleted successfully"}


# ========================================
# Azure DevOps Projects Endpoints
# ========================================

@app.get("/azure-devops/connections/{connection_id}/projects")
async def get_projects(
    connection_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get list of projects from Azure DevOps organization."""
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        projects = await azure_devops.get_projects(
            connection.organization,
            connection.personal_access_token
        )
        
        return {
            "organization": connection.organization,
            "projects": projects,
            "total": len(projects)
        }
        
    except Exception as e:
        logger.error(f"Failed to get projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Azure DevOps Work Items Endpoints
# ========================================

@app.post("/azure-devops/connections/{connection_id}/work-items/sync")
async def sync_work_items(
    connection_id: str,
    query: Optional[WorkItemQuery] = None,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Sync work items from Azure DevOps to local database.
    
    Pulls work items based on connection settings and optional query filters.
    """
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        # Use query parameters or connection defaults
        area_path = (query.area_path if query else None) or connection.area_path
        iteration_path = (query.iteration_path if query else None) or connection.iteration_path
        
        # Get work items from Azure DevOps
        work_items = await azure_devops.get_work_items(
            organization=connection.organization,
            project=connection.project,
            pat=connection.personal_access_token,
            area_path=area_path,
            iteration_path=iteration_path,
            work_item_type=query.work_item_type if query else None,
            state=query.state if query else None,
            max_items=query.max_items if query else 100
        )
        
        # Update or create work item records
        synced_count = 0
        for item in work_items:
            existing = db.query(AzureDevOpsWorkItem).filter(
                AzureDevOpsWorkItem.connection_id == connection_id,
                AzureDevOpsWorkItem.work_item_id == item["id"]
            ).first()
            
            if existing:
                # Update existing
                existing.work_item_type = item["type"]
                existing.title = item["title"]
                existing.description = item.get("description", "")
                existing.acceptance_criteria = item.get("acceptance_criteria", "")
                existing.state = item["state"]
                existing.assigned_to = item.get("assigned_to")
                existing.area_path = item.get("area_path")
                existing.iteration_path = item.get("iteration_path")
                existing.last_synced_at = datetime.utcnow()
            else:
                # Create new
                new_item = AzureDevOpsWorkItem(
                    connection_id=connection_id,
                    work_item_id=item["id"],
                    work_item_type=item["type"],
                    title=item["title"],
                    description=item.get("description", ""),
                    acceptance_criteria=item.get("acceptance_criteria", ""),
                    state=item["state"],
                    assigned_to=item.get("assigned_to"),
                    area_path=item.get("area_path"),
                    iteration_path=item.get("iteration_path"),
                    last_synced_at=datetime.utcnow()
                )
                db.add(new_item)
            
            synced_count += 1
        
        # Update connection sync status
        connection.last_sync_at = datetime.utcnow()
        connection.last_sync_status = f"synced_{synced_count}_items"
        
        db.commit()
        
        logger.info(f"Synced {synced_count} work items for connection {connection_id}")
        
        return {
            "synced": synced_count,
            "connection_id": connection_id,
            "last_sync_at": connection.last_sync_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to sync work items: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/azure-devops/connections/{connection_id}/work-items")
async def get_work_items(
    connection_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all synced work items for a connection."""
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    work_items = db.query(AzureDevOpsWorkItem).filter(
        AzureDevOpsWorkItem.connection_id == connection_id
    ).order_by(AzureDevOpsWorkItem.last_synced_at.desc()).all()
    
    return {
        "work_items": [
            {
                "id": item.id,
                "work_item_id": item.work_item_id,
                "type": item.work_item_type,
                "title": item.title,
                "description": item.description,
                "acceptance_criteria": item.acceptance_criteria,
                "state": item.state,
                "assigned_to": item.assigned_to,
                "area_path": item.area_path,
                "iteration_path": item.iteration_path,
                "diagram_id": item.diagram_id,
                "last_synced_at": item.last_synced_at.isoformat() if item.last_synced_at else None
            }
            for item in work_items
        ],
        "total": len(work_items)
    }


@app.get("/azure-devops/connections/{connection_id}/work-items/{work_item_id}")
async def get_work_item(
    connection_id: str,
    work_item_id: int,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get a specific work item from Azure DevOps (live)."""
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        work_item = await azure_devops.get_work_item(
            organization=connection.organization,
            project=connection.project,
            work_item_id=work_item_id,
            pat=connection.personal_access_token
        )
        
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        return work_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get work item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/azure-devops/connections/{connection_id}/work-items/{work_item_id}")
async def update_work_item(
    connection_id: str,
    work_item_id: int,
    update: WorkItemUpdate,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Update a work item in Azure DevOps.
    
    Can update state, add comments, or modify other fields.
    """
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        # Build fields to update
        fields_to_update = {}
        if update.state:
            fields_to_update["System.State"] = update.state
        if update.fields:
            fields_to_update.update(update.fields)
        
        # Update work item if there are fields to update
        if fields_to_update:
            result = await azure_devops.update_work_item(
                organization=connection.organization,
                project=connection.project,
                work_item_id=work_item_id,
                pat=connection.personal_access_token,
                fields=fields_to_update
            )
        else:
            result = {}
        
        # Add comment if provided
        if update.comment:
            await azure_devops.add_work_item_comment(
                organization=connection.organization,
                project=connection.project,
                work_item_id=work_item_id,
                pat=connection.personal_access_token,
                comment=update.comment
            )
        
        logger.info(f"Updated work item {work_item_id} in connection {connection_id}")
        
        return {
            "success": True,
            "work_item_id": work_item_id,
            "updated_fields": list(fields_to_update.keys()),
            "comment_added": bool(update.comment)
        }
        
    except Exception as e:
        logger.error(f"Failed to update work item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Azure DevOps Diagram Generation
# ========================================

@app.post("/azure-devops/connections/{connection_id}/work-items/{work_item_id}/generate-diagram")
async def generate_diagram_from_work_item(
    connection_id: str,
    work_item_id: int,
    request: DiagramGenerationRequest,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Generate a diagram from work item acceptance criteria using AI.
    
    Creates a new diagram file and links it to the work item.
    """
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        # Get work item details
        work_item = await azure_devops.get_work_item(
            organization=connection.organization,
            project=connection.project,
            work_item_id=work_item_id,
            pat=connection.personal_access_token
        )
        
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        # Prepare prompt for AI service
        acceptance_criteria = work_item.get("acceptance_criteria", "")
        description = work_item.get("description", "")
        title = work_item.get("title", "")
        
        if not acceptance_criteria and not description:
            raise HTTPException(
                status_code=400,
                detail="Work item has no acceptance criteria or description to generate from"
            )
        
        prompt = f"Work Item: {title}\n\n"
        if description:
            prompt += f"Description:\n{description}\n\n"
        if acceptance_criteria:
            prompt += f"Acceptance Criteria:\n{acceptance_criteria}\n\n"
        prompt += f"Generate a {request.diagram_type} diagram that visualizes the requirements and flow."
        
        # Call AI service to generate diagram
        ai_host = os.getenv("AI_SERVICE_HOST", "localhost")
        ai_port = os.getenv("AI_SERVICE_PORT", "8084")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"http://{ai_host}:{ai_port}/generate",
                json={
                    "prompt": prompt,
                    "diagram_type": request.diagram_type,
                    "user_id": user_id
                },
                headers={"Authorization": f"Bearer (internal)"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"AI service error: {response.text}"
                )
            
            diagram_data = response.json()
        
        # Create diagram file via diagram service
        diagram_host = os.getenv("DIAGRAM_SERVICE_HOST", "localhost")
        diagram_port = os.getenv("DIAGRAM_SERVICE_PORT", "8082")
        
        async with httpx.AsyncClient() as client:
            file_response = await client.post(
                f"http://{diagram_host}:{diagram_port}/files",
                json={
                    "title": f"{title} - Generated Diagram",
                    "type": "canvas",
                    "canvas_data": diagram_data.get("canvas_data", {}),
                    "note_content": f"Auto-generated from Azure DevOps Work Item #{work_item_id}\n\n{description}"
                },
                headers={"Authorization": f"Bearer (internal)"}
            )
            
            if file_response.status_code != 201:
                raise HTTPException(
                    status_code=file_response.status_code,
                    detail="Failed to create diagram file"
                )
            
            file_data = file_response.json()
            diagram_id = file_data.get("id")
        
        # Link diagram to work item in database
        db_work_item = db.query(AzureDevOpsWorkItem).filter(
            AzureDevOpsWorkItem.connection_id == connection_id,
            AzureDevOpsWorkItem.work_item_id == work_item_id
        ).first()
        
        if db_work_item:
            db_work_item.diagram_id = diagram_id
            db.commit()
        
        # Add comment to work item with diagram link
        diagram_url = f"https://autograph.app/diagrams/{diagram_id}"
        comment = f"Diagram generated automatically from acceptance criteria: {diagram_url}"
        
        await azure_devops.add_work_item_comment(
            organization=connection.organization,
            project=connection.project,
            work_item_id=work_item_id,
            pat=connection.personal_access_token,
            comment=comment
        )
        
        logger.info(f"Generated diagram {diagram_id} from work item {work_item_id}")
        
        return {
            "success": True,
            "diagram_id": diagram_id,
            "work_item_id": work_item_id,
            "diagram_url": diagram_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate diagram: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Azure DevOps Commit Linking
# ========================================

@app.post("/azure-devops/connections/{connection_id}/link-commit")
async def link_commit(
    connection_id: str,
    request: CommitLinkRequest,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Link a Git commit to an Azure DevOps work item."""
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        result = await azure_devops.link_commit_to_work_item(
            organization=connection.organization,
            project=connection.project,
            work_item_id=request.work_item_id,
            pat=connection.personal_access_token,
            commit_url=request.commit_url,
            comment=request.comment
        )
        
        logger.info(f"Linked commit to work item {request.work_item_id}")
        
        return {
            "success": True,
            "work_item_id": request.work_item_id,
            "commit_url": request.commit_url
        }
        
    except Exception as e:
        logger.error(f"Failed to link commit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Azure DevOps Area Paths and Iterations
# ========================================

@app.get("/azure-devops/connections/{connection_id}/area-paths")
async def get_area_paths(
    connection_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all area paths for the connected project."""
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        area_paths = await azure_devops.get_area_paths(
            organization=connection.organization,
            project=connection.project,
            pat=connection.personal_access_token
        )
        
        return {
            "organization": connection.organization,
            "project": connection.project,
            "area_paths": area_paths,
            "total": len(area_paths)
        }
        
    except Exception as e:
        logger.error(f"Failed to get area paths: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/azure-devops/connections/{connection_id}/iterations")
async def get_iterations(
    connection_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all iterations (sprints) for the connected project."""
    connection = db.query(AzureDevOpsConnection).filter(
        AzureDevOpsConnection.id == connection_id,
        AzureDevOpsConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        iterations = await azure_devops.get_iterations(
            organization=connection.organization,
            project=connection.project,
            pat=connection.personal_access_token
        )
        
        return {
            "organization": connection.organization,
            "project": connection.project,
            "iterations": iterations,
            "total": len(iterations)
        }
        
    except Exception as e:
        logger.error(f"Failed to get iterations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("GIT_SERVICE_PORT", "8087")))
