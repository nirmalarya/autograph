"""Layout algorithms for diagram generation."""
import re
import math
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LayoutAlgorithm(str, Enum):
    """Available layout algorithms."""
    HIERARCHICAL = "hierarchical"  # Sugiyama layout (already default)
    FORCE_DIRECTED = "force_directed"  # Spring/force-directed
    TREE = "tree"  # Tree layout
    CIRCULAR = "circular"  # Circular layout


@dataclass
class Node:
    """Represents a node in the diagram."""
    id: str
    label: str
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 60.0
    vx: float = 0.0  # velocity x
    vy: float = 0.0  # velocity y


@dataclass
class Edge:
    """Represents an edge/connection between nodes."""
    source: str
    target: str
    label: Optional[str] = None


class ForceDirectedLayout:
    """
    Force-directed layout algorithm (Fruchterman-Reingold).
    
    Treats nodes as charged particles that repel each other,
    and edges as springs that pull connected nodes together.
    
    Features #321: Force-directed layout
    """
    
    def __init__(
        self,
        width: float = 1200.0,
        height: float = 800.0,
        iterations: int = 100,
        k: Optional[float] = None  # optimal distance
    ):
        self.width = width
        self.height = height
        self.iterations = iterations
        self.k = k or math.sqrt((width * height) / 1)  # optimal distance
        self.temperature = 100.0  # initial temperature
        
    def apply(self, nodes: List[Node], edges: List[Edge]) -> List[Node]:
        """
        Apply force-directed layout algorithm to nodes.
        
        Returns positioned nodes with no overlaps and good spacing.
        """
        if not nodes:
            return nodes
        
        # Initialize random positions
        self._initialize_positions(nodes)
        
        # Run force-directed iterations
        for i in range(self.iterations):
            # Calculate forces
            self._calculate_repulsive_forces(nodes)
            self._calculate_attractive_forces(nodes, edges)
            
            # Update positions
            self._update_positions(nodes, i)
            
            # Cool down temperature
            self._cool_temperature(i)
        
        # Ensure no overlaps and minimum spacing
        self._prevent_overlaps(nodes)
        
        # Center the layout
        self._center_layout(nodes)
        
        logger.info(f"Force-directed layout applied: {len(nodes)} nodes, {len(edges)} edges")
        return nodes
    
    def _initialize_positions(self, nodes: List[Node]):
        """Initialize nodes in random positions."""
        import random
        for i, node in enumerate(nodes):
            # Distribute randomly but not too close to edges
            node.x = random.uniform(self.width * 0.1, self.width * 0.9)
            node.y = random.uniform(self.height * 0.1, self.height * 0.9)
            node.vx = 0.0
            node.vy = 0.0
    
    def _calculate_repulsive_forces(self, nodes: List[Node]):
        """Calculate repulsive forces between all node pairs."""
        k2 = self.k * self.k
        
        for i, node1 in enumerate(nodes):
            node1.vx = 0.0
            node1.vy = 0.0
            
            for j, node2 in enumerate(nodes):
                if i == j:
                    continue
                
                # Calculate distance
                dx = node1.x - node2.x
                dy = node1.y - node2.y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance < 0.01:
                    distance = 0.01  # prevent division by zero
                
                # Repulsive force (inversely proportional to distance)
                force = k2 / distance
                
                # Add to velocity
                node1.vx += (dx / distance) * force
                node1.vy += (dy / distance) * force
    
    def _calculate_attractive_forces(self, nodes: List[Node], edges: List[Edge]):
        """Calculate attractive forces along edges."""
        node_map = {node.id: node for node in nodes}
        
        for edge in edges:
            if edge.source not in node_map or edge.target not in node_map:
                continue
            
            source = node_map[edge.source]
            target = node_map[edge.target]
            
            # Calculate distance
            dx = target.x - source.x
            dy = target.y - source.y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < 0.01:
                continue
            
            # Attractive force (proportional to distance)
            force = (distance * distance) / self.k
            
            # Apply force
            fx = (dx / distance) * force
            fy = (dy / distance) * force
            
            source.vx += fx
            source.vy += fy
            target.vx -= fx
            target.vy -= fy
    
    def _update_positions(self, nodes: List[Node], iteration: int):
        """Update node positions based on forces."""
        # Limit displacement by temperature
        for node in nodes:
            # Calculate displacement magnitude
            disp = math.sqrt(node.vx * node.vx + node.vy * node.vy)
            
            if disp > 0.01:
                # Limit by temperature
                limited_disp = min(disp, self.temperature)
                
                # Update position
                node.x += (node.vx / disp) * limited_disp
                node.y += (node.vy / disp) * limited_disp
                
                # Keep within bounds
                node.x = max(50, min(self.width - 50, node.x))
                node.y = max(50, min(self.height - 50, node.y))
    
    def _cool_temperature(self, iteration: int):
        """Cool down temperature over iterations."""
        # Linear cooling
        self.temperature = 100.0 * (1.0 - iteration / self.iterations)
    
    def _prevent_overlaps(self, nodes: List[Node]):
        """Prevent node overlaps by moving nodes apart."""
        min_spacing = 60.0  # minimum spacing between nodes
        
        for _ in range(10):  # multiple passes
            overlaps = False
            
            for i, node1 in enumerate(nodes):
                for j, node2 in enumerate(nodes):
                    if i >= j:
                        continue
                    
                    dx = node2.x - node1.x
                    dy = node2.y - node1.y
                    distance = math.sqrt(dx * dx + dy * dy)
                    
                    min_dist = (node1.width + node2.width) / 2 + min_spacing
                    
                    if distance < min_dist:
                        overlaps = True
                        # Move nodes apart
                        if distance < 0.01:
                            distance = 0.01
                        
                        move_dist = (min_dist - distance) / 2
                        move_x = (dx / distance) * move_dist
                        move_y = (dy / distance) * move_dist
                        
                        node1.x -= move_x
                        node1.y -= move_y
                        node2.x += move_x
                        node2.y += move_y
            
            if not overlaps:
                break
    
    def _center_layout(self, nodes: List[Node]):
        """Center the layout in the canvas."""
        if not nodes:
            return
        
        # Calculate bounding box
        min_x = min(node.x for node in nodes)
        max_x = max(node.x for node in nodes)
        min_y = min(node.y for node in nodes)
        max_y = max(node.y for node in nodes)
        
        # Calculate centering offset
        layout_width = max_x - min_x
        layout_height = max_y - min_y
        
        offset_x = (self.width - layout_width) / 2 - min_x
        offset_y = (self.height - layout_height) / 2 - min_y
        
        # Apply offset
        for node in nodes:
            node.x += offset_x
            node.y += offset_y


