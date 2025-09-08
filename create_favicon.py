"""
Favicon generator for QA Brother app
This creates a favicon from the QualiAI logo for use in Streamlit
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_favicon_from_image(input_image_path):
    """Create favicon from an existing image (like the QualiAI logo)"""
    if not os.path.exists(input_image_path):
        print(f"Image not found: {input_image_path}")
        return create_favicon()  # Fallback to generated favicon
    
    try:
        # Open and process the original image
        original = Image.open(input_image_path)
        
        # Convert to RGBA if needed
        if original.mode != 'RGBA':
            original = original.convert('RGBA')
        
        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(static_dir, exist_ok=True)
        
        # Create multiple sizes
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
        images = []
        
        for size in sizes:
            # Resize with high quality resampling
            resized = original.resize(size, Image.Resampling.LANCZOS)
            
            # Save individual size
            size_path = os.path.join(static_dir, f"favicon_{size[0]}x{size[1]}.png")
            resized.save(size_path, 'PNG')
            images.append(resized)
        
        # Save main favicon (32x32)
        main_favicon = os.path.join(static_dir, "favicon.png")
        images[1].save(main_favicon, 'PNG')  # Use 32x32 as main
        
        # Create ICO file
        try:
            ico_path = os.path.join(static_dir, "favicon.ico")
            images[0].save(ico_path, format='ICO', 
                         sizes=[(img.size[0], img.size[1]) for img in images])
            print(f"Created favicon.ico from {input_image_path}")
        except Exception as e:
            print(f"ICO creation failed: {e}")
        
        print(f"Favicon created from {input_image_path}")
        return main_favicon
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return create_favicon()  # Fallback to generated favicon

def create_favicon():
    """Create a QA-themed favicon"""
    # Create static directory if it doesn't exist
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    
    # Create multiple sizes for different use cases
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    
    for size in sizes:
        # Create a new image with transparency
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Create a circular background with gradient colors (teal/green theme)
        center = (size[0] // 2, size[1] // 2)
        radius = min(size) // 2 - 2
        
        # Draw circle background
        draw.ellipse([center[0] - radius, center[1] - radius, 
                     center[0] + radius, center[1] + radius], 
                    fill=(64, 224, 208, 255))  # Turquoise color
        
        # Draw "Q" in the center
        try:
            # Try to use a system font
            font_size = max(size[0] // 3, 8)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position to center it
            bbox = draw.textbbox((0, 0), "Q", font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = center[0] - text_width // 2
            y = center[1] - text_height // 2
            
            # Draw the "Q" text
            draw.text((x, y), "Q", fill=(33, 37, 41, 255), font=font)  # Dark text
        except Exception as e:
            print(f"Font rendering error: {e}, using simple drawing")
            # Fallback: draw a simple Q-like shape
            draw.arc([center[0] - radius//2, center[1] - radius//2,
                     center[0] + radius//2, center[1] + radius//2],
                    0, 270, fill=(33, 37, 41, 255), width=2)
        
        # Save as PNG
        png_path = os.path.join(static_dir, f"favicon_{size[0]}x{size[1]}.png")
        img.save(png_path, 'PNG')
    
    # Save the 32x32 as the main favicon
    main_favicon = os.path.join(static_dir, "favicon.png")
    if os.path.exists(os.path.join(static_dir, "favicon_32x32.png")):
        os.rename(os.path.join(static_dir, "favicon_32x32.png"), main_favicon)
    
    # Also create an ICO file for traditional favicon support
    try:
        # Load all sizes and create ICO
        images = []
        for size in sizes:
            img_path = os.path.join(static_dir, f"favicon_{size[0]}x{size[1]}.png")
            if os.path.exists(img_path):
                images.append(Image.open(img_path))
        
        if images:
            ico_path = os.path.join(static_dir, "favicon.ico")
            images[0].save(ico_path, format='ICO', sizes=[(img.size[0], img.size[1]) for img in images])
            print(f"Created favicon.ico with {len(images)} sizes")
    except Exception as e:
        print(f"ICO creation failed: {e}")
    
    return main_favicon

if __name__ == "__main__":
    # Check for command line arguments to use custom logo
    import sys
    
    if len(sys.argv) > 1:
        # Use custom image provided as argument
        custom_logo_path = sys.argv[1]
        print(f"Using custom logo: {custom_logo_path}")
        favicon_path = create_favicon_from_image(custom_logo_path)
    else:
        # Generate default favicon
        print("Generating default Q logo favicon...")
        favicon_path = create_favicon()
    
    print(f"Favicon created at: {favicon_path}")
    print("\nUsage options:")
    print("1. Default: python create_favicon.py")
    print("2. Custom logo: python create_favicon.py path/to/your/logo.png")
    print("3. Replace static/favicon.png manually with your QualiAI logo")
    print("\nThe favicon will automatically appear in the Streamlit app!")
