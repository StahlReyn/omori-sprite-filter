# OMORI Sprite Filter
Automates creating consistent spritesheet from individual image frames.

## Features

- Choose animated or portrait presets at startup.
- Convert an existing spritesheet into one looping GIF or one GIF per row from the main menu.
- Choose common animated layouts directly: four emotions, six frames, neutral-only, or three emotions with one reused as neutral.
- Change the running resize config from the setup menu; the default is half-size bilinear.
- Use the guided animated setup to count input images and choose source rows and row reuse without a config file.
- Process multiple images in one run; choose whether to exit after each job.
- Use ZIP archives or folders as input for either mode.
- Drag and drop paths into the console; quoted Windows paths are supported.
- Press Enter at the output prompt to save beside the input with the same name as a PNG.
- Configure crop and a shared resize setting with scale or fixed dimensions, resampling, and sharpening.
- Omit crop or resize settings to skip those steps.
- Reuse settings with `$template` and inherit complete presets with `$extends`.
- Configure animated frame output order, such as `[0, 1, 2, 1]`.
- Optionally export the processed first neutral frame as `<output>_single.png`.
- Apply animated effects including glow, desaturation, inversion, and frame reuse.
- Stitch portrait images into configurable grids without animated effects.

Animated defaults, layouts, and resize choices are configured separately in
`config.json` under `animated_defaults`, `animated_setups`, and `running_configs`.
Portrait options remain under `presets`.

The first menu selects a common animated layout directly. For the three-emotion
layout, choose which input emotion fills neutral and which source feeds hurt and
defeat. Running resize configurations are defined separately under
`running_configs`, with `default_running_config` selecting the startup default.

Choose `G` from the setup menu for guided row configuration based on the image
count in the selected ZIP or folder. It uses the currently selected running
configuration.
