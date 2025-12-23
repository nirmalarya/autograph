"""Export Service - High-quality PNG/SVG/PDF export."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import os
import io
import json
import logging
from dotenv import load_dotenv
from PIL import Image
import base64

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AutoGraph v3 Export Service",
    description="High-quality diagram export service",
    version="1.0.0"
)


class ThumbnailRequest(BaseModel):
    """Request model for thumbnail generation."""
    diagram_id: str
    canvas_data: Dict[str, Any]
    width: int = 256
    height: int = 256


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "export-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.post("/thumbnail")
async def generate_thumbnail(request: ThumbnailRequest):
    """
    Generate a thumbnail for a diagram.
    
    This endpoint creates a 256x256 PNG preview of the diagram canvas.
    For now, we'll generate a simple placeholder thumbnail.
    In production, this would use Playwright to render the actual canvas.
    """
    try:
        logger.info(f"Generating thumbnail for diagram {request.diagram_id}")
        
        # Create a simple placeholder thumbnail
        # In production, this would render the actual canvas using Playwright
        img = Image.new('RGB', (request.width, request.height), color='#f0f0f0')
        
        # Add some visual indication
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        # Draw a border
        draw.rectangle(
            [(10, 10), (request.width - 10, request.height - 10)],
            outline='#cccccc',
            width=2
        )
        
        # Add text
        text = "Diagram\nPreview"
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = (
            (request.width - text_width) // 2,
            (request.height - text_height) // 2
        )
        draw.text(position, text, fill='#666666')
        
        # Convert to PNG bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Return as base64 for easy storage
        img_base64 = base64.b64encode(img_byte_arr.read()).decode('utf-8')
        
        logger.info(f"Thumbnail generated successfully for diagram {request.diagram_id}")
        
        return {
            "diagram_id": request.diagram_id,
            "thumbnail_base64": img_base64,
            "width": request.width,
            "height": request.height,
            "format": "PNG"
        }
        
    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate thumbnail: {str(e)}")


@app.post("/thumbnail/png")
async def generate_thumbnail_png(request: ThumbnailRequest):
    """
    Generate a thumbnail and return as PNG image.
    """
    try:
        logger.info(f"Generating PNG thumbnail for diagram {request.diagram_id}")
        
        # Create a simple placeholder thumbnail
        img = Image.new('RGB', (request.width, request.height), color='#f0f0f0')
        
        # Add some visual indication
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        
        # Draw a border
        draw.rectangle(
            [(10, 10), (request.width - 10, request.height - 10)],
            outline='#cccccc',
            width=2
        )
        
        # Add text
        text = "Diagram\nPreview"
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = (
            (request.width - text_width) // 2,
            (request.height - text_height) // 2
        )
        draw.text(position, text, fill='#666666')
        
        # Convert to PNG bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        logger.info(f"PNG thumbnail generated successfully for diagram {request.diagram_id}")
        
        return Response(
            content=img_byte_arr.read(),
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename=thumbnail_{request.diagram_id}.png"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating PNG thumbnail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate thumbnail: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("EXPORT_SERVICE_PORT", "8097")))
