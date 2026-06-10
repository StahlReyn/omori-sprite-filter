import numpy as np
from PIL import Image, ImageFilter

def create_krita_random_pick_glow(
        sprite_path, 
        glow_color=(255, 255, 255), 
        blur_radius=3, 
        expand_size=5, 
        pick_radius=2
    ):
    """
    Applies a glow to a sprite and subjects the glow layer to a 'Random Pick' 
    filter, mimicking Krita's behavior of shuffling pixels with their local neighbors.
    """
    # 1. Load sprite and build the expanded alpha silhouette
    sprite = Image.open(sprite_path).convert("RGBA")
    alpha = sprite.split()[3]
    mask = alpha.filter(ImageFilter.MaxFilter(expand_size * 2 + 1))
    
    # 2. Create the soft base glow
    glow = Image.new("RGBA", sprite.size, glow_color + (0,))
    glow.putalpha(mask)
    if blur_radius > 0:
        glow = glow.filter(ImageFilter.GaussianBlur(blur_radius))
    
    # 3. Convert glow to NumPy array for the "Random Pick" calculation
    glow_arr = np.array(glow)
    height, width, channels = glow_arr.shape
    
    # 4. Generate random coordinate offsets for every pixel position
    # Generates shifts like -3, -2, -1, 0, 1, 2, 3 based on your pick_radius
    dy = np.random.randint(-pick_radius, pick_radius + 1, size=(height, width))
    dx = np.random.randint(-pick_radius, pick_radius + 1, size=(height, width))
    
    # 5. Create a grid of current coordinates
    y_indices, x_indices = np.indices((height, width))
    
    # Apply the random shifts to build target coordinates
    pick_y = y_indices + dy
    pick_x = x_indices + dx
    
    # Clamp target coordinates inside boundaries to prevent out-of-bounds errors
    pick_y = np.clip(pick_y, 0, height - 1)
    pick_x = np.clip(pick_x, 0, width - 1)
    
    # 6. "Randomly Pick" and map the neighbor pixels into their new locations
    random_picked_glow_arr = glow_arr[pick_y, pick_x]
    
    # Convert back to Pillow Image
    noisy_glow = Image.fromarray(random_picked_glow_arr, "RGBA")
    
    # 7. Layer original sprite cleanly over the Krita-style dithered glow
    final_image = Image.new("RGBA", sprite.size)
    final_image.paste(noisy_glow, (0, 0))
    final_image.paste(sprite, (0, 0), sprite)
    
    return final_image
