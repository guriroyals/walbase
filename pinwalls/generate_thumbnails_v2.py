#!/usr/bin/env python3
"""
Thumbnail Generator for Pinwalls (Multi-Category Support)

This script:
1. Reads all category JSON files in `categories/`
2. For each category, finds its corresponding image folder
3. Generates compressed thumbnails (400px width, ~50KB) in `thumbnails/[Category]/`
4. Updates the category JSON file to point to the new thumbnails

Usage:
    cd /Users/guri/Documents/GitHub/walbase/pinwalls
    python3 generate_thumbnails_v2.py

Requirements:
    pip3 install Pillow
"""

import os
import json
from pathlib import Path
from PIL import Image

# Configuration
THUMBNAIL_WIDTH = 400  # Width in pixels
THUMBNAIL_QUALITY = 80  # JPEG quality (1-100)
BASE_DIR = Path("/Users/guri/Documents/GitHub/walbase/pinwalls")
CATEGORIES_DIR = BASE_DIR / "categories"
THUMBNAIL_BASE_DIR = BASE_DIR / "thumbnails"

def generate_thumbnail(input_path: Path, output_path: Path) -> bool:
    """Generate a compressed thumbnail from an image."""
    try:
        with Image.open(input_path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            aspect_ratio = img.height / img.width
            new_height = int(THUMBNAIL_WIDTH * aspect_ratio)
            
            img_resized = img.resize((THUMBNAIL_WIDTH, new_height), Image.Resampling.LANCZOS)
            img_resized.save(output_path, 'JPEG', quality=THUMBNAIL_QUALITY, optimize=True)
            
            return True
            
    except Exception as e:
        print(f"✗ {input_path.name}: Error - {e}")
        return False

def process_category(json_path: Path):
    """Process a single category JSON and its images."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Handle both old flat list and new wrapped object
        wallpapers = data.get("Wallpapers", data) if isinstance(data, dict) else data
        
        if not isinstance(wallpapers, list):
            print(f"⚠️  Skipping {json_path.name}: Invalid format")
            return 0, 0
            
        category_name = json_path.stem
        
        # We need to map the JSON name (e.g. Ghibli_inspired.json) to the folder name (e.g. "Ghibli Inspired")
        # Let's peek at the first wallpaper's URL to find the actual folder name
        if not wallpapers:
            return 0, 0
            
        first_url = wallpapers[0].get("url", "")
        if not first_url or "/" not in first_url:
            return 0, 0
            
        image_folder_name = first_url.split("/")[0]
        image_dir = BASE_DIR / image_folder_name
        thumb_out_dir = THUMBNAIL_BASE_DIR / image_folder_name
        
        if not image_dir.exists():
            print(f"⚠️  Image folder for {category_name} not found: {image_dir}")
            return 0, 0
            
        thumb_out_dir.mkdir(parents=True, exist_ok=True)
        
        imgs_processed = 0
        json_updated = 0
        
        for item in wallpapers:
            if 'url' in item:
                # url is like "Abstract/image_name.jpg"
                url_filename = item['url']
                rel_path = Path(url_filename)
                
                # Full path to original image
                img_path = BASE_DIR / rel_path
                
                if img_path.exists():
                    # Generate thumbnail
                    base_name = img_path.stem
                    thumb_rel_path = f"thumbnails/{image_folder_name}/{base_name}_thumb.jpg"
                    thumb_full_path = THUMBNAIL_BASE_DIR / image_folder_name / f"{base_name}_thumb.jpg"
                    
                    if generate_thumbnail(img_path, thumb_full_path):
                        imgs_processed += 1
                        # Update JSON entry
                        if 'thumbnail' in item and item['thumbnail'] != thumb_rel_path:
                            item['thumbnail'] = thumb_rel_path
                            json_updated += 1
                        elif 'thumbnail' not in item:
                            item['thumbnail'] = thumb_rel_path
                            json_updated += 1
                            
        # Write back JSON if updated
        if json_updated > 0:
            with open(json_path, 'w', encoding='utf-8') as f:
                # Always save in the new wrapped format
                out_data = {"Wallpapers": wallpapers}
                json.dump(out_data, f, indent=4, ensure_ascii=False)
                
        return imgs_processed, json_updated

    except Exception as e:
        print(f"Error processing {json_path.name}: {e}")
        return 0, 0

def main():
    print("Thumbnail Generator v2 (Multi-Category)")
    print("-" * 50)
    
    if not CATEGORIES_DIR.exists():
        print(f"❌ Categories directory not found: {CATEGORIES_DIR}")
        return
        
    json_files = list(CATEGORIES_DIR.glob("*.json"))
    print(f"Found {len(json_files)} category JSON files.\n")
    
    total_imgs = 0
    total_updates = 0
    
    for json_file in sorted(json_files):
        print(f"Processing: {json_file.name}")
        imgs, updates = process_category(json_file)
        print(f"  → Generated {imgs} thumbnails, updated {updates} JSON entries\n")
        total_imgs += imgs
        total_updates += updates
        
    print("-" * 50)
    print(f"✅ Total: Generated {total_imgs} thumbnails, updated {total_updates} JSON entries")

if __name__ == "__main__":
    main()
