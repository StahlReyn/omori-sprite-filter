import numpy as np
from PIL import Image, ImageFilter

def random_pick(image, pick_radius):
    """
    Applies 'Random Pick' filter, 
    mimicking Krita's behavior of shuffling pixels with their local neighbors.
    """
    # Convert glow to NumPy array for the "Random Pick" calculation
    glow_arr = np.array(image)
    height, width, channels = glow_arr.shape
    
    # Generate random coordinate offsets for every pixel position
    # Generates shifts like -3, -2, -1, 0, 1, 2, 3 based on your pick_radius
    dy = np.random.randint(-pick_radius, pick_radius + 1, size=(height, width))
    dx = np.random.randint(-pick_radius, pick_radius + 1, size=(height, width))
    
    # Create a grid of current coordinates
    y_indices, x_indices = np.indices((height, width))
    
    # Apply the random shifts to build target coordinates
    pick_y = y_indices + dy
    pick_x = x_indices + dx
    
    # Clamp target coordinates inside boundaries to prevent out-of-bounds errors
    pick_y = np.clip(pick_y, 0, height - 1)
    pick_x = np.clip(pick_x, 0, width - 1)
    
    # "Randomly Pick" and map the neighbor pixels into their new locations
    random_picked_arr = glow_arr[pick_y, pick_x]
    
    # Convert back to Pillow Image
    return Image.fromarray(random_picked_arr, "RGBA")

def random_pick_glow(
        sprite, 
        glow_color=(255, 255, 255), 
        blur_radius=3, 
        expand_size=5, 
        pick_radius=2
    ):
    """
    Applies a glow to a sprite and subjects the glow layer to a 'Random Pick' filter
    """
    #  Expand alpha silhouette
    alpha = sprite.split()[3]
    mask = alpha.filter(ImageFilter.MaxFilter(expand_size * 2 + 1))
    
    # Create the soft base glow
    glow = Image.new("RGBA", sprite.size, glow_color + (0,))
    glow.putalpha(mask)
    if blur_radius > 0:
        glow = glow.filter(ImageFilter.GaussianBlur(blur_radius))

    noisy_glow = random_pick(glow, pick_radius)
    
    # Layer original sprite on top of glow
    final_image = Image.new("RGBA", sprite.size)
    final_image.paste(noisy_glow, (0, 0))
    final_image.paste(sprite, (0, 0), sprite)
    
    return final_image
