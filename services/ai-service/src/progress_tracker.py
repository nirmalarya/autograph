"""Progress tracking for AI generation with detailed status updates."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum
import uuid


class GenerationStatus(str, Enum):
    """Generation status stages."""
    ANALYZING = "analyzing"
    GENERATING = "generating"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProgressUpdate:
    """Represents a single progress update."""
    generation_id: str
    status: GenerationStatus
    progress: float  # 0-100
    message: str
    timestamp: str
    details: Optional[Dict] = None


class ProgressTracker:
    """Track generation progress with detailed status updates."""

    def __init__(self):
        # In-memory storage: generation_id -> List[ProgressUpdate]
        self._progress: Dict[str, List[ProgressUpdate]] = {}
        self._active_generations: Dict[str, str] = {}  # generation_id -> current_status

    def create_generation(self, generation_id: Optional[str] = None) -> str:
        """Create a new generation tracking entry."""
        gen_id = generation_id or str(uuid.uuid4())
        self._progress[gen_id] = []
        self._active_generations[gen_id] = GenerationStatus.ANALYZING

        # Add initial update
        self.update(
            gen_id,
            GenerationStatus.ANALYZING,
            progress=0.0,
            message="Analyzing prompt..."
        )

        return gen_id

    def update(
        self,
        generation_id: str,
        status: GenerationStatus,
        progress: float,
        message: str,
        details: Optional[Dict] = None
    ):
        """Add a progress update."""
        if generation_id not in self._progress:
            self._progress[generation_id] = []

        update = ProgressUpdate(
            generation_id=generation_id,
            status=status,
            progress=progress,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            details=details
        )

        self._progress[generation_id].append(update)
        self._active_generations[generation_id] = status

    def analyzing(self, generation_id: str):
        """Update to analyzing phase."""
        self.update(
            generation_id,
            GenerationStatus.ANALYZING,
            progress=10.0,
            message="Analyzing prompt..."
        )

    def generating(self, generation_id: str):
        """Update to generating phase."""
        self.update(
            generation_id,
            GenerationStatus.GENERATING,
            progress=40.0,
            message="Generating layout..."
        )

    def rendering(self, generation_id: str):
        """Update to rendering phase."""
        self.update(
            generation_id,
            GenerationStatus.RENDERING,
            progress=80.0,
            message="Rendering diagram..."
        )

    def complete(self, generation_id: str, result: Optional[Dict] = None):
        """Mark generation as complete."""
        self.update(
            generation_id,
            GenerationStatus.COMPLETED,
            progress=100.0,
            message="Generation completed successfully",
            details=result
        )

    def fail(self, generation_id: str, error: str):
        """Mark generation as failed."""
        self.update(
            generation_id,
            GenerationStatus.FAILED,
            progress=100.0,
            message=f"Generation failed: {error}",
            details={"error": error}
        )

    def get_latest(self, generation_id: str) -> Optional[ProgressUpdate]:
        """Get latest progress update for a generation."""
        if generation_id not in self._progress or not self._progress[generation_id]:
            return None
        return self._progress[generation_id][-1]

    def get_all(self, generation_id: str) -> List[ProgressUpdate]:
        """Get all progress updates for a generation."""
        return self._progress.get(generation_id, [])

    def get_current_status(self, generation_id: str) -> Optional[GenerationStatus]:
        """Get current status of a generation."""
        return self._active_generations.get(generation_id)

    def cleanup(self, generation_id: str):
        """Remove a completed generation from tracking."""
        self._progress.pop(generation_id, None)
        self._active_generations.pop(generation_id, None)


# Global singleton instance
_progress_tracker = None


def get_progress_tracker() -> ProgressTracker:
    """Get global progress tracker instance."""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker
