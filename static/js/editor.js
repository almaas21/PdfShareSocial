let canvas;
let currentImage;
let originalImageData;
let processedImageData;
let cropMode = false;
let cropRect = null;

function initializeEditor(imageData) {
    const canvasContainer = document.getElementById('canvas').parentElement;
    const containerWidth = canvasContainer.offsetWidth;

    // Store original image data
    originalImageData = imageData;
    processedImageData = imageData; // Initialize with original image

    // Initialize Fabric.js canvas
    canvas = new fabric.Canvas('canvas', {
        width: containerWidth,
        height: containerWidth,
    });

    // Load image
    fabric.Image.fromURL(`data:image/png;base64,${imageData}`, function(img) {
        currentImage = img;
        img.scaleToWidth(canvas.width);
        canvas.add(img);
        canvas.centerObject(img);
        canvas.renderAll();
    });

    // Initialize controls
    initializeControls();
}

function initializeControls() {
    const brightness = document.getElementById('brightness');
    const contrast = document.getElementById('contrast');
    const grayscaleBtn = document.getElementById('grayscaleBtn');
    const enhanceBtn = document.getElementById('enhanceBtn');
    const cropBtn = document.getElementById('cropBtn');
    const templateSelect = document.getElementById('templateSelect');
    const downloadBtn = document.getElementById('downloadBtn');

    let operations = {
        brightness: 1,
        contrast: 1,
        grayscale: false,
        enhance: false,
        template: '',
        crop: null
    };

    function updateImage() {
        if (!currentImage) return;

        // Show loading state
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';

        // If we're in crop mode and have a crop rectangle, calculate crop coordinates
        if (cropRect && cropMode) {
            const scale = currentImage.scaleX;
            operations.crop = {
                left: cropRect.left / scale,
                top: cropRect.top / scale,
                width: cropRect.width * cropRect.scaleX / scale,
                height: cropRect.height * cropRect.scaleY / scale
            };
        }

        fetch('/process_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image: `data:image/png;base64,${originalImageData}`,
                operations: operations
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            // Store the processed image data
            processedImageData = data.processed_image;

            // Update canvas with new image
            fabric.Image.fromURL(`data:image/png;base64,${data.processed_image}`, function(img) {
                canvas.clear();
                img.scaleToWidth(canvas.width);
                canvas.add(img);
                canvas.centerObject(img);
                canvas.renderAll();
                currentImage = img;

                // Reset download button
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>Download';
            });
        })
        .catch(error => {
            alert(error.message || 'Error processing image');
            // Reset download button on error
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>Download';
        });
    }

    brightness.addEventListener('change', function() {
        operations.brightness = parseFloat(this.value);
        updateImage();
    });

    contrast.addEventListener('change', function() {
        operations.contrast = parseFloat(this.value);
        updateImage();
    });

    grayscaleBtn.addEventListener('click', function() {
        operations.grayscale = !operations.grayscale;
        this.classList.toggle('btn-primary');
        updateImage();
    });

    enhanceBtn.addEventListener('click', function() {
        operations.enhance = !operations.enhance;
        this.classList.toggle('btn-primary');
        updateImage();
    });

    templateSelect.addEventListener('change', function() {
        operations.template = this.value;
        updateImage();
    });

    cropBtn.addEventListener('click', function() {
        if (!cropMode) {
            // Enter crop mode
            cropMode = true;
            this.innerHTML = '<i class="fas fa-check me-2"></i>Apply Crop';
            this.classList.add('btn-primary');

            // Create crop rectangle
            const rect = new fabric.Rect({
                left: canvas.width / 4,
                top: canvas.height / 4,
                width: canvas.width / 2,
                height: canvas.height / 2,
                fill: 'rgba(0,0,0,0.3)',
                stroke: '#fff',
                strokeWidth: 2,
                strokeDashArray: [5, 5]
            });

            cropRect = rect;
            canvas.add(rect);
            canvas.setActiveObject(rect);
            rect.bringToFront();
        } else {
            // Apply crop
            cropMode = false;
            this.innerHTML = '<i class="fas fa-crop me-2"></i>Crop';
            this.classList.remove('btn-primary');

            if (cropRect) {
                canvas.remove(cropRect);
                updateImage();
                cropRect = null;
            }
        }
    });

    downloadBtn.addEventListener('click', function() {
        if (!processedImageData) {
            alert('Please wait for image processing to complete');
            return;
        }

        try {
            const link = document.createElement('a');
            link.download = 'instagram-image.png';
            link.href = `data:image/png;base64,${processedImageData}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Download error:', error);
            alert('Error downloading the image. Please try again.');
        }
    });
}