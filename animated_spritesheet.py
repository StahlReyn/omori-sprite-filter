import io
import math
import os
import zipfile

from pathlib import Path
from PIL import Image, ImageEnhance

from filters import apply_desat, apply_invert, apply_random_pick_glow, apply_channel_multiplier
from image_utils import process_image
from printutil import print_error, print_with_timestamp


VALID_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")


def count_image_files(input_path):
    input_path = Path(input_path)
    if input_path.is_dir():
        return sum(
            path.is_file()
            and not path.name.startswith(".")
            and path.suffix.lower() in VALID_IMAGE_EXTENSIONS
            for path in input_path.rglob("*")
        )

    with zipfile.ZipFile(input_path, "r") as archive:
        return len(filter_image_file_list(archive))


def create_omori_animated_spritesheet(input_path, output_path, config, export_single_frame=False):
    variant_names = config["variant_names"]
    lighten_hurt = config["lighten_hurt"]
    invert_defeat = config["invert_defeat"]
    row_reuse = config["row_reuse"]
    glow_settings = config["glow_settings"]

    emotion_blocks = grab_emotion_blocks(input_path, variant_names, config)

    neutral_source = row_name_convert("neutral", row_reuse)
    frames_per_emotion = max(len(block) for block in emotion_blocks.values())
    frame_size = emotion_blocks[neutral_source][0].size

    for block in emotion_blocks.values():
        while len(block) < frames_per_emotion:
            block.append(block[-1] if block else Image.new("RGBA", frame_size, (0, 0, 0, 0)))

    hurt_row = []
    for index, frame in enumerate(emotion_blocks[row_name_convert("hurt", row_reuse)]):
        print_with_timestamp("Process Hurt Effect")
        image = apply_desat(frame)
        if lighten_hurt and index % 2 == 0:
            image = ImageEnhance.Brightness(image).enhance(1.2)
        hurt_row.append(image)

    defeat_row = []
    for frame in emotion_blocks[row_name_convert("defeat", row_reuse)]:
        print_with_timestamp("Process Defeat Effect")
        image = apply_desat(frame)
        if invert_defeat:
            image = apply_invert(image)
        defeat_row.append(image)

    glow_colors = config["glow_colors"]
    sad_color = tuple(glow_colors["sad"])
    angry_color = tuple(glow_colors["angry"])
    happy_color = tuple(glow_colors["happy"])

    sprite_matrix = [
        emotion_blocks[neutral_source],
        hurt_row,
        defeat_row,
        [apply_glow_config(frame, sad_color, glow_settings) for frame in emotion_blocks[row_name_convert("sad", row_reuse)]],
        [apply_glow_config(frame, angry_color, glow_settings) for frame in emotion_blocks[row_name_convert("angry", row_reuse)]],
        [apply_glow_config(frame, happy_color, glow_settings) for frame in emotion_blocks[row_name_convert("happy", row_reuse)]],
    ]

    sprite_width, sprite_height = frame_size
    sheet_width = frames_per_emotion * sprite_width
    sheet_height = 6 * sprite_height
    spritesheet = Image.new("RGBA", (sheet_width, sheet_height), (0, 0, 0, 0))

    for row_index, row_images in enumerate(sprite_matrix):
        for column_index, image in enumerate(row_images):
            print_with_timestamp(f"Pasting ({row_index}, {column_index})")
            if image.size != (sprite_width, sprite_height):
                image = image.resize((sprite_width, sprite_height), Image.Resampling.LANCZOS)

            x = column_index * sprite_width
            y = row_index * sprite_height
            spritesheet.paste(image, (x, y), image)

    spritesheet.save(output_path, "PNG")
    print_with_timestamp(f"Finished! Generated a {frames_per_emotion}x6 grid layout saved to {output_path}.")

    if export_single_frame:
        single_output_path = Path(output_path).with_name(f"{Path(output_path).stem}_single.png")
        single_frame = spritesheet.crop((0, 0, sprite_width, sprite_height))
        single_frame.save(single_output_path, "PNG")
        single_frame.close()
        print_with_timestamp(f"Saved first frame to {single_output_path}.")


