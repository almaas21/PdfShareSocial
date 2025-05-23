import cv2
import numpy as np
from PIL import Image
import io

def enhance_image(image):
    """
    Enhance image using adaptive histogram equalization while maintaining sharpness
    """
    # Split into LAB channels
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Apply CLAHE to L channel with reduced clip limit
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)

    # Apply smart sharpening
    blurred = cv2.GaussianBlur(l, (0, 0), 3)
    sharpened = cv2.addWeighted(l, 1.5, blurred, -0.5, 0)

    # Merge back
    lab = cv2.merge((sharpened, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def adjust_brightness_contrast(image, brightness=1.0, contrast=1.0):
    """
    Adjust image brightness and contrast
    """
    # Apply contrast first
    mean = cv2.mean(image)[0]
    contrast_image = cv2.addWeighted(image, contrast, image, 0, mean * (1 - contrast))

    # Then brightness
    return cv2.convertScaleAbs(contrast_image, alpha=1, beta=(brightness - 1) * 100)

def convert_to_instagram_size(image):
    """
    Convert image to Instagram-compatible size (1080x1080)
    """
    height, width = image.shape[:2]

    # Calculate padding to make it square first
    if height > width:
        diff = height - width
        padding = diff // 2
        image = cv2.copyMakeBorder(image, 0, 0, padding, diff - padding, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    elif width > height:
        diff = width - height
        padding = diff // 2
        image = cv2.copyMakeBorder(image, padding, diff - padding, 0, 0, cv2.BORDER_CONSTANT, value=[255, 255, 255])

    # Only resize if the image is smaller than 1080x1080
    if height < 1080 or width < 1080:
        return cv2.resize(image, (1080, 1080), interpolation=cv2.INTER_LANCZOS4)
    return image

def apply_crop(image, crop):
    """
    Apply selection-based crop, keeping only the selected area
    """
    if not crop or 'points' not in crop:
        return image

    # Create mask from polygon points
    height, width = image.shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    points = np.array([[int(p['x']), int(p['y'])] for p in crop['points']], np.int32)
    points = points.reshape((-1, 1, 2))
    cv2.fillPoly(mask, [points], 255)

    # Create a 4-channel image (BGRA) for transparency
    rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    # Make non-selected areas transparent
    rgba[:, :, 3] = mask

    return rgba

def process_image(image_bytes, operations=None):
    """
    Process image with given operations
    """
    if operations is None:
        operations = {}

    # Convert bytes to image
    image = Image.open(io.BytesIO(image_bytes))
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Store original size
    original_height, original_width = cv_image.shape[:2]

    # Apply crop if specified
    if operations.get('crop'):
        cv_image = apply_crop(cv_image, operations['crop'])

    # Apply other operations
    if operations.get('brightness') or operations.get('contrast'):
        cv_image = adjust_brightness_contrast(
            cv_image,
            brightness=operations.get('brightness', 1.0),
            contrast=operations.get('contrast', 1.0)
        )

    if operations.get('enhance'):
        cv_image = enhance_image(cv_image)

    if operations.get('grayscale'):
        # Direct grayscale conversion without quality loss
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2BGR)

    # Ensure Instagram size with high quality
    if max(original_height, original_width) > 1080:
        cv_image = convert_to_instagram_size(cv_image)

    # Convert back to PIL Image with high quality
    if len(cv_image.shape) == 3 and cv_image.shape[2] == 4:  # RGBA
        image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGRA2RGBA))
    else:  # RGB
        image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

    # Convert to bytes with maximum quality
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG', optimize=False, quality=100)
    return img_byte_arr.getvalue()