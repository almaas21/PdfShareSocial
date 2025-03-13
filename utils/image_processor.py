import cv2
import numpy as np
from PIL import Image
import io

def enhance_image(image):
    """
    Enhance image using adaptive histogram equalization
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge((l,a,b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def adjust_brightness_contrast(image, brightness=1.0, contrast=1.0):
    """
    Adjust image brightness and contrast
    """
    return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)

def convert_to_instagram_size(image):
    """
    Convert image to Instagram-compatible size (1080x1080)
    """
    return cv2.resize(image, (1080, 1080), interpolation=cv2.INTER_LANCZOS4)

def process_image(image_bytes, operations=None):
    """
    Process image with given operations
    """
    if operations is None:
        operations = {}
    
    # Convert bytes to image
    image = Image.open(io.BytesIO(image_bytes))
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Apply operations
    if operations.get('brightness') or operations.get('contrast'):
        cv_image = adjust_brightness_contrast(
            cv_image,
            brightness=operations.get('brightness', 1.0),
            contrast=operations.get('contrast', 1.0)
        )
    
    if operations.get('enhance'):
        cv_image = enhance_image(cv_image)
    
    if operations.get('grayscale'):
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2BGR)
    
    # Ensure Instagram size
    cv_image = convert_to_instagram_size(cv_image)
    
    # Convert back to PIL Image
    image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
