# omori-sprite-filter
Automates creating consistent spritesheet from individual image frames

## Configuration

Add presets to `config.json` under `presets`. The program lists animated and portrait
presets when it starts; choose one by number or name, or press Enter to use
`default_preset`.

The existing flat config format is still supported and is treated as one default preset.

When the program runs, input paths can be pasted or dragged into the console. Quotation
marks added by Windows are removed automatically. Press Enter for the default output path.

Each preset can optionally include `resize_settings`. Resizing is enabled by default in
the sample config: images are scaled to half size with bilinear resampling, then lightly
sharpened. Set `enabled` to `false` to keep the source size, or adjust `scale`,
`resampling`, and the `sharpen` settings.

Portrait presets use `type: "portrait"` and support a folder, crop, fixed resize,
sharpening, and column count. They are processed without animated-sprite effects such
as glow, frame reuse, or emotion rows.
