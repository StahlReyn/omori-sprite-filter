import json
import math
from pathlib import Path

from PIL import Image, ImageFilter


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def select_config(config_data):
    if "presets" not in config_data:
        return config_data

    presets = config_data["presets"]
    if not presets:
        raise ValueError("No config presets found.")

    preset_names = list(presets)
    default_preset = config_data.get("default_preset", preset_names[0])
    if default_preset not in presets:
        default_preset = preset_names[0]

    print("Available config presets:")
    for index, preset_name in enumerate(preset_names, start=1):
        suffix = " (default)" if preset_name == default_preset else ""
        print(f"  {index}. {preset_name}{suffix}")

    while True:
        choice = input(f"Choose a config preset [{default_preset}]: ").strip()
        if choice == "":
            return presets[default_preset]
        if choice.isdigit() and 1 <= int(choice) <= len(preset_names):
            return presets[preset_names[int(choice) - 1]]
        if choice in presets:
            return presets[choice]
        print("Invalid preset. Enter its number or name.")


def resize_and_sharpen(img, settings):
    if not settings.get("enabled", True):
        return img

    scale = float(settings.get("scale", 0.5))
    if scale <= 0:
        raise ValueError("resize settings scale must be greater than zero.")

    resampling_name = settings.get("resampling", "bilinear").lower()
    resampling_filters = {
        "nearest": Image.Resampling.NEAREST,
        "bilinear": Image.Resampling.BILINEAR,
        "bicubic": Image.Resampling.BICUBIC,
        "lanczos": Image.Resampling.LANCZOS,
    }
    if resampling_name not in resampling_filters:
        raise ValueError(f"Unsupported resize resampling filter: {resampling_name}")

    resized = img.resize(
        (max(1, round(img.width * scale)), max(1, round(img.height * scale))),
        resampling_filters[resampling_name]
    )
    return sharpen_image(resized, settings.get("sharpen"))


def sharpen_image(img, settings):
    if not isinstance(settings, dict) or not settings.get("enabled", True):
        return img

    return img.filter(ImageFilter.UnsharpMask(
        radius=float(settings.get("radius", 1)),
        percent=int(settings.get("percent", 50)),
        threshold=int(settings.get("threshold", 0))
    ))


def process_image(img, config):
    crop = config.get("crop")
    if isinstance(crop, dict):
        img = img.crop((crop["left"], crop["top"], crop["right"], crop["bottom"]))

    resize = config.get("resize")
    if isinstance(resize, dict):
        img = img.resize(
            (int(resize["width"]), int(resize["height"])),
            get_resampling_filter(config.get("resampling", "lanczos"))
        )
        return sharpen_image(img, config.get("sharpen"))

    resize_settings = config.get("resize_settings")
    if isinstance(resize_settings, dict):
        return resize_and_sharpen(img, resize_settings)

    return sharpen_image(img, config.get("sharpen"))


def get_resampling_filter(name):
    filters = {
        "nearest": Image.Resampling.NEAREST,
        "bilinear": Image.Resampling.BILINEAR,
        "bicubic": Image.Resampling.BICUBIC,
        "lanczos": Image.Resampling.LANCZOS,
    }
    name = name.lower()
    if name not in filters:
        raise ValueError(f"Unsupported resize resampling filter: {name}")
    return filters[name]


def create_grid_sheet(images, columns, output_name):
    if not images:
        raise ValueError("No images to stitch.")

    if not columns:
        columns = math.ceil(math.sqrt(len(images)))
    rows = math.ceil(len(images) / columns)
    cell_width = max(image.width for image in images)
    cell_height = max(image.height for image in images)
    sheet = Image.new("RGBA", (columns * cell_width, rows * cell_height), (0, 0, 0, 0))

    for index, image in enumerate(images):
        col_idx = index % columns
        row_idx = index // columns
        x = col_idx * cell_width + ((cell_width - image.width) // 2)
        y = row_idx * cell_height + ((cell_height - image.height) // 2)
        sheet.paste(image, (x, y), image)

    sheet.save(output_name, "PNG")
    return columns, rows, cell_width, cell_height
