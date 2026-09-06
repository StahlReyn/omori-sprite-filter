import os

from PIL import Image

from image_utils import create_grid_sheet, load_config, process_image, select_config


VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")


def create_sprite_sheet(config):
    folder_path = config.get("folder_path", ".")
    output_name = config.get("output_name", "spritesheet.png")
    image_files = sorted(
        file_name for file_name in os.listdir(folder_path)
        if file_name.lower().endswith(VALID_EXTENSIONS)
    )

    if not image_files:
        print("No valid images found.")
        return

    processed_images = []
    for file_name in image_files:
        with Image.open(os.path.join(folder_path, file_name)) as image:
            processed_images.append(process_image(image.convert("RGBA"), config))

    columns, rows, cell_width, cell_height = create_grid_sheet(
        processed_images,
        config.get("columns"),
        output_name
    )
    for image in processed_images:
        image.close()

    print(f"Generated {output_name} ({columns}x{rows} grid, Cell size: {cell_width}x{cell_height})")


def create_sprite_sheet_from_config(config_path="config.json"):
    create_sprite_sheet(select_config(load_config(config_path)))


if __name__ == "__main__":
    create_sprite_sheet_from_config()
