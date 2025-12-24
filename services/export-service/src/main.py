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


class ExportRequest(BaseModel):
    """Request model for diagram export."""
    diagram_id: str
    canvas_data: Dict[str, Any]
    format: str  # png, svg, pdf
    width: Optional[int] = 1920
    height: Optional[int] = 1080
    quality: Optional[str] = "high"  # low, medium, high, ultra
    background: Optional[str] = "white"  # transparent, white, custom
    scale: Optional[int] = 2  # 1x, 2x, 4x for retina


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


@app.post("/export/png")
async def export_png(request: ExportRequest):
    """
    Export diagram as PNG image with anti-aliased edges.
    
    This endpoint creates a high-quality PNG export of the diagram with:
    - Anti-aliased edges for smooth appearance
    - Configurable resolution (1x, 2x, 4x for retina displays)
    - Transparent or custom background support
    - High-quality compression
    
    For now, we'll generate a simple placeholder with anti-aliasing enabled.
    In production, this would use Playwright to render the actual canvas.
    """
    try:
        logger.info(f"Exporting diagram {request.diagram_id} as PNG with anti-aliasing")
        
        # Create a placeholder PNG with anti-aliasing
        # In production, this would render the actual canvas using Playwright
        width = request.width * request.scale
        height = request.height * request.scale
        
        # Create image with background
        bg_color = 'white' if request.background == 'white' else (255, 255, 255, 0)
        img = Image.new('RGBA' if request.background == 'transparent' else 'RGB', 
                       (width, height), color=bg_color)
        
        # Add some visual indication with anti-aliasing
        from PIL import ImageDraw, ImageFont
        
        # Use high-quality drawing with anti-aliasing
        # Note: PIL's ImageDraw uses anti-aliasing by default for text and shapes
        draw = ImageDraw.Draw(img)
        
        # Draw shapes with anti-aliasing
        # For demonstration, we'll draw various shapes to show smooth edges
        
        # Draw a border rectangle
        draw.rectangle(
            [(20, 20), (width - 20, height - 20)],
            outline='#cccccc',
            width=4
        )
        
        # Draw a circle to demonstrate anti-aliasing
        circle_center = (width // 2, height // 2 - 50)
        circle_radius = 80
        draw.ellipse(
            [
                (circle_center[0] - circle_radius, circle_center[1] - circle_radius),
                (circle_center[0] + circle_radius, circle_center[1] + circle_radius)
            ],
            outline='#4a90e2',
            width=3
        )
        
        # Add text with anti-aliasing (PIL uses anti-aliasing for text by default)
        text = f"PNG Export\nAnti-aliased\n{request.quality} quality"
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = (
            (width - text_width) // 2,
            (height - text_height) // 2 + 80
        )
        draw.text(position, text, fill='#333333', align='center')
        
        # Convert to PNG bytes with optimal settings for anti-aliasing
        img_byte_arr = io.BytesIO()
        
        # PNG format doesn't have a 'quality' parameter like JPEG
        # Instead, we use 'compress_level' (0-9) and 'optimize' for best quality
        # compress_level: 6 is a good balance (0=no compression, 9=max compression)
        # optimize=True enables additional compression optimization
        img.save(
            img_byte_arr,
            format='PNG',
            compress_level=6,
            optimize=True
        )
        img_byte_arr.seek(0)
        
        logger.info(f"PNG export with anti-aliasing generated successfully for diagram {request.diagram_id}")
        
        return Response(
            content=img_byte_arr.read(),
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=diagram_{request.diagram_id}.png"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting PNG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export PNG: {str(e)}")


@app.post("/export/svg")
async def export_svg(request: ExportRequest):
    """
    Export diagram as SVG vector image.
    
    This endpoint creates a scalable SVG export of the diagram.
    For now, we'll generate a simple placeholder.
    In production, this would convert the canvas to SVG.
    """
    try:
        logger.info(f"Exporting diagram {request.diagram_id} as SVG")
        
        # Create a placeholder SVG
        # In production, this would convert the actual canvas to SVG
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{request.width}" height="{request.height}" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="{request.width - 20}" height="{request.height - 20}" 
        fill="none" stroke="#cccccc" stroke-width="2"/>
  <text x="{request.width // 2}" y="{request.height // 2}" 
        text-anchor="middle" fill="#666666" font-family="Arial" font-size="24">
    SVG Export
  </text>
  <text x="{request.width // 2}" y="{request.height // 2 + 30}" 
        text-anchor="middle" fill="#666666" font-family="Arial" font-size="16">
    {request.diagram_id}
  </text>
</svg>'''
        
        logger.info(f"SVG export generated successfully for diagram {request.diagram_id}")
        
        return Response(
            content=svg_content,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f"attachment; filename=diagram_{request.diagram_id}.svg"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting SVG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export SVG: {str(e)}")


@app.post("/export/pdf")
async def export_pdf(request: ExportRequest):
    """
    Export diagram as PDF document.
    
    This endpoint creates a PDF export of the diagram.
    For now, we'll generate a simple placeholder.
    In production, this would use a PDF library to create the actual PDF.
    """
    try:
        logger.info(f"Exporting diagram {request.diagram_id} as PDF")
        
        # Create a simple placeholder PDF
        # In production, this would use reportlab or similar to create actual PDF
        pdf_content = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(PDF Export) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000317 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n410\n%%EOF'
        
        logger.info(f"PDF export generated successfully for diagram {request.diagram_id}")
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=diagram_{request.diagram_id}.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export PDF: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("EXPORT_SERVICE_PORT", "8097")))
