import io
import math
import os
import zipfile
import numpy as np

from pathlib import Path
from PIL import Image

from filters import random_pick_glow
from printutil import print_error, print_with_timestamp

# This script creates sprite sheet and effect from individual image files
# This script is intended to replicate OMORI's enemy sprite sheet
# The standard final output are 4 columns and 6 rows, 
# Each row have different effects:
# - Row 1: Normal
# - Row 2: Hurt (Desaturate)
# - Row 3: Defeated (Desaturate + Invert color)
# - Row 4: Sad (Blue Glow)
# - Row 5: Angry (Red Glow)
# - Row 6: Happy (Yellow Glow)

# --- CONFIGURATION ---
ZIP_PATH ="input/Fairy.zip"
OUTPUT_SHEET = "output/spritesheet.png"
MAX_COLUMNS = 2  # Maximum number of sprites per row
BACKGROUND_COLOR = (0, 0, 0, 0)  # Transparent (use (255,255,255) for solid white)

def main():
    create_folder_structure()
    
    if not Path(ZIP_PATH).is_file():
        print_error(f"File not found at {ZIP_PATH}.")
        return

    spritesheet = create_spritesheet_from_zip(ZIP_PATH, MAX_COLUMNS)
    spritesheet.save(OUTPUT_SHEET, "PNG")

def create_spritesheet_from_zip(zip_path, max_cols):
    images = []

    with zipfile.ZipFile(zip_path, "r") as archive:
        for file_path in archive.namelist():
            
            # 1. Skip macOS metadata junk files and directory pointers
            if "__MACOSX" in file_path or file_path.endswith("/"):
                continue
                
            # 2. Extract only valid image files (ignoring hidden files like .DS_Store)
            file_name = os.path.basename(file_path)
            if file_name.lower().endswith((".png", ".jpg", ".jpeg")) and not file_name.startswith("."):
                
                print(f"Loading: {file_path}")  # Shows the nested path it found
                with archive.open(file_path) as file_stream:
                    img_bytes = file_stream.read()
                    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                    images.append(img)

    if not images:
        print("Error: No valid images found in the ZIP archive.")
        return

    num_images = len(images)
    print(f"Successfully loaded {num_images} total images.")

    # 3. Determine grid layout dimensions
    sprite_w, sprite_h = images[0].size
    cols = min(num_images, max_cols)
    rows = math.ceil(num_images / cols)

    sheet_w = cols * sprite_w
    sheet_h = rows * sprite_h

    # 4. Create the canvas and compile the spritesheet
    spritesheet = Image.new("RGBA", (sheet_w, sheet_h), BACKGROUND_COLOR)

    for idx, img in enumerate(images):
        if img.size != (sprite_w, sprite_h):
            img = img.resize((sprite_w, sprite_h), Image.Resampling.LANCZOS)

        col_idx = idx % cols
        row_idx = idx // cols

        x = col_idx * sprite_w
        y = row_idx * sprite_h

        spritesheet.paste(img, (x, y), img)

    return spritesheet

def process_image(sprite):
    result_image = random_pick_glow(sprite)
    result_image.save(output_path, optimize=True, compress_level=9)
    print_with_timestamp(f"Noisy glow sprite saved to {output_path}")

def create_folder_structure():
    Path("input").mkdir(parents=True, exist_ok=True)
    Path("output").mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    main()