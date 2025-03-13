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

def detect_document_edges(image):
    """
    Detect document edges in the image
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply Gaussian blur
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # Detect edges
    edges = cv2.Canny(blur, 75, 200)
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # Get the largest contour
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        # Approximate the contour to get corners
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        corners = cv2.approxPolyDP(largest_contour, epsilon, True)
        if len(corners) == 4:
            return corners.reshape(4, 2)
    return None

def apply_perspective_correction(image, corners):
    """
    Apply perspective correction using detected corners
    """
    if corners is None:
        return image

    # Get image dimensions
    height, width = image.shape[:2]

    # Define target corners (rectangle)
    target_corners = np.float32([[0, 0], [width, 0], [width, height], [0, height]])

    # Sort corners (top-left, top-right, bottom-right, bottom-left)
    corners = corners.astype(np.float32)
    s = corners.sum(axis=1)
    corners_sorted = np.zeros((4, 2), dtype=np.float32)
    corners_sorted[0] = corners[np.argmin(s)]  # Top-left
    corners_sorted[2] = corners[np.argmax(s)]  # Bottom-right
    diff = np.diff(corners, axis=1)
    corners_sorted[1] = corners[np.argmin(diff)]  # Top-right
    corners_sorted[3] = corners[np.argmax(diff)]  # Bottom-left

    # Get perspective transform matrix
    matrix = cv2.getPerspectiveTransform(corners_sorted, target_corners)

    # Apply perspective correction
    return cv2.warpPerspective(image, matrix, (width, height))

def process_image(image_bytes, operations=None):
    """
    Process image with given operations
    """
    if operations is None:
        operations = {}

    # Convert bytes to image
    image = Image.open(io.BytesIO(image_bytes))
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Detect document edges and apply perspective correction if requested
    if operations.get('perspective_correction'):
        corners = detect_document_edges(cv_image)
        if corners is not None:
            cv_image = apply_perspective_correction(cv_image, corners)

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