import os
import io
import zipfile

from PIL import Image

from image_utils import create_grid_sheet, process_image


VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")


def create_sprite_sheet(folder_path, output_name, config):
    input_path = os.fspath(folder_path)
    if os.path.isdir(input_path):
        image_sources = [
            (file_name, os.path.join(input_path, file_name))
            for file_name in sorted(os.listdir(input_path))
            if file_name.lower().endswith(VALID_EXTENSIONS)
        ]
    else:
        with zipfile.ZipFile(input_path, "r") as archive:
            image_sources = [
                (file_name, archive.read(file_name))
                for file_name in sorted(archive.namelist())
                if not file_name.endswith("/")
                and "__MACOSX" not in file_name
                and file_name.lower().endswith(VALID_EXTENSIONS)
            ]

    if not image_sources:
        print("No valid images found.")
        return

    processed_images = []
    for file_name, source in image_sources:
        image_data = io.BytesIO(source) if isinstance(source, bytes) else source
        with Image.open(image_data) as image:
            processed_images.append(process_image(image.convert("RGBA"), config))

    columns, rows, cell_width, cell_height = create_grid_sheet(
        processed_images,
        config.get("columns"),
        output_name
    )
    for image in processed_images:
        image.close()

    print(f"Generated {output_name} ({columns}x{rows} grid, Cell size: {cell_width}x{cell_height})")


if __name__ == "__main__":
    print("Run main.py to select a portrait preset and provide input/output paths.")
