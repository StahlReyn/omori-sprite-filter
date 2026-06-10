import io
import json
import math
import os
import zipfile

from pathlib import Path
from PIL import Image, ImageEnhance

from filters import apply_desat, apply_invert, apply_emotion_glow
from printutil import print_error, print_with_timestamp

# This script creates sprite sheet and effect from individual image files
# This script is intended to replicate OMORI's enemy sprite sheet

# The input image files will likely at least contain Neutral, Sad, Angry, Happy,
# But rows may reuse the same image as well.
# The standard final output are 4 columns and 6 rows,
# Each row have different effects:
# - Row 1: Neutral
# - Row 2: Hurt (Sad or Angry with Desat)
# - Row 3: Defeated (Hurt with Invert color)
# - Row 4: Sad (Blue Glow)
# - Row 5: Angry (Red Glow)
# - Row 6: Happy (Yellow Glow)

def load_config(config_path="config.json"):
    with open(config_path, "r") as f:
        return json.load(f)

def main():
    config = load_config()
    create_folder_structure()

    if not Path(config["zip_path"]).is_file():
        print_error(f"File not found at {config['zip_path']}.")
        return

    create_omori_animated_spritesheet(config)

def create_folder_structure():
    Path("input").mkdir(parents=True, exist_ok=True)
    Path("output").mkdir(parents=True, exist_ok=True)

def create_omori_animated_spritesheet(config):
    zip_path = config["zip_path"]
    output_path = config["output_sheet"]
    variant_count = config["variant_count"]
    lighten_hurt = config["lighten_hurt"]
    invert_defeat = config["invert_defeat"]

    # Gather and sort files from ZIP alphabetically
    emotion_blocks = grab_emotion_blocks(zip_path, variant_count)

    frames_per_emotion = len(emotion_blocks["neutral"])
    frame_size = emotion_blocks["neutral"][0].size

    # Normalize frame lists to make sure they all have an identical count
    for block in emotion_blocks:
        while len(block) < frames_per_emotion:
            block.append(block[-1] if block else Image.new("RGBA", emotion_blocks["neutral"].size, (0,0,0,0)))

    i = 0
    hurt_row = []
    for f in emotion_blocks[row_name_convert("hurt", config)]:
        img = apply_desat(f)
        if lighten_hurt and i % 2 == 0: # Lighten every other sprite
            img = ImageEnhance.Brightness(img).enhance(1.2)
        hurt_row.append(img)

    defeat_row = []
    for f in emotion_blocks[row_name_convert("defeat", config)]:
        img = apply_desat(f)
        if invert_defeat:
            img = apply_invert(img)
        defeat_row.append(img)

    # Grid layout layout rows
    sad_color = tuple(config["colors"]["sad"])
    angry_color = tuple(config["colors"]["angry"])
    happy_color = tuple(config["colors"]["happy"])

    sprite_matrix = [
        emotion_blocks["neutral"],
        hurt_row,
        defeat_row,
        [apply_emotion_glow(f, sad_color) for f in emotion_blocks["sad"]],
        [apply_emotion_glow(f, angry_color) for f in emotion_blocks["angry"]],
        [apply_emotion_glow(f, happy_color) for f in emotion_blocks["happy"]]
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
    print_with_timestamp(f"Animated sheet built successfully! Generated a {total_columns}x6 grid layout saved to {output_path}.")

def row_name_convert(base_name, config):
    if config["row_reuse"]:
        new_block_name = config["row_reuse"][base_name]
        print_with_timestamp(f"Using {new_block_name} for {base_name}")
        return new_block_name
    else:
        return base_name

def grab_emotion_blocks(zip_path, variant_count):
    print_with_timestamp(f"Loading Zip: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as archive:
        raw_file_list = filter_image_file_list(archive)
        total_files = len(raw_file_list)
        
        # Calculate how many animation frames exist per emotion slot
        frames_per_emotion = math.ceil(total_files / variant_count)
        print_with_timestamp(f"Found {total_files} files. Splitting into {variant_count} variants with {frames_per_emotion} frames each.")

        # Lists to hold the frame blocks
        emotion_blocks = {"neutral": [], "sad": [], "angry": [], "happy": []}

        # 3. Read files and slice them into sequential animation blocks
        for idx, file_path in enumerate(raw_file_list):
            print_with_timestamp(f"File Got: {file_path}")
            with archive.open(file_path) as file_stream:
                img = Image.open(io.BytesIO(file_stream.read())).convert("RGBA")
                
                # Determine which block this sequence index belongs to
                block_idx = idx // frames_per_emotion
                if block_idx == 0:
                    emotion_blocks["neutral"].append(img)
                elif block_idx == 1:
                    emotion_blocks["sad"].append(img)
                elif block_idx == 2:
                    emotion_blocks["angry"].append(img)
                elif block_idx == 3:
                    emotion_blocks["happy"].append(img)
    return emotion_blocks

def filter_image_file_list(archive):
    raw_file_list = []
    for file_path in archive.namelist():
        if "__MACOSX" in file_path or file_path.endswith("/"):
            continue
        file_name = os.path.basename(file_path)
        if file_name.lower().endswith((".png", ".jpg", ".jpeg")) and not file_name.startswith("."):
            raw_file_list.append(file_path)

    if not raw_file_list:
        print_error("No valid images found in the ZIP archive.")
        return

    raw_file_list.sort()
    return raw_file_list

if __name__ == "__main__":
    main()