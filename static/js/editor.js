let canvas;
let currentImage;
let originalImageData;
let processedImageData;
let isDrawing = false;
let cropPolygon = null;

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
        selection: false // Disable group selection
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

    let points = [];
    let lines = [];
    let cropMode = false;

    function updateImage() {
        if (!currentImage) return;

        // Show loading state
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';

        // If we have a crop polygon, calculate crop coordinates
        if (cropPolygon) {
            const scale = currentImage.scaleX;
            operations.crop = {
                points: cropPolygon.points.map(point => ({
                    x: point.x / scale,
                    y: point.y / scale
                }))
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

    function enableCropMode() {
        cropMode = true;
        points = [];
        lines = [];
        if (cropPolygon) {
            canvas.remove(cropPolygon);
            cropPolygon = null;
        }

        canvas.on('mouse:down', startDrawing);
        canvas.on('mouse:move', draw);
        canvas.on('mouse:up', stopDrawing);

        cropBtn.innerHTML = '<i class="fas fa-check me-2"></i>Apply Crop';
        cropBtn.classList.add('btn-primary');
    }

    function disableCropMode() {
        cropMode = false;
        canvas.off('mouse:down', startDrawing);
        canvas.off('mouse:move', draw);
        canvas.off('mouse:up', stopDrawing);

        cropBtn.innerHTML = '<i class="fas fa-crop me-2"></i>Crop';
        cropBtn.classList.remove('btn-primary');

        updateImage();
    }

    function startDrawing(event) {
        isDrawing = true;
        const pointer = canvas.getPointer(event.e);
        points.push({ x: pointer.x, y: pointer.y });

        // Start new polygon
        if (points.length === 1) {
            cropPolygon = new fabric.Polygon(points, {
                fill: 'rgba(0,0,0,0.3)',
                stroke: '#fff',
                strokeWidth: 2,
                selectable: false
            });
            canvas.add(cropPolygon);
        }
    }

    function draw(event) {
        if (!isDrawing) return;

        const pointer = canvas.getPointer(event.e);
        points.push({ x: pointer.x, y: pointer.y });

        if (cropPolygon) {
            cropPolygon.set({ points: points });
            canvas.renderAll();
        }
    }

    function stopDrawing() {
        isDrawing = false;
        if (points.length > 2) {
            // Close the polygon
            points.push(points[0]);
            if (cropPolygon) {
                cropPolygon.set({ points: points });
                canvas.renderAll();
            }
        }
    }

    cropBtn.addEventListener('click', function() {
        if (!cropMode) {
            enableCropMode();
        } else {
            disableCropMode();
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