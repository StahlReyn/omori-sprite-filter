import io
import math
import os
import zipfile
import numpy as np

from pathlib import Path
from PIL import Image, ImageEnhance

from filters import apply_desat, apply_invert, apply_emotion_glow
from printutil import print_error, print_with_timestamp

# This script creates sprite sheet and effect from individual image files
# This script is intended to replicate OMORI's enemy sprite sheet

# The input image files will likely at least contain Normal, Sad, Angry, Happy, 
# But rows may reuse the same image as well.
# The standard final output are 4 columns and 6 rows, 
# Each row have different effects:
# - Row 1: Normal
# - Row 2: Hurt (Sad or Angry with Desat)
# - Row 3: Defeated (Hurt with Invert color)
# - Row 4: Sad (Blue Glow)
# - Row 5: Angry (Red Glow)
# - Row 6: Happy (Yellow Glow)

# --- CONFIGURATION ---
ZIP_PATH ="input/Fairy.zip"
OUTPUT_SHEET = "output/spritesheet.png"

FRAMES_PER_BLOCK = 2
VARIANT_COUNT = 4
LIGHTEN_HURT = True
INVERT_DEFEAT = True

SAD_COLOR = (0, 100, 255)
ANGRY_COLOR = (255, 0, 50)
HAPPY_COLOR = (255, 220, 0)

def main():
    create_folder_structure()
    
    if not Path(ZIP_PATH).is_file():
        print_error(f"File not found at {ZIP_PATH}.")
        return

    create_omori_animated_spritesheet(ZIP_PATH, OUTPUT_SHEET)

def create_folder_structure():
    Path("input").mkdir(parents=True, exist_ok=True)
    Path("output").mkdir(parents=True, exist_ok=True)

# By default, it is likely the individual images are exported from art program, 
# making it in format of "filename_0001" with incrementing number. 
# The number can be divided by number of column to decide which emotion it belongs 
# to in order by default if unspecified
def create_omori_animated_spritesheet(zip_path, output_path):
    # Gather and sort files from ZIP alphabetically
    emotion_blocks = grab_emotion_blocks(zip_path, VARIANT_COUNT)

    frames_per_emotion = len(emotion_blocks["normal"])
    frame_size = emotion_blocks["normal"][0].size

    # Normalize frame lists to make sure they all have an identical count
    for block in emotion_blocks:
        while len(block) < frames_per_emotion:
            block.append(block[-1] if block else Image.new("RGBA", emotion_blocks["normal"].size, (0,0,0,0)))
    
    i = 0
    hurt_row = []
    for f in emotion_blocks["sad"]:
        img = apply_desat(f)
        if LIGHTEN_HURT and i % 2 == 0: # Lighten every other sprite
            img = ImageEnhance.Brightness(img).enhance(1.2)
        hurt_row.append(img)
    
    defeat_row = []
    for f in emotion_blocks["sad"]:
        img = apply_desat(f)
        if INVERT_DEFEAT:
            img = apply_invert(img)
        defeat_row.append(img)

    # Grid layout layout rows
    sprite_matrix = [
        emotion_blocks["normal"],
        hurt_row,
        defeat_row,
        [apply_emotion_glow(f, SAD_COLOR) for f in emotion_blocks["sad"]],
        [apply_emotion_glow(f, ANGRY_COLOR) for f in emotion_blocks["angry"]],
        [apply_emotion_glow(f, HAPPY_COLOR) for f in emotion_blocks["happy"]]
    ]

    # Canvas Composition Setup
    sprite_w, sprite_h = frame_size
    total_columns = frames_per_emotion
    sheet_w = frames_per_emotion * sprite_w
    sheet_h = 6 * sprite_h
    spritesheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

    # Grid stitch block
    for row_idx, row_images in enumerate(sprite_matrix):
        for col_idx, img in enumerate(row_images):
            if img.size != (sprite_w, sprite_h):
                img = img.resize((sprite_w, sprite_h), Image.Resampling.LANCZOS)
                
            x = col_idx * sprite_w
            y = row_idx * sprite_h
            spritesheet.paste(img, (x, y), img)

    # Output export
    spritesheet.save(output_path, "PNG")
    print(f"Animated sheet built successfully! Generated a {total_columns}x6 grid layout saved to {output_path}.")

def grab_emotion_blocks(zip_path, variant_count):
    raw_file_list = []
    with zipfile.ZipFile(zip_path, "r") as archive:
        for file_path in archive.namelist():
            if "__MACOSX" in file_path or file_path.endswith("/"):
                continue
            file_name = os.path.basename(file_path)
            if file_name.lower().endswith((".png", ".jpg", ".jpeg")) and not file_name.startswith("."):
                raw_file_list.append(file_path)

        if not raw_file_list:
            print("Error: No valid images found in the ZIP archive.")
            return

        raw_file_list.sort()
        total_files = len(raw_file_list)
        
        # Calculate how many animation frames exist per emotion slot
        frames_per_emotion = math.ceil(total_files / variant_count)
        print(f"Found {total_files} files. Splitting into {variant_count} variants with {frames_per_emotion} frames each.")

        # Lists to hold the frame blocks
        emotion_blocks = {"normal": [], "sad": [], "angry": [], "happy": []}

        # 3. Read files and slice them into sequential animation blocks
        for idx, file_path in enumerate(raw_file_list):
            with archive.open(file_path) as file_stream:
                img = Image.open(io.BytesIO(file_stream.read())).convert("RGBA")
                
                # Determine which block this sequence index belongs to
                block_idx = idx // frames_per_emotion
                if block_idx == 0:
                    emotion_blocks["normal"].append(img)
                elif block_idx == 1:
                    emotion_blocks["sad"].append(img)
                elif block_idx == 2:
                    emotion_blocks["angry"].append(img)
                elif block_idx == 3:
                    emotion_blocks["happy"].append(img)
    return emotion_blocks
    
if __name__ == "__main__":
    main()