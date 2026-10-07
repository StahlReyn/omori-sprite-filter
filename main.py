from pathlib import Path

from image_utils import load_config, select_config
from printutil import print_error, print_info
from animated_spritesheet import create_omori_animated_spritesheet

def read_path(prompt):
    return input(prompt).strip().strip('"').strip("'")

def default_output_path(input_path):
    path = Path(input_path)
    if path.is_file():
        return path.with_suffix(".png")
    return path.parent / f"{path.name}.png"

def process_once(config_path):
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
        single_frame = read_path("Also export the first frame as a separate image? [y/N]: ").lower()
        create_omori_animated_spritesheet(
            input_path,
            output_path,
            config,
            export_single_frame=single_frame in ("y", "yes")
        )

def main():
    config_path = "config.json"
    if not Path(config_path).is_file():
        print_error("config.json not found. Create it before running the program.")
        return

    while True:
        process_once(config_path)
        should_exit = read_path("Exit the program? [y/N]: ").lower()
        if should_exit in ("y", "yes"):
            break

if __name__ == "__main__":
    main()