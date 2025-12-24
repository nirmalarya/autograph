#!/usr/bin/env python3
"""
Generate PWA icons using PIL (Pillow)
This script creates placeholder icons for the PWA
In production, replace with actual branded icons
"""

import os
from PIL import Image, ImageDraw, ImageFont

# Icon sizes
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
ICON_DIR = os.path.dirname(os.path.abspath(__file__))

def create_icon(size, is_maskable=False):
    """Create a simple icon with AutoGraph branding"""
    # Create image with gradient-like background
    img = Image.new('RGB', (size, size), color='#3b82f6')
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect (simple version)
    for y in range(size):
        color_value = int(59 + (37 * y / size))  # Gradient from #3b to #25
        draw.line([(0, y), (size, y)], fill=(color_value, 130, 246))
    
    # Add padding for maskable icons
    padding = int(size * 0.1) if is_maskable else 0
    content_size = size - (padding * 2)
    content_x = padding
    content_y = padding
    
    # Draw "A" for AutoGraph
    try:
        # Try to use a nice font
        font_size = int(content_size * 0.6)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw text
    text = "A"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = content_x + (content_size - text_width) // 2
    text_y = content_y + (content_size - text_height) // 2
    
    draw.text((text_x, text_y), text, fill='white', font=font)
    
    # Draw grid lines (simplified)
    grid_color = (255, 255, 255, 80)  # Semi-transparent white
    line_width = max(1, size // 64)
    grid_size = content_size // 4
    
    for i in range(1, 4):
        # Vertical lines
        x = content_x + i * grid_size
        draw.line([(x, content_y), (x, content_y + content_size)], 
                  fill=grid_color, width=line_width)
        
        # Horizontal lines
        y = content_y + i * grid_size
        draw.line([(content_x, y), (content_x + content_size, y)], 
                  fill=grid_color, width=line_width)
    
    return img

def create_shortcut_icon(name, emoji):
    """Create a shortcut icon"""
    size = 96
    img = Image.new('RGB', (size, size), color='#3b82f6')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
    except:
        font = ImageFont.load_default()
    
    # Draw emoji/text
    bbox = draw.textbbox((0, 0), emoji, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2
    
    draw.text((text_x, text_y), emoji, fill='white', font=font)
    
    return img

# Generate icons
print('Generating PWA icons...')

for size in SIZES:
    # Regular icon
    img = create_icon(size, is_maskable=False)
    filename = os.path.join(ICON_DIR, f'icon-{size}x{size}.png')
    img.save(filename, 'PNG')
    print(f'✓ Created icon-{size}x{size}.png')
    
    # Maskable icons (only for 192 and 512)
    if size in [192, 512]:
        maskable_img = create_icon(size, is_maskable=True)
        maskable_filename = os.path.join(ICON_DIR, f'icon-{size}x{size}-maskable.png')
        maskable_img.save(maskable_filename, 'PNG')
        print(f'✓ Created icon-{size}x{size}-maskable.png')

# Generate shortcut icons
shortcuts = {
    'new': '+',
    'dashboard': '☰',
    'ai': '✨'
}

for name, emoji in shortcuts.items():
    img = create_shortcut_icon(name, emoji)
    filename = os.path.join(ICON_DIR, f'shortcut-{name}.png')
    img.save(filename, 'PNG')
    print(f'✓ Created shortcut-{name}.png')

print('✓ All icons generated successfully!')