def apply_glow_config(image, glow_color, setting):
    if "multiply_strength" in setting:
        strength = float(setting["multiply_strength"])
        if strength != 0:
            print_with_timestamp(f"Process Tint {glow_color}")
            image = apply_channel_multiplier(image, glow_color, strength / 255)

    print_with_timestamp(f"Process Glow {glow_color}")
    return apply_random_pick_glow(
        img=image,
        glow_color=glow_color,
        blur_radius=setting["blur_radius"],
        expand_size=setting["expand_size"],
        pick_radius=setting["pick_radius"],
    )


def row_name_convert(base_name, row_reuse):
    new_block_name = row_reuse.get(base_name)
    if new_block_name:
        print_with_timestamp(f"Using {new_block_name} for {base_name}.")
        return new_block_name
    return base_name


def apply_frame_order(emotion_blocks, frame_order=None, duplicate_last_frame=False):
    if frame_order is None:
        ordered_blocks = emotion_blocks
    elif not frame_order:
        raise ValueError("frame_order must contain at least one frame index.")
    else:
        ordered_blocks = {}
        for name, frames in emotion_blocks.items():
            if any(not isinstance(index, int) or index < 0 or index >= len(frames) for index in frame_order):
                raise ValueError(f"frame_order contains an invalid index for {name}.")
            ordered_blocks[name] = [frames[index] for index in frame_order]

    if duplicate_last_frame:
        for frames in ordered_blocks.values():
            if not frames:
                raise ValueError("Cannot duplicate the final frame of an empty block.")
            frames.append(frames[-1])
    return ordered_blocks


def grab_emotion_blocks(input_name, variant_names, config):
    input_path = Path(input_name)
    if input_path.is_dir():
        print_with_timestamp(f"Loading folder: {input_path}")
        raw_file_list = sorted(
            path for path in input_path.rglob("*")
            if path.is_file()
            and not path.name.startswith(".")
            and path.suffix.lower() in VALID_IMAGE_EXTENSIONS
        )
        image_streams = ((path, path.open("rb")) for path in raw_file_list)
    else:
        print_with_timestamp(f"Loading Zip: {input_path}")
        archive = zipfile.ZipFile(input_path, "r")
        raw_file_list = filter_image_file_list(archive)
        image_streams = ((file_path, archive.open(file_path)) for file_path in raw_file_list)

    try:
        total_files = len(raw_file_list)
        if total_files == 0:
            raise ValueError("No valid images found in the input.")

        variant_count = len(variant_names)
        if variant_count > total_files:
            raise ValueError("There must be at least one image for every configured source row.")
        frames_per_emotion = math.ceil(total_files / variant_count)
        print_with_timestamp(
            f"Found {total_files} files. Splitting into {variant_count} variants "
            f"with {frames_per_emotion} frames each."
        )

        emotion_blocks = {}
        for index, (file_path, file_stream) in enumerate(image_streams):
            print_with_timestamp(f"File Got: {file_path}")
            with file_stream:
                image = Image.open(io.BytesIO(file_stream.read())).convert("RGBA")
                image = process_image(image, config)

                block_index = min(index * variant_count // total_files, variant_count - 1)
                name = variant_names[block_index]
                emotion_blocks.setdefault(name, []).append(image)

        return apply_frame_order(
            emotion_blocks,
            config.get("frame_order"),
            config.get("duplicate_last_frame", False),
        )
    finally:
        if not input_path.is_dir():
            archive.close()


def filter_image_file_list(archive):
    raw_file_list = []
    for file_path in archive.namelist():
        if "__MACOSX" in file_path or file_path.endswith("/"):
            continue
        file_name = os.path.basename(file_path)
        if file_name.lower().endswith(VALID_IMAGE_EXTENSIONS) and not file_name.startswith("."):
            raw_file_list.append(file_path)

    if not raw_file_list:
        print_error("No valid images found in the ZIP archive.")

    return sorted(raw_file_list)