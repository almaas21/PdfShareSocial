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

def detect_document_edges(image):
    """
    Detect document edges in the image and return both corners and visualization
    """
    # Make a copy for visualization
    vis_image = image.copy()

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply Gaussian blur
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # Detect edges
    edges = cv2.Canny(blur, 75, 200)
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    corners = None
    if contours:
        # Get the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        # Approximate the contour to get corners
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        corners = cv2.approxPolyDP(largest_contour, epsilon, True)

        if len(corners) == 4:
            corners = corners.reshape(4, 2)
            # Draw corners and boundaries on visualization image
            cv2.drawContours(vis_image, [corners.reshape(-1,1,2)], -1, (0,255,0), 3)
            for corner in corners:
                cv2.circle(vis_image, tuple(corner), 10, (0,0,255), -1)

            return corners, vis_image

    return None, vis_image

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

    # Apply perspective correction with high-quality interpolation
    return cv2.warpPerspective(image, matrix, (width, height), flags=cv2.INTER_LANCZOS4)

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

    # Detect document edges and apply perspective correction if requested
    if operations.get('perspective_correction'):
        corners, vis_image = detect_document_edges(cv_image)
        if corners is not None:
            # Return visualization if corners detected
            cv_image = vis_image if operations.get('show_boundaries') else apply_perspective_correction(cv_image, corners)

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
    image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

    # Convert to bytes with maximum quality
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG', optimize=False, quality=100)
    return img_byte_arr.getvalue()