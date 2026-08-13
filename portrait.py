import os
import json
import math
from PIL import Image, ImageFilter

def load_config(config_path="config.json"):
    with open(config_path, "r") as f:
        return json.load(f)

def process_image(img, config):
    # Step 1: Crop (Optional)
    if "crop" in config and config["crop"]:
        c = config["crop"]
        img = img.crop((c["left"], c["top"], c["right"], c["bottom"]))

    # Step 2: Resize (Optional)
    if "resize" in config and config["resize"]:
        r = config["resize"]
        img = img.resize((r["width"], r["height"]), Image.Resampling.LANCZOS)

    # Step 3: Sharpen with specific parameters (Optional)
    sharpen_config = config.get("sharpen")
    if isinstance(sharpen_config, dict):
        # Extract user parameters or fallback to mild defaults if keys are missing
        radius = sharpen_config.get("radius", 1)
        percent = sharpen_config.get("percent", 50)
        threshold = sharpen_config.get("threshold", 3)
        
        img = img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))
        
    return img

def create_sprite_sheet_from_config(config_path="config.json"):
    cfg = load_config(config_path)
    folder_path = cfg.get("folder_path", ".")
    output_name = cfg.get("output_name", "spritesheet.png")
    columns = cfg.get("columns")

    valid_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
    image_files = sorted([
        f for f in os.listdir(folder_path) 
        if f.lower().endswith(valid_exts)
    ])
    
    if not image_files:
        print("No valid images found.")
        return

    processed_images = []
    for file_name in image_files:
        full_path = os.path.join(folder_path, file_name)
        with Image.open(full_path) as img:
            proc_img = process_image(img.convert("RGBA"), cfg)
            processed_images.append(proc_img)

    cell_width = max(i.width for i in processed_images)
    cell_height = max(i.height for i in processed_images)
    num_images = len(processed_images)

    if not columns:
        columns = math.ceil(math.sqrt(num_images))
    rows = math.ceil(num_images / columns)

    sheet_width = columns * cell_width
    sheet_height = rows * cell_height
    sprite_sheet = Image.new("RGBA", (sheet_width, sheet_height), (0, 0, 0, 0))

    for index, img in enumerate(processed_images):
        col_idx = index % columns
        row_idx = index // columns
        
        x = col_idx * cell_width + ((cell_width - img.width) // 2)
        y = row_idx * cell_height + ((cell_height - img.height) // 2)
        
        sprite_sheet.paste(img, (x, y), img)
        img.close()

    sprite_sheet.save(output_name)
    print(f"Generated {output_name} ({columns}x{rows} grid, Cell size: {cell_width}x{cell_height})")

if __name__ == "__main__":
    create_sprite_sheet_from_config("omori-sprite-filter/config_portrait.json")
