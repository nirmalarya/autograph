/**
 * Generate PWA icons using Canvas API
 * This script creates placeholder icons for the PWA
 * In production, replace with actual branded icons
 */

const fs = require('fs');
const path = require('path');
const { createCanvas } = require('canvas');

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const iconDir = __dirname;

// Create a simple icon with the AutoGraph logo
function createIcon(size, isMaskable = false) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');

  // Background
  const gradient = ctx.createLinearGradient(0, 0, size, size);
  gradient.addColorStop(0, '#3b82f6'); // Blue
  gradient.addColorStop(1, '#2563eb'); // Darker blue
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);

  // Add padding for maskable icons
  const padding = isMaskable ? size * 0.1 : 0;
  const contentSize = size - (padding * 2);
  const contentX = padding;
  const contentY = padding;

  // Draw "A" for AutoGraph
  ctx.fillStyle = '#ffffff';
  ctx.font = `bold ${contentSize * 0.6}px Arial`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('A', contentX + contentSize / 2, contentY + contentSize / 2);

  // Draw graph lines (simplified)
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = Math.max(2, size / 64);
  ctx.globalAlpha = 0.3;

  // Draw grid
  const gridSize = contentSize / 4;
  for (let i = 1; i < 4; i++) {
    // Vertical lines
    ctx.beginPath();
    ctx.moveTo(contentX + i * gridSize, contentY);
    ctx.lineTo(contentX + i * gridSize, contentY + contentSize);
    ctx.stroke();

    // Horizontal lines
    ctx.beginPath();
    ctx.moveTo(contentX, contentY + i * gridSize);
    ctx.lineTo(contentX + contentSize, contentY + i * gridSize);
    ctx.stroke();
  }

  return canvas;
}

// Generate icons
console.log('Generating PWA icons...');

sizes.forEach(size => {
  // Regular icon
  const canvas = createIcon(size, false);
  const buffer = canvas.toBuffer('image/png');
  const filename = path.join(iconDir, `icon-${size}x${size}.png`);
  fs.writeFileSync(filename, buffer);
  console.log(`✓ Created ${filename}`);

  // Maskable icons (only for 192 and 512)
  if (size === 192 || size === 512) {
    const maskableCanvas = createIcon(size, true);
    const maskableBuffer = maskableCanvas.toBuffer('image/png');
    const maskableFilename = path.join(iconDir, `icon-${size}x${size}-maskable.png`);
    fs.writeFileSync(maskableFilename, maskableBuffer);
    console.log(`✓ Created ${maskableFilename}`);
  }
});

// Generate shortcut icons
const shortcuts = ['new', 'dashboard', 'ai'];
shortcuts.forEach(shortcut => {
  const canvas = createCanvas(96, 96);
  const ctx = canvas.getContext('2d');

  // Background
  ctx.fillStyle = '#3b82f6';
  ctx.fillRect(0, 0, 96, 96);

  // Icon text
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 48px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  
  const icons = {
    'new': '+',
    'dashboard': '☰',
    'ai': '✨'
  };
  
  ctx.fillText(icons[shortcut], 48, 48);

  const buffer = canvas.toBuffer('image/png');
  const filename = path.join(iconDir, `shortcut-${shortcut}.png`);
  fs.writeFileSync(filename, buffer);
  console.log(`✓ Created ${filename}`);
});

console.log('✓ All icons generated successfully!');
