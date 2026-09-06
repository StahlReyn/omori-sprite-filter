import json
import math
from copy import deepcopy

from PIL import Image, ImageFilter


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def select_config(config_data):
    if "presets" not in config_data:
        return config_data

    presets = config_data["presets"]
    templates = config_data.get("templates", {})
    if not presets:
        raise ValueError("No config presets found.")

    preset_names = list(presets)
    default_preset = config_data.get("default_preset", preset_names[0])
    if default_preset not in presets:
        default_preset = preset_names[0]

    print("Available config presets:")
    for index, preset_name in enumerate(preset_names, start=1):
        suffix = " (default)" if preset_name == default_preset else ""
        description = presets[preset_name].get("description", "")
        description = f" - {description}" if description else ""
        print(f"  {index}. {preset_name}{suffix}{description}")
    print("=" * 32)

    while True:
        choice = input(f"Choose a config preset [{default_preset}]: ").strip()
        if choice == "":
            return resolve_preset(default_preset, presets, templates)
        if choice.isdigit() and 1 <= int(choice) <= len(preset_names):
            return resolve_preset(preset_names[int(choice) - 1], presets, templates)
        if choice in presets:
            return resolve_preset(choice, presets, templates)
        print("Invalid preset. Enter its number or name.")


def resolve_preset(preset_name, presets, templates, inheritance_chain=None):
    inheritance_chain = inheritance_chain or []
    if preset_name in inheritance_chain:
        chain = " -> ".join(inheritance_chain + [preset_name])
        raise ValueError(f"Circular preset inheritance: {chain}")

    preset = presets[preset_name]
    parent_name = preset.get("$extends")
    if parent_name is None:
        resolved = {}
    else:
        if parent_name not in presets:
            raise ValueError(f"Unknown parent preset: {parent_name}")
        resolved = resolve_preset(parent_name, presets, templates, inheritance_chain + [preset_name])

    overrides = {key: value for key, value in preset.items() if key != "$extends"}
    return merge_config(resolved, resolve_templates(overrides, templates))


def resolve_templates(value, templates):
    if isinstance(value, dict):
        if "$template" in value:
            template_name = value["$template"]
            if template_name not in templates:
                raise ValueError(f"Unknown config template: {template_name}")
            resolved = deepcopy(templates[template_name])
            overrides = {key: item for key, item in value.items() if key != "$template"}
            return merge_config(resolved, resolve_templates(overrides, templates))
        return {key: resolve_templates(item, templates) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_templates(item, templates) for item in value]
    return value


def merge_config(base, overrides):
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge_config(base[key], value)
        else:
            base[key] = value
    return base


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

    resize = config.get("resize", config.get("resize_settings"))
    if isinstance(resize, dict):
        if resize.get("enabled", True):
            if "width" in resize and "height" in resize:
                size = (int(resize["width"]), int(resize["height"]))
            else:
                scale = float(resize.get("scale", 0.5))
                if scale <= 0:
                    raise ValueError("resize scale must be greater than zero.")
                size = (
                    max(1, round(img.width * scale)),
                    max(1, round(img.height * scale))
                )
            img = img.resize(size, get_resampling_filter(resize.get("resampling", "lanczos")))
        return sharpen_image(img, resize.get("sharpen", config.get("sharpen")))

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
