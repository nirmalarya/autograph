"""Quality validation for AI-generated diagrams."""
import re
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from .layout_algorithms import Node, Edge, LayoutEngine

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of diagram quality validation."""
    score: float  # 0-100
    passed: bool
    issues: List[str]
    metrics: Dict[str, any]


class QualityValidator:
    """
    Quality validation system for AI-generated diagrams.
    
    Features:
    - #327: Check overlapping nodes
    - #328: Spacing minimum 50px
    - #329: Alignment check
    - #330: Readability score 0-100
    """
    
    MIN_SPACING = 50.0  # Feature #328
    MIN_QUALITY_SCORE = 80.0  # Threshold for auto-retry
    
    @staticmethod
    def validate_diagram(
        mermaid_code: str,
        context: str = ""
    ) -> ValidationResult:
        """
        Comprehensive diagram quality validation.
        
        Returns validation result with score and issues.
        """
        issues = []
        metrics = {}
        
        # Parse diagram
        try:
            nodes, edges = LayoutEngine.parse_mermaid_graph(mermaid_code)
            metrics["node_count"] = len(nodes)
            metrics["edge_count"] = len(edges)
        except Exception as e:
            logger.error(f"Failed to parse diagram: {str(e)}")
            return ValidationResult(
                score=0.0,
                passed=False,
                issues=["Failed to parse Mermaid diagram"],
                metrics={}
            )
        
        if not nodes:
            return ValidationResult(
                score=0.0,
                passed=False,
                issues=["No nodes found in diagram"],
                metrics=metrics
            )
        
        # Feature #327: Check overlapping nodes
        overlap_result = QualityValidator._check_overlaps(nodes)
        issues.extend(overlap_result["issues"])
        metrics["overlap_count"] = overlap_result["overlap_count"]
        metrics["overlap_score"] = overlap_result["score"]
        
        # Feature #328: Check spacing minimum 50px
        spacing_result = QualityValidator._check_spacing(nodes)
        issues.extend(spacing_result["issues"])
        metrics["min_spacing"] = spacing_result["min_spacing"]
        metrics["spacing_score"] = spacing_result["score"]
        
        # Feature #329: Check alignment
        alignment_result = QualityValidator._check_alignment(nodes)
        issues.extend(alignment_result["issues"])
        metrics["alignment_score"] = alignment_result["score"]
        
        # Feature #330: Calculate readability score
        readability_result = QualityValidator._calculate_readability(
            mermaid_code, nodes, edges
        )
        issues.extend(readability_result["issues"])
        metrics["readability_score"] = readability_result["score"]
        
        # Calculate overall score
        overall_score = (
            overlap_result["score"] * 0.30 +
            spacing_result["score"] * 0.25 +
            alignment_result["score"] * 0.20 +
            readability_result["score"] * 0.25
        )
        
        metrics["overall_score"] = overall_score
        
        passed = overall_score >= QualityValidator.MIN_QUALITY_SCORE
        
        logger.info(
            f"Quality validation: {overall_score:.1f}/100 "
            f"({'PASSED' if passed else 'FAILED'})"
        )
        
        return ValidationResult(
            score=overall_score,
            passed=passed,
            issues=issues,
            metrics=metrics
        )
    
    @staticmethod
    def _check_overlaps(nodes: List[Node]) -> Dict[str, any]:
        """
        Feature #327: Check for overlapping nodes.
        
        Returns score and list of overlapping pairs.
        """
        issues = []
        overlap_count = 0
        
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i >= j:
                    continue
                
                # Calculate distance between centers
                dx = node2.x - node1.x
                dy = node2.y - node1.y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Check if nodes overlap (including their dimensions)
                min_dist = (node1.width + node2.width) / 2
                
                if distance < min_dist:
                    overlap_count += 1
                    issues.append(
                        f"Nodes '{node1.label}' and '{node2.label}' overlap "
                        f"(distance: {distance:.1f}px, minimum: {min_dist:.1f}px)"
                    )
        
        # Calculate score (0 overlaps = 100, more overlaps = lower score)
        total_pairs = len(nodes) * (len(nodes) - 1) / 2
        if total_pairs == 0:
            score = 100.0
        else:
            score = max(0, 100 - (overlap_count / total_pairs * 100))
        
        return {
            "score": score,
            "overlap_count": overlap_count,
            "issues": issues
        }
    
    @staticmethod
    def _check_spacing(nodes: List[Node]) -> Dict[str, any]:
        """
        Feature #328: Check spacing minimum 50px.
        
        Ensures nodes have adequate spacing for readability.
        """
        issues = []
        min_spacing_found = float('inf')
        violation_count = 0
        
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i >= j:
                    continue
                
                # Calculate distance
                dx = node2.x - node1.x
                dy = node2.y - node1.y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Account for node dimensions
                spacing = distance - (node1.width + node2.width) / 2
                
                min_spacing_found = min(min_spacing_found, spacing)
                
                if spacing < QualityValidator.MIN_SPACING:
                    violation_count += 1
                    issues.append(
                        f"Insufficient spacing between '{node1.label}' and '{node2.label}': "
                        f"{spacing:.1f}px (minimum: {QualityValidator.MIN_SPACING}px)"
                    )
        
        # Calculate score
        if min_spacing_found == float('inf'):
            score = 100.0
        elif min_spacing_found >= QualityValidator.MIN_SPACING:
            score = 100.0
        else:
            # Score decreases as spacing gets worse
            score = max(0, (min_spacing_found / QualityValidator.MIN_SPACING) * 100)
        
        return {
            "score": score,
            "min_spacing": min_spacing_found if min_spacing_found != float('inf') else 0,
            "violation_count": violation_count,
            "issues": issues
        }
    
    @staticmethod
    def _check_alignment(nodes: List[Node]) -> Dict[str, any]:
        """
        Feature #329: Check alignment.
        
        Good diagrams have nodes aligned horizontally or vertically.
        """
        if len(nodes) < 2:
            return {"score": 100.0, "issues": []}
        
        issues = []
        alignment_tolerance = 10.0  # pixels
        
        # Check horizontal alignment (same Y coordinate)
        y_coords = [node.y for node in nodes]
        y_groups = QualityValidator._group_similar_values(y_coords, alignment_tolerance)
        
        # Check vertical alignment (same X coordinate)
        x_coords = [node.x for node in nodes]
        x_groups = QualityValidator._group_similar_values(x_coords, alignment_tolerance)
        
        # Calculate alignment score
        # More nodes in aligned groups = better score
        max_aligned_h = max(len(group) for group in y_groups) if y_groups else 1
        max_aligned_v = max(len(group) for group in x_groups) if x_groups else 1
        max_aligned = max(max_aligned_h, max_aligned_v)
        
        alignment_ratio = max_aligned / len(nodes)
        score = alignment_ratio * 100
        
        if score < 50:
            issues.append(
                f"Poor alignment: only {max_aligned}/{len(nodes)} nodes aligned"
            )
        
        return {
            "score": score,
            "horizontal_groups": len(y_groups),
            "vertical_groups": len(x_groups),
            "max_aligned": max_aligned,
            "issues": issues
        }
    
    @staticmethod
    def _group_similar_values(values: List[float], tolerance: float) -> List[List[float]]:
        """Group values that are within tolerance of each other."""
        if not values:
            return []
        
        sorted_values = sorted(values)
        groups = []
        current_group = [sorted_values[0]]
        
        for i in range(1, len(sorted_values)):
            if abs(sorted_values[i] - sorted_values[i-1]) <= tolerance:
                current_group.append(sorted_values[i])
            else:
                groups.append(current_group)
                current_group = [sorted_values[i]]
        
        groups.append(current_group)
        return groups
    
    @staticmethod
    def _calculate_readability(
        mermaid_code: str,
        nodes: List[Node],
        edges: List[Edge]
    ) -> Dict[str, any]:
        """
        Feature #330: Calculate readability score 0-100.
        
        Factors:
        - Code clarity (proper syntax, formatting)
        - Label quality (descriptive, not too long)
        - Complexity (not too many nodes/edges)
        - Edge crossing (fewer crossings = better)
        """
        issues = []
        scores = []
        
        # 1. Code clarity (25%)
        code_lines = [line.strip() for line in mermaid_code.split('\n') if line.strip()]
        has_declaration = any(
            line.startswith('graph') or line.startswith('flowchart') 
            for line in code_lines
        )
        
        code_score = 100.0 if has_declaration else 50.0
        scores.append(code_score * 0.25)
        
        if not has_declaration:
            issues.append("Missing graph declaration (graph TD or flowchart)")
        
        # 2. Label quality (25%)
        long_labels = [
            node for node in nodes 
            if len(node.label) > 50
        ]
        
        if long_labels:
            label_score = max(0, 100 - len(long_labels) * 20)
            issues.append(f"{len(long_labels)} labels are too long (>50 chars)")
        else:
            label_score = 100.0
        
        scores.append(label_score * 0.25)
        
        # 3. Complexity (25%)
        node_count = len(nodes)
        edge_count = len(edges)
        
        if node_count > 20:
            complexity_score = max(0, 100 - (node_count - 20) * 5)
            issues.append(f"High complexity: {node_count} nodes (recommended: < 20)")
        elif node_count < 2:
            complexity_score = 50.0
            issues.append("Too few nodes for meaningful diagram")
        else:
            complexity_score = 100.0
        
        scores.append(complexity_score * 0.25)
        
        # 4. Edge density (25%)
        # Ideal: 1-2 edges per node
        if node_count > 0:
            edge_ratio = edge_count / node_count
            if 1.0 <= edge_ratio <= 2.0:
                density_score = 100.0
            elif edge_ratio < 1.0:
                density_score = 70.0  # Too sparse
            else:
                density_score = max(0, 100 - (edge_ratio - 2.0) * 20)
                issues.append(f"High edge density: {edge_ratio:.1f} edges per node")
        else:
            density_score = 0.0
        
        scores.append(density_score * 0.25)
        
        # Overall readability score
        overall = sum(scores)
        
        return {
            "score": overall,
            "code_clarity": code_score,
            "label_quality": label_score,
            "complexity": complexity_score,
            "edge_density": density_score,
            "issues": issues
        }
    
    @staticmethod
    def should_retry(validation_result: ValidationResult) -> bool:
        """
        Determine if diagram generation should be retried.
        
        Retry if score is below threshold and issues are fixable.
        """
        if validation_result.score >= QualityValidator.MIN_QUALITY_SCORE:
            return False
        
        # Check if issues are fixable
        fixable_keywords = ["overlap", "spacing", "alignment"]
        fixable_issues = sum(
            1 for issue in validation_result.issues
            if any(keyword in issue.lower() for keyword in fixable_keywords)
        )
        
        return fixable_issues > 0
    
    @staticmethod
    def generate_improvement_suggestions(
        validation_result: ValidationResult
    ) -> List[str]:
        """
        Generate suggestions for improving diagram quality.
        """
        suggestions = []
        metrics = validation_result.metrics
        
        if metrics.get("overlap_count", 0) > 0:
            suggestions.append(
                "Increase spacing between nodes to prevent overlaps"
            )
        
        if metrics.get("min_spacing", 100) < QualityValidator.MIN_SPACING:
            suggestions.append(
                f"Ensure minimum {QualityValidator.MIN_SPACING}px spacing between nodes"
            )
        
        if metrics.get("alignment_score", 100) < 60:
            suggestions.append(
                "Improve alignment by positioning nodes in rows or columns"
            )
        
        if metrics.get("readability_score", 100) < 70:
            if metrics.get("node_count", 0) > 20:
                suggestions.append(
                    "Reduce complexity by grouping related nodes or splitting into multiple diagrams"
                )
            
            if metrics.get("edge_density", 1) > 3:
                suggestions.append(
                    "Simplify connections by removing redundant edges"
                )
        
        return suggestions


class QualityReport:
    """Generate human-readable quality reports."""
    
    @staticmethod
    def generate_report(validation_result: ValidationResult) -> str:
        """Generate a formatted quality report."""
        report_lines = []
        
        report_lines.append("=== DIAGRAM QUALITY REPORT ===")
        report_lines.append("")
        report_lines.append(f"Overall Score: {validation_result.score:.1f}/100")
        report_lines.append(f"Status: {'✓ PASSED' if validation_result.passed else '✗ FAILED'}")
        report_lines.append("")
        
        if validation_result.metrics:
            report_lines.append("Metrics:")
            for key, value in validation_result.metrics.items():
                if isinstance(value, float):
                    report_lines.append(f"  - {key}: {value:.1f}")
                else:
                    report_lines.append(f"  - {key}: {value}")
            report_lines.append("")
        
        if validation_result.issues:
            report_lines.append(f"Issues ({len(validation_result.issues)}):")
            for i, issue in enumerate(validation_result.issues, 1):
                report_lines.append(f"  {i}. {issue}")
            report_lines.append("")
        
        suggestions = QualityValidator.generate_improvement_suggestions(validation_result)
        if suggestions:
            report_lines.append("Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                report_lines.append(f"  {i}. {suggestion}")
        
        return '\n'.join(report_lines)
