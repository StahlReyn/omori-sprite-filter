import json
import math
import textwrap
from copy import deepcopy

from PIL import Image, ImageFilter


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def select_config(config_data, image_count=None):
    if "presets" not in config_data:
        return config_data

    presets = config_data["presets"]
    templates = config_data.get("templates", {})
    custom_options = config_data.get("custom_options", {})
    if not presets:
        raise ValueError("No config presets found.")
    if not isinstance(custom_options, dict):
        raise ValueError("custom_options must be a mapping of setting names to option lists.")

    preset_names = list(presets)
    default_preset = config_data.get("default_preset", preset_names[0])
    if default_preset not in presets:
        default_preset = preset_names[0]

    if image_count is not None:
        print(f"Input images found: {image_count}")

    preset_offset = 1
    if custom_options:
        print("\n--- CUSTOM ---")
        print(f"  1. Custom settings based on {default_preset}")
        preset_offset = 2
    print("\n--- PRESETS ---")
    for index, preset_name in enumerate(preset_names, start=preset_offset):
        suffix = " (default)" if preset_name == default_preset else ""
        description = presets[preset_name].get("description", "")
        description = f" - {description}" if description else ""
        print(f"  {index}. {preset_name}{suffix}{description}")
    print("=" * 32)

    while True:
        choice = input(f"Choose a configuration [{default_preset}]: ").strip()
        if choice == "":
            return resolve_preset(default_preset, presets, templates)
        if custom_options and (choice == "1" or choice.lower() == "custom"):
            config = resolve_preset(default_preset, presets, templates)
            return apply_custom_options(config, custom_options, templates)
        if choice.isdigit():
            preset_index = int(choice) - preset_offset
            if 0 <= preset_index < len(preset_names):
                return resolve_preset(preset_names[preset_index], presets, templates)
        if choice in presets:
            return resolve_preset(choice, presets, templates)
        print("Invalid choice. Enter a number or preset name.")


def apply_custom_options(config, custom_options, templates=None):
    templates = templates or {}
    for setting_name, options in custom_options.items():
        if not isinstance(options, list) or not options:
            raise ValueError(f"custom_options.{setting_name} must be a non-empty list.")

        label = setting_name.replace("_", " ").title()
        print(f"\n--- {label.upper()} ---")
        current_value = config.get(setting_name)
        print_custom_value("  Current: ", current_value)

        if setting_name == "frames_per_variant":
            print(f"  Available values: {', '.join(str(option) for option in options)}")
            while True:
                choice = input(f"  Frames per variant [{current_value}]: ").strip()
                if choice == "":
                    break
                if choice.isdigit() and int(choice) in options:
                    config[setting_name] = int(choice)
                    break
                print("  Enter one of the available frame counts or press Enter to keep the current value.")
            continue

        if setting_name == "invert_defeat":
            print("  Options: y/yes, n/no")
            while True:
                default = "Y/n" if current_value else "y/N"
                choice = input(f"  Invert defeat? [{default}]: ").strip().lower()
                if choice == "":
                    break
                if choice in ("y", "yes") and True in options:
                    config[setting_name] = True
                    break
                if choice in ("n", "no") and False in options:
                    config[setting_name] = False
                    break
                print("  Enter y or n, or press Enter to keep the current value.")
            continue

        available_options = []
        for option in options:
            if isinstance(option, dict) and "value" in option:
                option_value = option["value"]
            else:
                option_value = option
            available_options.append(resolve_templates(deepcopy(option_value), templates))

        for index, option_value in enumerate(available_options, start=1):
            print_custom_value(f"  {index}. ", option_value)

        while True:
            choice = input(f"  Choose {label.lower()} [Enter to keep current]: ").strip()
            if choice == "":
                break
            if choice.isdigit() and 1 <= int(choice) <= len(available_options):
                config[setting_name] = deepcopy(available_options[int(choice) - 1])
                break
            print("  Invalid choice. Enter one of the listed numbers or press Enter.")

    return config


def print_custom_value(prefix, value, width=88):
    serialized = json.dumps(value, ensure_ascii=False)
    available_width = max(24, width - len(prefix))
    lines = textwrap.wrap(
        serialized,
        width=available_width,
        subsequent_indent=" " * len(prefix),
        break_long_words=True,
        break_on_hyphens=False
    ) or [""]
    print(prefix + lines[0])
    for line in lines[1:]:
        print(line)


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
