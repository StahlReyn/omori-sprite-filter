import json
import math
from copy import deepcopy

from PIL import Image, ImageFilter


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def select_config(config_data):
    if "animated_setups" in config_data:
        return select_animated_setup(config_data)

    return select_preset_config(config_data)


def select_preset_config(config_data):
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
            config = resolve_preset(default_preset, presets, templates)
            return configure_animated_options(config, config_data, templates)
        if choice.isdigit() and 1 <= int(choice) <= len(preset_names):
            config = resolve_preset(preset_names[int(choice) - 1], presets, templates)
            return configure_animated_options(config, config_data, templates)
        if choice in presets:
            config = resolve_preset(choice, presets, templates)
            return configure_animated_options(config, config_data, templates)
        print("Invalid preset. Enter its number or name.")


def select_animated_setup(config_data):
    setups = config_data["animated_setups"]
    running_configs = config_data.get("running_configs", {})
    templates = config_data.get("templates", {})
    default_setup = config_data.get("default_setup", next(iter(setups)))
    running_name = config_data.get("default_running_config", next(iter(running_configs), None))
    if default_setup not in setups:
        default_setup = next(iter(setups))
    if running_name not in running_configs:
        running_name = next(iter(running_configs), None)
    setup_names = list(setups)
    default_index = setup_names.index(default_setup) + 1

    while True:
        print("Choose sprite-sheet setup:")
        for index, (name, setup) in enumerate(setups.items(), start=1):
            label = setup.get("label", name)
            description = setup.get("description", "")
            suffix = f" - {description}" if description else ""
            print(f"  {index}. {label}{suffix}")
        running_description = "not set"
        if running_name:
            running_description = running_configs[running_name].get("description", running_name)
        print(f"  R. Running config: {running_description}")
        print("  G. Guided setup from image count")
        if config_data.get("presets"):
            print("  P. Portrait preset")

        choice = input(f"Choose setup [{default_index}]: ").strip().lower()
        if choice == "r":
            running_name = choose_running_config(running_name, running_configs)
            continue
        if choice == "p" and config_data.get("presets"):
            return select_preset_config(config_data)
        if choice == "g":
            return {
                "_guided_setup": True,
                "_running_settings": resolve_running_config(running_name, running_configs, templates),
            }

        if choice.isdigit() and 1 <= int(choice) <= len(setup_names):
            setup_name = setup_names[int(choice) - 1]
        elif choice in setups:
            setup_name = choice
        elif not choice:
            setup_name = default_setup
        else:
            print("Choose a listed setup, R, G, or P.")
            continue

        config = resolve_templates(config_data.get("animated_defaults", {}), templates)
        setup_settings = resolve_templates(setups[setup_name], templates)
        description = setup_settings.pop("description", None)
        setup_settings.pop("label", None)
        prompt_hurt_defeat = setup_settings.pop("prompt_hurt_defeat", False)
        prompt_neutral_reuse = setup_settings.pop("prompt_neutral_reuse", False)
        merge_config(config, setup_settings)
        merge_config(config, resolve_running_config(running_name, running_configs, templates))

        if prompt_neutral_reuse:
            config["row_reuse"]["neutral"] = choose_variant_source(
                "neutral row", config["variant_names"], config["row_reuse"]["neutral"]
            )
        if prompt_hurt_defeat:
            source = choose_variant_source(
                "hurt and defeat", config["variant_names"], config["row_reuse"]["hurt"]
            )
            config["row_reuse"]["hurt"] = source
            config["row_reuse"]["defeat"] = source
        return config


def choose_running_config(default_name, running_configs):
    if not running_configs:
        print("No running configs are defined.")
        return None

    running_names = list(running_configs)
    print("Available running configs:")
    for index, name in enumerate(running_names, start=1):
        description = running_configs[name].get("description", "")
        suffix = f" - {description}" if description else ""
        print(f"  {index}. {name}{suffix}")

    while True:
        choice = input(f"Choose running config [{default_name}]: ").strip()
        if not choice:
            return default_name
        if choice.isdigit() and 1 <= int(choice) <= len(running_names):
            return running_names[int(choice) - 1]
        if choice in running_configs:
            return choice
        print("Choose a listed running config name or number.")


def resolve_running_config(running_name, running_configs, templates):
    if running_name is None:
        return {}
    settings = resolve_templates(running_configs[running_name], templates)
    settings.pop("description", None)
    return settings


