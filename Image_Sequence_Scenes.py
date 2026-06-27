import json
import numpy as np
from moviepy import ImageClip, AudioFileClip, ColorClip, CompositeVideoClip, concatenate_videoclips, CompositeAudioClip
from PIL import Image, ImageDraw, ImageFilter

def Image_sequence_generation(scene_durations: list) -> None:

    """
    Entry point for generating image sequences for historical photo scenes.

    Args:
        scene_durations: List of dicts, each containing:
            - scene         : scene number / ID
            - duration_seconds : clip duration for that scene
            - aspect_ratio  : "4:3" | "9:16" | None  (as selected by the user)
    """
    print(f"[Image_sequence_generation] Starting for {len(scene_durations)} scene(s).")
    for entry in scene_durations:
        scene_id      = entry.get("scene")
        duration      = entry.get("duration_seconds")
        aspect_ratio  = entry.get("aspect_ratio")
        print(f"  → Scene {scene_id} | Duration: {duration}s | Aspect: {aspect_ratio}")

        #set it off
        video_sequence_gen(scene_id, duration, aspect_ratio)

    

# Load image list
with open('Text_Files\historical_selections.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

sfx_file = "SFX\click.mp3"
canvas_size = (1080, 1920)  # vertical reel


def apply_rounded_corners(pil_img, radius=40):
    """Apply rounded corners to a PIL image"""
    # Convert to RGBA if needed
    if pil_img.mode != 'RGBA':
        pil_img = pil_img.convert('RGBA')
    
    # Create mask with rounded corners
    mask = Image.new('L', pil_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, *pil_img.size), radius=radius, fill=255)
    
    # Apply mask
    result = Image.new('RGBA', pil_img.size, (0, 0, 0, 0))
    result.paste(pil_img, mask=mask)
    
    return result



def apply_rounded_corners(pil_img, radius=40):
    """Apply rounded corners to a PIL image"""
    if pil_img.mode != 'RGBA':
        pil_img = pil_img.convert('RGBA')
    
    mask = Image.new('L', pil_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, *pil_img.size), radius=radius, fill=255)
    
    result = Image.new('RGBA', pil_img.size, (0, 0, 0, 0))
    result.paste(pil_img, mask=mask)
    
    return result



def add_rounded_blurred_border(pil_img, border_width=8, border_color=(0, 0, 0), 
                                 blur_radius=3, corner_radius=40):
    """Add a rounded border with blur effect"""
    if pil_img.mode != 'RGBA':
        pil_img = pil_img.convert('RGBA')
    
    # Create larger canvas for border
    new_size = (pil_img.width + border_width * 2, 
                pil_img.height + border_width * 2)
    
    # Create border background with rounded corners
    border_bg = Image.new('RGBA', new_size, (0, 0, 0, 0))
    
    # Create rounded rectangle mask for border
    mask = Image.new('L', new_size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, *new_size), 
                          radius=corner_radius + border_width, 
                          fill=120)
    
    # Apply blur to the mask for soft edges
    mask = mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    # Create colored border
    border_layer = Image.new('RGBA', new_size, border_color + (255,))
    border_layer.putalpha(mask)
    
    # Paste the original image on top
    result = Image.new('RGBA', new_size, (0, 0, 0, 0))
    result.paste(border_layer, (0, 0), border_layer)
    result.paste(pil_img, (border_width, border_width), pil_img)
    
    return result

def video_sequence_gen(scene_ID, duration, aspect_ratio):
    clips = []
    imgs_file = [images for images in data[str(scene_ID)]["selected_images"]]
    print("TOTAL IMAGES", len(imgs_file), enumerate(imgs_file))

    for i, img in enumerate(imgs_file):
        img_duration = int(duration)/len(imgs_file)

        HEIGHT = 0
        WIDTH = 0

        # Load and process image with PIL
        pil_img = Image.open(img)

        if aspect_ratio == "4:3":
            HEIGHT = 786
            WIDTH = 1024
        elif aspect_ratio == "9:16":
            HEIGHT = 1664
            WIDTH = 938
        
        # Resize to cover 1024x786 OR 720x1280
        if pil_img.width > pil_img.height:
            new_height = HEIGHT
            new_width = int(pil_img.width * (HEIGHT / pil_img.height))
        else:
            new_width = WIDTH
            new_height = int(pil_img.height * (WIDTH / pil_img.width))
        
        pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Center crop to 1024x786 OR 720x1280
        left = (new_width - WIDTH) // 2
        top = (new_height - HEIGHT) // 2
        pil_img = pil_img.crop((left, top, left + WIDTH, top + HEIGHT))
        
        # Apply rounded corners to PIL image BEFORE converting to MoviePy
        pil_img = apply_rounded_corners(pil_img, radius=40)

        # Add rounded blurred border
        pil_img = add_rounded_blurred_border(
            pil_img, 
            border_width=14,           # Thickness of border
            border_color=(50, 50, 50), # Dark gray border
            blur_radius=18,            # Blur amount (higher = more blur)
            corner_radius=40          # Must match rounded corner radius
        )
        
        
        # Convert PIL Image to numpy array for MoviePy
        img_array = np.array(pil_img)
        img_clip = ImageClip(img_array).with_duration(img_duration)

        # Place on canvas (transparent corners will blend with white background)
        bg = ColorClip(size=canvas_size, color=(255, 255, 255), duration=img_duration)
        clip = CompositeVideoClip([bg, img_clip.with_position("center")])

        # Add SFX (all except first)
        if i < len(imgs_file) - 1:
            sfx = AudioFileClip(sfx_file).with_volume_scaled(0.6)
            sfx = sfx.with_start(img_duration)
            clip = clip.with_audio(CompositeAudioClip([sfx]))

        clips.append(clip)

    # Concatenate and export
    video = concatenate_videoclips(clips, method="compose")
    video.write_videofile(f"VIDEO\{scene_ID}_sequence.mp4", fps=24)