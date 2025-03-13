import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

class Template:
    def __init__(self, name, description, overlay=None):
        self.name = name
        self.description = description
        self.overlay = overlay

class InstagramTemplates:
    @staticmethod
    def get_templates():
        """Return list of available templates"""
        return [
            Template(
                "minimal",
                "Clean design with subtle border",
                lambda img: InstagramTemplates._apply_minimal(img)
            ),
            Template(
                "gradient",
                "Modern gradient background",
                lambda img: InstagramTemplates._apply_gradient(img)
            ),
            Template(
                "polaroid",
                "Classic Polaroid style",
                lambda img: InstagramTemplates._apply_polaroid(img)
            ),
            Template(
                "magazine",
                "Editorial magazine layout",
                lambda img: InstagramTemplates._apply_magazine(img)
            )
        ]

    @staticmethod
    def _apply_minimal(image):
        """Apply minimal template with clean border"""
        # Convert to PIL Image if needed
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Create new image with padding
        border = 40
        new_size = (1080, 1080)
        template = Image.new('RGB', new_size, 'white')
        
        # Calculate resize maintaining aspect ratio
        img_w, img_h = image.size
        aspect = img_w / img_h
        if aspect > 1:
            new_w = new_size[0] - (2 * border)
            new_h = int(new_w / aspect)
        else:
            new_h = new_size[1] - (2 * border)
            new_w = int(new_h * aspect)
            
        # Resize image
        image = image.resize((new_w, new_h), Image.LANCZOS)
        
        # Paste image
        x = (new_size[0] - new_w) // 2
        y = (new_size[1] - new_h) // 2
        template.paste(image, (x, y))
        
        return cv2.cvtColor(np.array(template), cv2.COLOR_RGB2BGR)

    @staticmethod
    def _apply_gradient(image):
        """Apply gradient background template"""
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Create gradient background
        gradient = Image.new('RGB', (1080, 1080))
        draw = ImageDraw.Draw(gradient)
        for y in range(1080):
            r = int(255 * (1 - y/1080))
            g = int(200 * (1 - y/1080))
            b = int(255 * (y/1080))
            draw.line([(0, y), (1080, y)], fill=(r, g, b))
        
        # Resize and center image
        img_w, img_h = image.size
        aspect = img_w / img_h
        if aspect > 1:
            new_w = 900
            new_h = int(new_w / aspect)
        else:
            new_h = 900
            new_w = int(new_h * aspect)
            
        image = image.resize((new_w, new_h), Image.LANCZOS)
        x = (1080 - new_w) // 2
        y = (1080 - new_h) // 2
        gradient.paste(image, (x, y))
        
        return cv2.cvtColor(np.array(gradient), cv2.COLOR_RGB2BGR)

    @staticmethod
    def _apply_polaroid(image):
        """Apply Polaroid-style template"""
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Create white background
        template = Image.new('RGB', (1080, 1080), 'white')
        
        # Calculate Polaroid dimensions
        frame_width = 60
        bottom_height = 120
        max_photo_size = 900
        
        # Resize image maintaining aspect ratio
        img_w, img_h = image.size
        aspect = img_w / img_h
        if aspect > 1:
            new_w = max_photo_size
            new_h = int(new_w / aspect)
        else:
            new_h = max_photo_size
            new_w = int(new_h * aspect)
            
        image = image.resize((new_w, new_h), Image.LANCZOS)
        
        # Create Polaroid frame
        frame_w = new_w + (2 * frame_width)
        frame_h = new_h + (2 * frame_width) + bottom_height
        frame = Image.new('RGB', (frame_w, frame_h), 'white')
        
        # Add shadow
        shadow = Image.new('RGBA', (frame_w + 20, frame_h + 20), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rectangle([10, 10, frame_w + 10, frame_h + 10], fill=(0, 0, 0, 50))
        template.paste(shadow, ((1080 - frame_w) // 2 - 5, (1080 - frame_h) // 2 - 5), shadow)
        
        # Paste image onto frame
        frame.paste(image, (frame_width, frame_width))
        
        # Paste frame onto template
        template.paste(frame, ((1080 - frame_w) // 2, (1080 - frame_h) // 2))
        
        return cv2.cvtColor(np.array(template), cv2.COLOR_RGB2BGR)

    @staticmethod
    def _apply_magazine(image):
        """Apply magazine-style template"""
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Create template
        template = Image.new('RGB', (1080, 1080), 'black')
        draw = ImageDraw.Draw(template)
        
        # Add geometric elements
        draw.rectangle([40, 40, 1040, 1040], outline='white', width=2)
        draw.line([40, 120, 1040, 120], fill='white', width=2)
        
        # Resize and position image
        img_w, img_h = image.size
        aspect = img_w / img_h
        if aspect > 1:
            new_w = 960
            new_h = int(new_w / aspect)
        else:
            new_h = 880
            new_w = int(new_h * aspect)
            
        image = image.resize((new_w, new_h), Image.LANCZOS)
        x = (1080 - new_w) // 2
        y = 160
        template.paste(image, (x, y))
        
        return cv2.cvtColor(np.array(template), cv2.COLOR_RGB2BGR)

def apply_template(image_bytes, template_name):
    """Apply selected template to image"""
    # Convert bytes to image
    image = Image.open(io.BytesIO(image_bytes))
    
    # Find template
    templates = {t.name: t for t in InstagramTemplates.get_templates()}
    template = templates.get(template_name)
    
    if template and template.overlay:
        # Apply template overlay
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        processed = template.overlay(cv_image)
        
        # Convert back to PIL Image
        result = Image.fromarray(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
        
        # Convert to bytes
        output = io.BytesIO()
        result.save(output, format='PNG', quality=100)
        return output.getvalue()
        
    return image_bytes
