from pathlib import Path

from animated_spritesheet import count_image_files, create_omori_animated_spritesheet
from gif_maker import spritesheet_to_row_gifs, spritesheet_to_single_gif
from image_utils import load_config, select_config
from interactive_config import build_interactive_config
from printutil import print_error, print_info

def read_path(prompt):
    return input(prompt).strip().strip('"').strip("'")

def default_output_path(input_path):
    path = Path(input_path)
    if path.is_file():
        return path.with_suffix(".png")
    return path.parent / f"{path.name}.png"

def process_once(config_path):
    print("Choose action:")
    print("  1. Create a spritesheet")
    print("  2. Convert a spritesheet to GIF")
    action = read_path("Choose action [1]: ") or "1"
    if action == "2":
        process_gif_once()
        return
    if action != "1":
        print_error("Choose 1 or 2.")
        return

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

    if config.get("_guided_setup"):
        running_settings = config["_running_settings"]
        image_count = count_image_files(input_path)
        if image_count == 0:
            print_error("No valid images found in the input.")
            return
        config = build_interactive_config(image_count)
        config.update(running_settings)

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


def process_gif_once():
    sheet_path = read_path("Enter spritesheet path: ")
    if not Path(sheet_path).is_file():
        print_error(f"Spritesheet not found at {sheet_path}.")
        return

    columns = read_positive_integer("Number of columns [4]: ", 4)
    rows = read_positive_integer("Number of rows [6]: ", 6)
    duration = read_positive_integer("Frame duration in milliseconds [250]: ", 250)
    stack_frames = read_path("Stack previous transparent frames? [y/N]: ").lower()
    dispose_mode = 1 if stack_frames in ("y", "yes") else 2

    print("GIF export mode:")
    print("  1. One combined GIF")
    print("  2. One GIF per row")
    mode = read_path("Choose export mode [1]: ") or "1"
    output_prefix = str(Path(sheet_path).with_suffix(""))

    try:
        if mode == "1":
            max_frames = read_positive_integer("Number of frames [4]: ", 4)
            output_path = f"{output_prefix}_animation.gif"
            spritesheet_to_single_gif(
                sheet_path,
                output_path,
                columns,
                rows,
                max_frames,
                duration,
                dispose_mode,
            )
        elif mode == "2":
            spritesheet_to_row_gifs(
                sheet_path, output_prefix, columns, rows, duration, dispose_mode
            )
        else:
            print_error("Choose 1 or 2.")
    except (OSError, ValueError) as error:
        print_error(f"Could not convert spritesheet: {error}")


def read_positive_integer(prompt, default):
    while True:
        value = read_path(prompt)
        if not value:
            return default
        try:
            number = int(value)
        except ValueError:
            print_error("Enter a whole number.")
            continue
        if number > 0:
            return number
        print_error("Enter a number greater than zero.")


def main():
    config_path = "config.json"
    while True:
        process_once(config_path)
        should_exit = read_path("Exit the program? [y/N]: ").lower()
        if should_exit in ("y", "yes"):
            break

if __name__ == "__main__":
    main()