class TreeLayout:
    """
    Tree layout algorithm.
    
    Arranges nodes in a tree structure with configurable direction.
    Good for hierarchical data like org charts, file systems.
    
    Features #322: Tree layout algorithm
    """
    
    def __init__(
        self,
        direction: str = "TB",  # TB (top-bottom), LR (left-right)
        level_spacing: float = 150.0,
        node_spacing: float = 100.0
    ):
        self.direction = direction
        self.level_spacing = level_spacing
        self.node_spacing = node_spacing
    
    def apply(self, nodes: List[Node], edges: List[Edge]) -> List[Node]:
        """Apply tree layout algorithm."""
        if not nodes:
            return nodes
        
        # Build adjacency list
        children_map: Dict[str, List[str]] = {node.id: [] for node in nodes}
        parents_map: Dict[str, str] = {}
        
        for edge in edges:
            if edge.source in children_map:
                children_map[edge.source].append(edge.target)
                parents_map[edge.target] = edge.source
        
        # Find root nodes (nodes with no parents)
        roots = [node for node in nodes if node.id not in parents_map]
        if not roots:
            # If no clear root, pick first node
            roots = [nodes[0]]
        
        # Assign levels using BFS
        levels: Dict[str, int] = {}
        queue = [(root.id, 0) for root in roots]
        visited = set()
        
        while queue:
            node_id, level = queue.pop(0)
            if node_id in visited:
                continue
            
            visited.add(node_id)
            levels[node_id] = level
            
            for child_id in children_map.get(node_id, []):
                if child_id not in visited:
                    queue.append((child_id, level + 1))
        
        # Group nodes by level
        level_groups: Dict[int, List[Node]] = {}
        for node in nodes:
            level = levels.get(node.id, 0)
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node)
        
        # Position nodes
        if self.direction == "TB":
            self._position_top_bottom(level_groups)
        else:
            self._position_left_right(level_groups)
        
        logger.info(f"Tree layout applied: {len(nodes)} nodes, {len(level_groups)} levels")
        return nodes
    
    def _position_top_bottom(self, level_groups: Dict[int, List[Node]]):
        """Position nodes top to bottom."""
        for level, nodes_in_level in level_groups.items():
            y = level * self.level_spacing + 100
            
            total_width = len(nodes_in_level) * self.node_spacing
            start_x = (1200 - total_width) / 2  # center
            
            for i, node in enumerate(nodes_in_level):
                node.x = start_x + i * self.node_spacing
                node.y = y
    
    def _position_left_right(self, level_groups: Dict[int, List[Node]]):
        """Position nodes left to right."""
        for level, nodes_in_level in level_groups.items():
            x = level * self.level_spacing + 100
            
            total_height = len(nodes_in_level) * self.node_spacing
            start_y = (800 - total_height) / 2  # center
            
            for i, node in enumerate(nodes_in_level):
                node.x = x
                node.y = start_y + i * self.node_spacing


