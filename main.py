import io
import math
import os
import zipfile
import numpy as np

from pathlib import Path
from PIL import Image

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
MAX_COLUMNS = 2  # Maximum number of sprites per row
BACKGROUND_COLOR = (0, 0, 0, 0)  # Transparent (use (255,255,255) for solid white)

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
    raw_file_list = []

    # 1. Gather and sort files from ZIP alphabetically
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
        
        # 2. Automatically calculate how many animation frames exist per emotion slot
        # OMORI uses 4 distinct emotion states (Normal, Sad, Angry, Happy)
        frames_per_emotion = math.ceil(total_files / 4)
        print(f"Detected {total_files} total files. Splitting into 4 emotions with {frames_per_emotion} animation frames each.")

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

    # Fallback safety if the zip does not contain enough frames for all emotions
    base_frames = emotion_blocks["normal"]
    if not base_frames:
        print("Error: Could not extract base 'normal' animation frames.")
        return

    sad_frames = emotion_blocks["sad"] if emotion_blocks["sad"] else base_frames
    angry_frames = emotion_blocks["angry"] if emotion_blocks["angry"] else base_frames
    happy_frames = emotion_blocks["happy"] if emotion_blocks["happy"] else base_frames

    # Normalize frame lists to make sure they all have an identical count
    all_blocks = [base_frames, sad_frames, angry_frames, happy_frames]
    for block in all_blocks:
        while len(block) < frames_per_emotion:
            block.append(block[-1] if block else Image.new("RGBA", base_frames[0].size, (0,0,0,0)))

    # 4. Construct the grid layout layout rows
    # The columns map to: Normal Animation Block -> Sad Block -> Angry Block -> Happy Block
    sprite_matrix = [
        # Row 1: Normal
        base_frames,
        # Row 2: Hurt (Desaturated variants)
        [apply_desat(f) for f in sad_frames],
        # Row 3: Defeated (Inverted Hurt variants)
        [apply_invert(apply_desat(f)) for f in sad_frames],
        # Row 4: Sad (Blue Glow)
        [apply_emotion_glow(f, SAD_COLOR) for f in sad_frames],
        # Row 5: Angry (Red Glow)
        [apply_emotion_glow(f, ANGRY_COLOR) for f in angry_frames],
        # Row 6: Happy (Yellow Glow)
        [apply_emotion_glow(f, HAPPY_COLOR) for f in happy_frames]
    ]

    # 5. Canvas Composition Setup
    sprite_w, sprite_h = base_frames[0].size
    total_columns = frames_per_emotion
    sheet_w = frames_per_emotion * sprite_w
    sheet_h = 6 * sprite_h
    spritesheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

    # 6. Grid stitch block
    for row_idx, row_images in enumerate(sprite_matrix):
        for col_idx, img in enumerate(row_images):
            if img.size != (sprite_w, sprite_h):
                img = img.resize((sprite_w, sprite_h), Image.Resampling.LANCZOS)
                
            x = col_idx * sprite_w
            y = row_idx * sprite_h
            spritesheet.paste(img, (x, y), img)

    # 7. Output export
    spritesheet.save(output_path, "PNG")
    print(f"Animated sheet built successfully! Generated a {total_columns}x6 grid layout saved to {output_path}.")

if __name__ == "__main__":
    main()