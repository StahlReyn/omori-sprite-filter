from PIL import Image

def _validate_grid(cols, rows, duration):
    if cols < 1 or rows < 1:
        raise ValueError("Grid columns and rows must be positive.")
    if duration < 1:
        raise ValueError("Frame duration must be positive.")


def _grid_size(sheet, cols, rows):
    _validate_grid(cols, rows, 1)
    frame_width = sheet.width // cols
    frame_height = sheet.height // rows
    if frame_width < 1 or frame_height < 1:
        raise ValueError("Grid is larger than the spritesheet.")
    return frame_width, frame_height


def _crop_row(sheet, row, cols, rows):
    frame_width, frame_height = _grid_size(sheet, cols, rows)
    return [
        sheet.crop((col * frame_width, row * frame_height,
                    (col + 1) * frame_width, (row + 1) * frame_height))
        for col in range(cols)
    ]


def _save_gif(frames, output_path, duration, dispose_mode):
    if not frames:
        return False
    try:
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            disposal=dispose_mode,
            loop=0,
        )
    finally:
        for frame in frames:
            frame.close()
    return True


def spritesheet_to_single_gif(sheet_path, output_gif_path, cols=4, rows=6, max_frames=4, duration=250, dispose_mode=2):
    """Export the first max_frames cells in row-major order as one looping GIF."""
    _validate_grid(cols, rows, duration)
    if max_frames < 1:
        raise ValueError("Maximum frame count must be positive.")

    with Image.open(sheet_path) as sheet:
        frames = []
        for row in range(rows):
            row_frames = _crop_row(sheet, row, cols, rows)
            remaining = max_frames - len(frames)
            frames.extend(row_frames[:remaining])
            for frame in row_frames[remaining:]:
                frame.close()
            if len(frames) >= max_frames:
                break

    if _save_gif(frames, output_gif_path, duration, dispose_mode):
        print(f"Saved combined GIF: {output_gif_path} ({len(frames)} frames)")
        return output_gif_path
    raise ValueError("No frames could be extracted.")


def spritesheet_to_row_gifs(sheet_path, output_prefix, cols=4, rows=6, duration=250, dispose_mode=2):
    """Export one looping GIF per spritesheet row."""
    _validate_grid(cols, rows, duration)
    output_paths = []
    with Image.open(sheet_path) as sheet:
        _grid_size(sheet, cols, rows)
        for row in range(rows):
            frames = _crop_row(sheet, row, cols, rows)
            row_output_path = f"{output_prefix}_row_{row}.gif"
            if _save_gif(frames, row_output_path, duration, dispose_mode):
                print(f"Saved row {row} GIF: {row_output_path}")
                output_paths.append(row_output_path)
    return output_paths