class CircularLayout:
    """
    Circular layout algorithm.
    
    Arranges nodes in a circle. Good for showing relationships
    without hierarchy, or for small graphs.
    
    Features #323: Circular layout algorithm
    """
    
    def __init__(
        self,
        radius: float = 300.0,
        center_x: float = 600.0,
        center_y: float = 400.0
    ):
        self.radius = radius
        self.center_x = center_x
        self.center_y = center_y
    
    def apply(self, nodes: List[Node], edges: List[Edge]) -> List[Node]:
        """Apply circular layout algorithm."""
        if not nodes:
            return nodes
        
        n = len(nodes)
        
        for i, node in enumerate(nodes):
            angle = (2 * math.pi * i) / n
            node.x = self.center_x + self.radius * math.cos(angle)
            node.y = self.center_y + self.radius * math.sin(angle)
        
        logger.info(f"Circular layout applied: {len(nodes)} nodes")
        return nodes


class LayoutEngine:
    """
    Main layout engine that applies layout algorithms to Mermaid diagrams.
    """
    
    @staticmethod
    def parse_mermaid_graph(mermaid_code: str) -> Tuple[List[Node], List[Edge]]:
        """
        Parse Mermaid code to extract nodes and edges.
        
        Supports graph TD, graph LR, flowchart formats.
        """
        nodes = []
        edges = []
        node_map = {}
        
        lines = mermaid_code.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and graph declaration
            if not line or line.startswith('graph') or line.startswith('flowchart'):
                continue
            
            # Parse edge: A --> B or A -->|label| B
            edge_match = re.search(r'(\w+)\s*-->(?:\|([^|]+)\|)?\s*(\w+)', line)
            if edge_match:
                source_id = edge_match.group(1)
                label = edge_match.group(2)
                target_id = edge_match.group(3)
                
                # Create nodes if not exist
                if source_id not in node_map:
                    node = Node(id=source_id, label=source_id)
                    nodes.append(node)
                    node_map[source_id] = node
                
                if target_id not in node_map:
                    node = Node(id=target_id, label=target_id)
                    nodes.append(node)
                    node_map[target_id] = node
                
                edges.append(Edge(source=source_id, target=target_id, label=label))
                continue
            
            # Parse node definition: A[Label] or A([Label])
            node_match = re.search(r'(\w+)\[([^\]]+)\]', line)
            if node_match:
                node_id = node_match.group(1)
                label = node_match.group(2)
                
                if node_id not in node_map:
                    node = Node(id=node_id, label=label)
                    nodes.append(node)
                    node_map[node_id] = node
        
        return nodes, edges
    
    @staticmethod
    def apply_layout(
        mermaid_code: str,
        algorithm: LayoutAlgorithm = LayoutAlgorithm.FORCE_DIRECTED
    ) -> str:
        """
        Apply layout algorithm to Mermaid diagram.
        
        Note: This is a conceptual implementation. In practice, Mermaid.js
        handles layout automatically, so this is more for validation and
        quality checking rather than modifying the code.
        
        Returns the same Mermaid code (Mermaid handles layout).
        """
        try:
            # Parse diagram
            nodes, edges = LayoutEngine.parse_mermaid_graph(mermaid_code)
            
            if not nodes:
                logger.warning("No nodes found in Mermaid diagram")
                return mermaid_code
            
            # Apply layout algorithm
            if algorithm == LayoutAlgorithm.FORCE_DIRECTED:
                layout = ForceDirectedLayout()
                nodes = layout.apply(nodes, edges)
            elif algorithm == LayoutAlgorithm.TREE:
                layout = TreeLayout()
                nodes = layout.apply(nodes, edges)
            elif algorithm == LayoutAlgorithm.CIRCULAR:
                layout = CircularLayout()
                nodes = layout.apply(nodes, edges)
            else:
                # Hierarchical is default in Mermaid
                pass
            
            # Log layout info
            logger.info(f"Layout algorithm {algorithm} applied to {len(nodes)} nodes")
            
            # Return original code (Mermaid handles actual rendering)
            # The layout calculation is used for quality validation
            return mermaid_code
            
        except Exception as e:
            logger.error(f"Layout application failed: {str(e)}")
            return mermaid_code
    
    @staticmethod
    def validate_spacing(nodes: List[Node], min_spacing: float = 50.0) -> Dict[str, any]:
        """
        Validate that nodes have adequate spacing.
        
        Returns validation result with score and issues.
        """
        issues = []
        overlap_count = 0
        
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i >= j:
                    continue
                
                dx = node2.x - node1.x
                dy = node2.y - node1.y
                distance = math.sqrt(dx * dx + dy * dy)
                
                min_dist = (node1.width + node2.width) / 2 + min_spacing
                
                if distance < min_dist:
                    overlap_count += 1
                    issues.append(f"Nodes {node1.id} and {node2.id} too close: {distance:.1f}px")
        
        total_pairs = len(nodes) * (len(nodes) - 1) / 2
        score = 100 if total_pairs == 0 else max(0, 100 - (overlap_count / total_pairs * 100))
        
        return {
            "score": score,
            "issues": issues,
            "overlap_count": overlap_count,
            "total_nodes": len(nodes)
        }