def configure_animated_options(config, config_data, templates):
    variant_sets = config_data.get("variant_sets", {})
    variant_set_name = config.pop("variant_set", None)
    if config.get("type") != "animated" or variant_set_name is None:
        return config
    if variant_set_name not in variant_sets:
        raise ValueError(f"Unknown variant set: {variant_set_name}")

    variant_settings = load_variant_settings(variant_set_name, variant_sets, templates)
    merge_config(config, deepcopy(variant_settings))
    print("Animated setup:")
    print("  1. Standard (default)")
    if "neutral_only" in variant_sets:
        print("  2. Neutral only")
    print("  3. Use one source row for hurt and defeat")
    print("  4. Custom row setup")

    while True:
        setup = input("Choose animated setup [1]: ").strip().lower()
        if not setup or setup in ("1", "standard"):
            return config
        if setup in ("2", "neutral", "neutral_only") and "neutral_only" in variant_sets:
            neutral_settings = load_variant_settings("neutral_only", variant_sets, templates)
            merge_config(config, deepcopy(neutral_settings))
            return config
        if setup in ("3", "reuse"):
            source = choose_variant_source(
                "hurt and defeat", config["variant_names"], config["row_reuse"]["hurt"]
            )
            config["row_reuse"]["hurt"] = source
            config["row_reuse"]["defeat"] = source
            return config
        if setup in ("4", "custom"):
            return configure_custom_animated_options(
                config, variant_set_name, variant_sets, templates
            )
        print("Choose 1, 2, 3, or 4.")


def configure_custom_animated_options(config, default_variant_set, variant_sets, templates):
    if variant_sets:
        variant_set_name = choose_variant_set(default_variant_set, variant_sets)
        variant_settings = load_variant_settings(variant_set_name, variant_sets, templates)
        merge_config(config, deepcopy(variant_settings))

    variant_names = config["variant_names"]
    defaults = (config["row_reuse"]["hurt"], config["row_reuse"]["defeat"])
    while True:
        choices = input(
            f"Source rows for hurt and defeat, comma-separated [{defaults[0]},{defaults[1]}]: "
        ).strip()
        if not choices:
            break
        selected = [name.strip() for name in choices.split(",")]
        if len(selected) == 2 and all(name in variant_names for name in selected):
            config["row_reuse"]["hurt"], config["row_reuse"]["defeat"] = selected
            break
        print(f"Enter two listed source names: {', '.join(variant_names)}.")

    inversion_default = config.get("invert_defeat", True)
    inversion_prompt = "[Y/n]" if inversion_default else "[y/N]"
    while True:
        inversion = input(f"Invert the defeat row? {inversion_prompt}: ").strip().lower()
        if inversion in ("", "y", "yes"):
            config["invert_defeat"] = inversion_default if not inversion else True
            break
        if inversion in ("n", "no"):
            config["invert_defeat"] = False
            break
        print("Enter yes or no.")
    return config


def load_variant_settings(variant_set_name, variant_sets, templates):
    settings = resolve_templates(variant_sets[variant_set_name], templates)
    settings.pop("description", None)
    return settings


def choose_variant_set(default_name, variant_sets):
    variant_names = list(variant_sets)
    print("Available variant sets:")
    for index, name in enumerate(variant_names, start=1):
        description = variant_sets[name].get("description", "")
        suffix = f" - {description}" if description else ""
        print(f"  {index}. {name}{suffix}")

    while True:
        choice = input(f"Choose variant set [{default_name}]: ").strip()
        if not choice:
            return default_name
        if choice.isdigit() and 1 <= int(choice) <= len(variant_names):
            return variant_names[int(choice) - 1]
        if choice in variant_sets:
            return choice
        print("Invalid variant set. Enter its number or name.")


def choose_variant_source(row_name, variant_names, default_name):
    options = ", ".join(
        f"{index}. {name}" for index, name in enumerate(variant_names, start=1)
    )
    default_index = variant_names.index(default_name) + 1
    while True:
        choice = input(
            f"Source row for {row_name} ({options}) [{default_index}]: "
        ).strip()
        if not choice:
            return default_name
        if choice.isdigit() and 1 <= int(choice) <= len(variant_names):
            return variant_names[int(choice) - 1]
        if choice in variant_names:
            return choice
        print("Choose a listed number or row name.")


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
