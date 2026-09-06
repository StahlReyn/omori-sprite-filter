import io
import math
import os
import zipfile

from pathlib import Path
from PIL import Image, ImageEnhance

from filters import apply_desat, apply_invert, apply_random_pick_glow, apply_channel_multiplier
from image_utils import load_config, process_image, select_config
from printutil import print_error, print_with_timestamp, print_info

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

def read_path(prompt):
    return input(prompt).strip().strip('"').strip("'")

def default_output_path(input_path):
    path = Path(input_path)
    if path.is_file():
        return path.with_suffix(".png")
    return path.parent / f"{path.name}.png"

def main():
    config_path = "config.json"
    if not Path(config_path).is_file():
        print_error("config.json not found. Create it before running the program.")
        return
    config = select_config(load_config(config_path))

    print_info("HINT: Drag and drop a file on Windows copies file path.")
    input_path = read_path("Enter input ZIP or folder path: ")
    input_is_valid = Path(input_path).is_file() or Path(input_path).is_dir()
    if not input_is_valid:
        print_error(f"Input path not found at {input_path}.")
        return

    output_path = read_path("Enter output image file path: ")
    if output_path == "":
        output_path = default_output_path(input_path)
        print_info(f"Default output to {output_path}")

    if config.get("type") == "portrait":
        from portrait import create_sprite_sheet
        create_sprite_sheet(input_path, output_path, config)
    else:
        create_omori_animated_spritesheet(input_path, output_path, config)

    input("Press any key to exit.")

