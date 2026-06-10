from pathlib import Path

from filters import create_krita_random_pick_glow
from printutil import print_error, print_with_timestamp

# This script creates sprite sheet and effect from individual image files
# This script is intended to replicate OMORI's enemy sprite sheet
# The standard final output are 4 columns and 6 rows, 
# Each row have different effects:
# - Row 1: Normal
# - Row 2: Hurt (Desaturate)
# - Row 3: Defeated (Desaturate + Invert color)
# - Row 4: Sad (Blue Glow)
# - Row 5: Angry (Red Glow)
# - Row 6: Happy (Yellow Glow)

def main():
    create_folder_structure()
    sprite_path = "input/sprite.png"
    output_path = "output/noisy_glow_sprite.png"
    
    if not Path(sprite_path).is_file():
        print_error(f"Sprite image not found at {sprite_path}. Please place your sprite image there.")
        return
    
    result_image = create_krita_random_pick_glow(sprite_path)
    result_image.save(output_path)
    print_with_timestamp(f"Noisy glow sprite saved to {output_path}")

def create_folder_structure():
    Path("input").mkdir(parents=True, exist_ok=True)
    Path("output").mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    main()