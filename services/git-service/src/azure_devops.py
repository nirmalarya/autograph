"""Azure DevOps integration handler."""
import httpx
import base64
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AzureDevOpsHandler:
    """Handler for Azure DevOps API operations."""
    
    def __init__(self):
        self.base_url = "https://dev.azure.com"
        self.api_version = "7.0"
    
    def _get_auth_header(self, pat: str) -> Dict[str, str]:
        """Create authentication header from Personal Access Token."""
        # Azure DevOps uses basic auth with PAT as username and empty password
        credentials = base64.b64encode(f":{pat}".encode()).decode()
        return {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }
    
    async def test_connection(self, organization: str, project: str, pat: str) -> Dict[str, Any]:
        """Test Azure DevOps connection with PAT."""
        try:
            headers = self._get_auth_header(pat)
            url = f"{self.base_url}/{organization}/_apis/projects/{project}?api-version={self.api_version}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "project": {
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "description": data.get("description", ""),
                            "url": data.get("url")
                        }
                    }
                elif response.status_code == 401:
                    return {"success": False, "error": "Invalid Personal Access Token"}
                elif response.status_code == 404:
                    return {"success": False, "error": "Project not found"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                    
        except httpx.TimeoutException:
            return {"success": False, "error": "Connection timeout"}
        except Exception as e:
            logger.error(f"Azure DevOps connection test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_projects(self, organization: str, pat: str) -> List[Dict[str, Any]]:
        """Get list of projects in organization."""
        try:
            headers = self._get_auth_header(pat)
            url = f"{self.base_url}/{organization}/_apis/projects?api-version={self.api_version}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                projects = []
                
                for project in data.get("value", []):
                    projects.append({
                        "id": project.get("id"),
                        "name": project.get("name"),
                        "description": project.get("description", ""),
                        "url": project.get("url"),
                        "state": project.get("state"),
                        "lastUpdateTime": project.get("lastUpdateTime")
                    })
                
                return projects
                
        except Exception as e:
            logger.error(f"Failed to get Azure DevOps projects: {str(e)}")
            raise
    
    async def get_work_item(self, organization: str, project: str, work_item_id: int, pat: str) -> Optional[Dict[str, Any]]:
        """Get a single work item by ID."""
        try:
            headers = self._get_auth_header(pat)
            # Get work item with all fields
            url = f"{self.base_url}/{organization}/{project}/_apis/wit/workitems/{work_item_id}?$expand=all&api-version={self.api_version}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 404:
                    return None
                    
                response.raise_for_status()
                data = response.json()
                
                fields = data.get("fields", {})
                
                return {
                    "id": data.get("id"),
                    "rev": data.get("rev"),
                    "type": fields.get("System.WorkItemType"),
                    "title": fields.get("System.Title"),
                    "description": fields.get("System.Description", ""),
                    "acceptance_criteria": fields.get("Microsoft.VSTS.Common.AcceptanceCriteria", ""),
                    "state": fields.get("System.State"),
                    "reason": fields.get("System.Reason"),
                    "assigned_to": fields.get("System.AssignedTo", {}).get("displayName") if fields.get("System.AssignedTo") else None,
                    "created_by": fields.get("System.CreatedBy", {}).get("displayName") if fields.get("System.CreatedBy") else None,
                    "area_path": fields.get("System.AreaPath"),
                    "iteration_path": fields.get("System.IterationPath"),
                    "tags": fields.get("System.Tags", ""),
                    "created_date": fields.get("System.CreatedDate"),
                    "changed_date": fields.get("System.ChangedDate"),
                    "url": data.get("url")
                }
                
        except Exception as e:
            logger.error(f"Failed to get work item {work_item_id}: {str(e)}")
            raise
    
    async def get_work_items(
        self,
        organization: str,
        project: str,
        pat: str,
        area_path: Optional[str] = None,
        iteration_path: Optional[str] = None,
        work_item_type: Optional[str] = None,
        state: Optional[str] = None,
        max_items: int = 100
    ) -> List[Dict[str, Any]]:
        """Get work items using WIQL (Work Item Query Language)."""
        try:
            headers = self._get_auth_header(pat)
            
            # Build WIQL query
            conditions = [f"[System.TeamProject] = '{project}'"]
            
            if area_path:
                conditions.append(f"[System.AreaPath] UNDER '{area_path}'")
            
            if iteration_path:
                conditions.append(f"[System.IterationPath] = '{iteration_path}'")
            
            if work_item_type:
                conditions.append(f"[System.WorkItemType] = '{work_item_type}'")
            
            if state:
                conditions.append(f"[System.State] = '{state}'")
            
            where_clause = " AND ".join(conditions)
            wiql = f"SELECT [System.Id] FROM WorkItems WHERE {where_clause} ORDER BY [System.ChangedDate] DESC"
            
            # Execute WIQL query
            url = f"{self.base_url}/{organization}/{project}/_apis/wit/wiql?api-version={self.api_version}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json={"query": wiql}
                )
                response.raise_for_status()
                
                data = response.json()
                work_item_refs = data.get("workItems", [])
                
                if not work_item_refs:
                    return []
                
                # Get full details for each work item (batch API)
                work_item_ids = [ref["id"] for ref in work_item_refs[:max_items]]
                ids_param = ",".join(str(id) for id in work_item_ids)
                
                batch_url = f"{self.base_url}/{organization}/_apis/wit/workitems?ids={ids_param}&$expand=all&api-version={self.api_version}"
                
                response = await client.get(batch_url, headers=headers)
                response.raise_for_status()
                
                batch_data = response.json()
                work_items = []
                
                for item in batch_data.get("value", []):
                    fields = item.get("fields", {})
                    work_items.append({
                        "id": item.get("id"),
                        "rev": item.get("rev"),
                        "type": fields.get("System.WorkItemType"),
                        "title": fields.get("System.Title"),
                        "description": fields.get("System.Description", ""),
                        "acceptance_criteria": fields.get("Microsoft.VSTS.Common.AcceptanceCriteria", ""),
                        "state": fields.get("System.State"),
                        "assigned_to": fields.get("System.AssignedTo", {}).get("displayName") if fields.get("System.AssignedTo") else None,
                        "area_path": fields.get("System.AreaPath"),
                        "iteration_path": fields.get("System.IterationPath"),
                        "tags": fields.get("System.Tags", ""),
                        "created_date": fields.get("System.CreatedDate"),
                        "changed_date": fields.get("System.ChangedDate")
                    })
                
                return work_items
                
        except Exception as e:
            logger.error(f"Failed to get work items: {str(e)}")
            raise
    
    async def update_work_item(
        self,
        organization: str,
        project: str,
        work_item_id: int,
        pat: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update work item fields."""
        try:
            headers = self._get_auth_header(pat)
            headers["Content-Type"] = "application/json-patch+json"
            
            # Build JSON patch operations
            operations = []
            for field_name, value in fields.items():
                operations.append({
                    "op": "add",
                    "path": f"/fields/{field_name}",
                    "value": value
                })
            
            url = f"{self.base_url}/{organization}/_apis/wit/workitems/{work_item_id}?api-version={self.api_version}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    url,
                    headers=headers,
                    json=operations
                )
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to update work item {work_item_id}: {str(e)}")
            raise
    
    async def add_work_item_comment(
        self,
        organization: str,
        project: str,
        work_item_id: int,
        pat: str,
        comment: str
    ) -> Dict[str, Any]:
        """Add a comment to a work item."""
        try:
            headers = self._get_auth_header(pat)
            
            url = f"{self.base_url}/{organization}/{project}/_apis/wit/workitems/{work_item_id}/comments?api-version={self.api_version}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json={"text": comment}
                )
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to add comment to work item {work_item_id}: {str(e)}")
            raise
    
    async def get_area_paths(self, organization: str, project: str, pat: str) -> List[str]:
        """Get all area paths for a project."""
        try:
            headers = self._get_auth_header(pat)
            url = f"{self.base_url}/{organization}/{project}/_apis/wit/classificationnodes/areas?$depth=10&api-version={self.api_version}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                def extract_paths(node, prefix=""):
                    paths = []
                    current_path = f"{prefix}{node.get('name')}"
                    paths.append(current_path)
                    
                    for child in node.get("children", []):
                        paths.extend(extract_paths(child, f"{current_path}\\"))
                    
                    return paths
                
                return extract_paths(data)
                
        except Exception as e:
            logger.error(f"Failed to get area paths: {str(e)}")
            raise
    
    async def get_iterations(self, organization: str, project: str, pat: str) -> List[Dict[str, Any]]:
        """Get all iterations (sprints) for a project."""
        try:
            headers = self._get_auth_header(pat)
            url = f"{self.base_url}/{organization}/{project}/_apis/wit/classificationnodes/iterations?$depth=10&api-version={self.api_version}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                def extract_iterations(node, prefix=""):
                    iterations = []
                    current_path = f"{prefix}{node.get('name')}"
                    
                    iteration = {
                        "path": current_path,
                        "name": node.get("name"),
                        "start_date": node.get("attributes", {}).get("startDate"),
                        "finish_date": node.get("attributes", {}).get("finishDate")
                    }
                    iterations.append(iteration)
                    
                    for child in node.get("children", []):
                        iterations.extend(extract_iterations(child, f"{current_path}\\"))
                    
                    return iterations
                
                return extract_iterations(data)
                
        except Exception as e:
            logger.error(f"Failed to get iterations: {str(e)}")
            raise
    
    async def link_commit_to_work_item(
        self,
        organization: str,
        project: str,
        work_item_id: int,
        pat: str,
        commit_url: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Link a Git commit to a work item."""
        try:
            headers = self._get_auth_header(pat)
            headers["Content-Type"] = "application/json-patch+json"
            
            operations = [
                {
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": "ArtifactLink",
                        "url": commit_url,
                        "attributes": {
                            "name": "Commit",
                            "comment": comment or "Linked from AutoGraph"
                        }
                    }
                }
            ]
            
            url = f"{self.base_url}/{organization}/_apis/wit/workitems/{work_item_id}?api-version={self.api_version}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    url,
                    headers=headers,
                    json=operations
                )
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to link commit to work item {work_item_id}: {str(e)}")
            raise