def create_omori_animated_spritesheet(input_path, output_path, config):
    variant_names = config["variant_names"]
    lighten_hurt = config["lighten_hurt"]
    invert_defeat = config["invert_defeat"]
    row_reuse = config["row_reuse"]
    glow_settings = config["glow_settings"]

    # Gather and sort files from ZIP alphabetically
    emotion_blocks = grab_emotion_blocks(input_path, variant_names, config)

    frames_per_emotion = len(emotion_blocks["neutral"])
    frame_size = emotion_blocks["neutral"][0].size

    # Normalize frame lists to make sure they all have an identical count
    for block in emotion_blocks.values():
        while len(block) < frames_per_emotion:
            block.append(block[-1] if block else Image.new("RGBA", frame_size, (0,0,0,0)))

    i = 0
    hurt_row = []
    for i, f in enumerate(emotion_blocks[row_name_convert("hurt", row_reuse)]):
        print_with_timestamp(f"Process Hurt Effect")
        img = apply_desat(f)
        if lighten_hurt and i % 2 == 0: # Lighten every other sprite
            img = ImageEnhance.Brightness(img).enhance(1.2)
        hurt_row.append(img)

    defeat_row = []
    for f in emotion_blocks[row_name_convert("defeat", row_reuse)]:
        print_with_timestamp(f"Process Defeat Effect")
        img = apply_desat(f)
        if invert_defeat:
            img = apply_invert(img)
        defeat_row.append(img)

    # Grid layout layout rows
    glow_colors = config["glow_colors"]
    sad_color = tuple(glow_colors["sad"])
    angry_color = tuple(glow_colors["angry"])
    happy_color = tuple(glow_colors["happy"])
    
    sprite_matrix = [
        emotion_blocks["neutral"],
        hurt_row,
        defeat_row,
        [apply_glow_config(f, sad_color, glow_settings) for f in emotion_blocks["sad"]],
        [apply_glow_config(f, angry_color, glow_settings) for f in emotion_blocks["angry"]],
        [apply_glow_config(f, happy_color, glow_settings) for f in emotion_blocks["happy"]]
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
            print_with_timestamp(f"Pasting ({row_idx}, {col_idx})")
            if img.size != (sprite_w, sprite_h):
                img = img.resize((sprite_w, sprite_h), Image.Resampling.LANCZOS)

            x = col_idx * sprite_w
            y = row_idx * sprite_h
            spritesheet.paste(img, (x, y), img)

    # Output export
    spritesheet.save(output_path, "PNG")
    print_with_timestamp(f"Finished! Generated a {total_columns}x6 grid layout saved to {output_path}.")
    
def apply_glow_config(img, glow_color, setting):
    if "multiply_strength" in setting:
        strength = float(setting["multiply_strength"])
        if strength != 0:
            print_with_timestamp(f"Process Tint {glow_color}")
            # No tint is white, pure tint is the color (0 to Target)
            img = apply_channel_multiplier(img, glow_color, strength / 255)
    
    print_with_timestamp(f"Process Glow {glow_color}")
    return apply_random_pick_glow(
        img=img,
        glow_color=glow_color,
        blur_radius=setting["blur_radius"],
        expand_size=setting["expand_size"], 
        pick_radius=setting["pick_radius"]
    )

def row_name_convert(base_name, row_reuse):
    if row_reuse[base_name]:
        new_block_name = row_reuse[base_name]
        print_with_timestamp(f"Using {new_block_name} for {base_name}.")
        return new_block_name
    else:
        return base_name

def apply_frame_order(emotion_blocks, frame_order=None, duplicate_last_frame=False):
    if frame_order is None:
        ordered_blocks = emotion_blocks
    elif not frame_order:
        raise ValueError("frame_order must contain at least one frame index.")

    else:
        ordered_blocks = {}
        for name, frames in emotion_blocks.items():
            if any(not isinstance(index, int) or index < 0 or index >= len(frames) for index in frame_order):
                raise ValueError(f"frame_order contains an invalid index for {name}.")
            ordered_blocks[name] = [frames[index] for index in frame_order]

    if duplicate_last_frame:
        for frames in ordered_blocks.values():
            if not frames:
                raise ValueError("Cannot duplicate the final frame of an empty block.")
            frames.append(frames[-1])
    return ordered_blocks

def grab_emotion_blocks(zip_path, variant_names, config):
    input_path = Path(zip_path)
    if input_path.is_dir():
        print_with_timestamp(f"Loading folder: {input_path}")
        raw_file_list = sorted(
            path for path in input_path.rglob("*")
            if path.is_file() and path.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp")
        )
        image_streams = ((path, path.open("rb")) for path in raw_file_list)
    else:
        print_with_timestamp(f"Loading Zip: {input_path}")
        archive = zipfile.ZipFile(input_path, "r")
        raw_file_list = filter_image_file_list(archive)
        image_streams = ((file_path, archive.open(file_path)) for file_path in raw_file_list)

    try:
        total_files = len(raw_file_list)
        
        # Calculate how many animation frames exist per emotion slot
        variant_count = len(variant_names)
        frames_per_emotion = math.ceil(total_files / variant_count)
        print_with_timestamp(f"Found {total_files} files. Splitting into {variant_count} variants with {frames_per_emotion} frames each.")

        # Read files and slice them into sequential animation blocks
        emotion_blocks = {}
        for idx, (file_path, file_stream) in enumerate(image_streams):
            print_with_timestamp(f"File Got: {file_path}")
            with file_stream:
                img = Image.open(io.BytesIO(file_stream.read())).convert("RGBA")
                img = process_image(img, config)
                
                # Determine which block this sequence index belongs to
                block_idx = idx // frames_per_emotion
                name = variant_names[block_idx]
                if name not in emotion_blocks:
                    emotion_blocks[name] = []
                emotion_blocks[name].append(img)
        return apply_frame_order(
            emotion_blocks,
            config.get("frame_order"),
            config.get("duplicate_last_frame", False)
        )
    finally:
        if not input_path.is_dir():
            archive.close()

def filter_image_file_list(archive):
    raw_file_list = []
    for file_path in archive.namelist():
        if "__MACOSX" in file_path or file_path.endswith("/"):
            continue
        file_name = os.path.basename(file_path)
        if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")) and not file_name.startswith("."):
            raw_file_list.append(file_path)

    if not raw_file_list:
        print_error("No valid images found in the ZIP archive.")
        return

    raw_file_list.sort()
    return raw_file_list

if __name__ == "__main__":
    main()