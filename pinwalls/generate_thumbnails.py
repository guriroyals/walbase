#!/usr/bin/env python3
"""
Thumbnail Generator for Pinwalls

This script:
1. Reads all images from the current directory
2. Generates compressed thumbnails (400px width, ~50KB)
3. Saves them to a 'thumbnails' subfolder
4. Updates the JSON file to point to the new thumbnails

Usage:
    cd "/Users/guri/Downloads/all wallpapers"
    python3 generate_thumbnails.py

Requirements:
    pip3 install Pillow
"""

import os
import json
from pathlib import Path
from PIL import Image

# Configuration
THUMBNAIL_WIDTH = 400  # Width in pixels (height auto-calculated to maintain aspect ratio)
THUMBNAIL_QUALITY = 80  # JPEG quality (1-100)
THUMBNAIL_DIR = "thumbnails"
JSON_FILE = "1.json"

def generate_thumbnail(input_path: Path, output_path: Path) -> bool:
    """Generate a compressed thumbnail from an image."""
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate new height maintaining aspect ratio
            aspect_ratio = img.height / img.width
            new_height = int(THUMBNAIL_WIDTH * aspect_ratio)
            
            # Resize using high-quality downsampling
            img_resized = img.resize((THUMBNAIL_WIDTH, new_height), Image.Resampling.LANCZOS)
            
            # Save as JPEG with compression
            img_resized.save(output_path, 'JPEG', quality=THUMBNAIL_QUALITY, optimize=True)
            
            # Get file sizes for comparison
            original_size = input_path.stat().st_size / 1024  # KB
            thumb_size = output_path.stat().st_size / 1024  # KB
            
            print(f"✓ {input_path.name}: {original_size:.0f}KB → {thumb_size:.0f}KB ({100 - (thumb_size/original_size*100):.0f}% smaller)")
            return True
            
    except Exception as e:
        print(f"✗ {input_path.name}: Error - {e}")
        return False

def update_json(json_path: Path, thumbnail_dir: str) -> int:
    """Update JSON file to use thumbnail paths."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        updated_count = 0
        for item in data:
            if 'thumbnail' in item and 'url' in item:
                # Get the base filename without extension
                url_filename = item['url']
                base_name = Path(url_filename).stem
                
                # New thumbnail filename (always .jpg since we save as JPEG)
                thumb_filename = f"{thumbnail_dir}/{base_name}_thumb.jpg"
                
                # Check if thumbnail exists
                thumb_path = json_path.parent / thumb_filename
                if thumb_path.exists():
                    item['thumbnail'] = thumb_filename
                    updated_count += 1
        
        # Write updated JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return updated_count
        
    except Exception as e:
        print(f"Error updating JSON: {e}")
        return 0

def main():
    # Get current directory
    base_dir = Path(__file__).parent
    thumb_dir = base_dir / THUMBNAIL_DIR
    json_path = base_dir / JSON_FILE
    
    # Create thumbnails directory
    thumb_dir.mkdir(exist_ok=True)
    print(f"📁 Thumbnail directory: {thumb_dir}")
    print(f"📋 JSON file: {json_path}")
    print(f"📐 Thumbnail width: {THUMBNAIL_WIDTH}px")
    print(f"🗜️  Quality: {THUMBNAIL_QUALITY}%")
    print("-" * 50)
    
    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    images = [f for f in base_dir.iterdir() 
              if f.is_file() and f.suffix.lower() in image_extensions]
    
    print(f"Found {len(images)} images to process\n")
    
    # Generate thumbnails
    success_count = 0
    for img_path in sorted(images):
        # Output filename (always .jpg)
        output_name = f"{img_path.stem}_thumb.jpg"
        output_path = thumb_dir / output_name
        
        if generate_thumbnail(img_path, output_path):
            success_count += 1
    
    print("-" * 50)
    print(f"✅ Generated {success_count}/{len(images)} thumbnails")
    
    # Update JSON
    if json_path.exists():
        print(f"\n📝 Updating {JSON_FILE}...")
        updated = update_json(json_path, THUMBNAIL_DIR)
        print(f"✅ Updated {updated} entries in JSON")
    else:
        print(f"\n⚠️  JSON file not found: {json_path}")
    
    # Calculate total savings
    original_total = sum(f.stat().st_size for f in images) / (1024 * 1024)  # MB
    thumb_total = sum(f.stat().st_size for f in thumb_dir.iterdir() if f.is_file()) / (1024 * 1024)  # MB
    
    print(f"\n📊 Total size reduction:")
    print(f"   Original images: {original_total:.1f} MB")
    print(f"   Thumbnails: {thumb_total:.1f} MB")
    print(f"   Savings: {original_total - thumb_total:.1f} MB ({100 - (thumb_total/original_total*100):.0f}%)")

if __name__ == "__main__":
    main()
