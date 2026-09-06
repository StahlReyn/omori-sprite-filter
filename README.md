# OMORI Sprite Filter
Automates creating consistent spritesheet from individual image frames.

## Features

- Choose animated or portrait presets at startup.
- Use ZIP archives or folders as input for either mode.
- Drag and drop paths into the console; quoted Windows paths are supported.
- Press Enter at the output prompt to save beside the input with the same name as a PNG.
- Configure crop and a shared resize setting with scale or fixed dimensions, resampling, and sharpening.
- Omit crop or resize settings to skip those steps.
- Reuse settings with `$template` and inherit complete presets with `$extends`.
- Configure animated frame output order, such as `[0, 1, 2, 1]`.
- Apply animated effects including glow, desaturation, inversion, and frame reuse.
- Stitch portrait images into configurable grids without animated effects.

Configuration is stored in `config.json` under `presets`. Each preset includes a
description and can override only the settings it needs.
