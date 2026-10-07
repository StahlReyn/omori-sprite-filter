import math


ROW_NAMES = ("hurt", "defeat", "sad", "angry", "happy")


def build_interactive_config(image_count):
    if image_count < 1:
        raise ValueError("At least one image is required for guided configuration.")

    suggested_rows = min(4, image_count)
    default_names = ["neutral", "sad", "angry", "happy"][:suggested_rows]
    print(f"Found {image_count} images. Choose the source emotion rows in file order.")

    while True:
        entered_names = input(
            f"Source row names, comma-separated [{', '.join(default_names)}]: "
        ).strip()
        variant_names = [name.strip() for name in entered_names.split(",")] if entered_names else default_names
        if (
            1 <= len(variant_names) <= image_count
            and all(variant_names)
            and len(set(variant_names)) == len(variant_names)
            and variant_names[0] == "neutral"
        ):
            break
        print(f"Enter 1 to {image_count} unique names, starting with neutral.")

    frames_per_row = math.ceil(image_count / len(variant_names))
    print(f"That gives up to {frames_per_row} frame(s) per source row.")

    row_reuse = {}
    for row_name in ROW_NAMES:
        preferred = _default_source(row_name, variant_names)
        row_reuse[row_name] = _choose_source(row_name, variant_names, preferred)

    return {
        "type": "animated",
        "variant_names": variant_names,
        "row_reuse": row_reuse,
        "lighten_hurt": True,
        "invert_defeat": True,
        "resize": {
            "enabled": True,
            "scale": 0.5,
            "resampling": "bilinear",
            "sharpen": {"enabled": True, "radius": 1, "percent": 25, "threshold": 0},
        },
        "glow_colors": {
            "sad": [0, 100, 255],
            "angry": [255, 0, 50],
            "happy": [255, 220, 0],
        },
        "glow_settings": {
            "blur_radius": 3,
            "expand_size": 7,
            "pick_radius": 2,
            "multiply_strength": 0.1,
        },
    }


def _default_source(row_name, variant_names):
    if row_name in variant_names:
        return row_name
    if row_name in ("hurt", "defeat") and "sad" in variant_names:
        return "sad"
    return variant_names[-1]


def _choose_source(row_name, variant_names, default_name):
    options = ", ".join(
        f"{index}. {name}" for index, name in enumerate(variant_names, start=1)
    )
    default_index = variant_names.index(default_name) + 1
    while True:
        choice = input(
            f"Source row for output '{row_name}' ({options}) [{default_index}]: "
        ).strip()
        if not choice:
            return default_name
        if choice.isdigit() and 1 <= int(choice) <= len(variant_names):
            return variant_names[int(choice) - 1]
        if choice in variant_names:
            return choice
        print("Choose a listed number or row name.")