# OMORI Sprite Filter
Automates creating consistent spritesheet from individual image frames.

## Features

- Choose animated or portrait presets at startup.
- Process multiple images in one run; choose whether to exit after each job.
- Use ZIP archives or folders as input for either mode.
- Drag and drop paths into the console; quoted Windows paths are supported.
- Press Enter at the output prompt to save beside the input with the same name as a PNG.
- Configure crop and a shared resize setting with a decimal scale (`0.5`), fixed dimensions, resampling, and sharpening.
- Omit crop or resize settings to skip those steps.
- Reuse settings with `$template` and inherit complete presets with `$extends`.
- Configure animated frame output order, such as `[0, 1, 2, 1]`.
- Assign source images to named groups with `frames_per_variant` instead of splitting all images evenly.
- Optionally export the processed first neutral frame as `<output>_single.png`.
- Apply animated effects including glow, desaturation, inversion, and frame reuse.
- Stitch portrait images into configurable grids without animated effects.

Configuration is stored in `config.json` under `presets`. Each preset includes a
description and can override only the settings it needs.

The configuration picker offers `Custom` separately from presets. Custom starts
from the default preset and prompts for each setting listed in top-level
`custom_options`; Enter keeps the current value. The input image count appears
before the configuration choices. Frame count is entered directly, booleans use
yes/no, and other settings show stable numbered choices with compact values.

For animated presets, `variant_names` gives the ordered names of source groups.
`frames_per_variant` sets the number of consecutive input images in every group;
the total must match the input image count. For unusual uneven layouts,
`variant_frame_counts` can map names to individual counts instead. These group
names are references used by `row_reuse`, so they do not need to be emotion names.
`row_reuse` can map any output row, including `neutral`, to one of these groups.
When both count settings are omitted, images retain the legacy even-split
behavior. `frame_order` selects and reorders frames within each group; inherited
presets can override it without repeating the other settings.

Resize `scale` uses decimal values such as `0.5`. The `standard_two_frame` and
`standard_three_frame` presets show common frame-order variations.
