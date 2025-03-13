let canvas;
let currentImage;
let originalImageData;

function initializeEditor(imageData) {
    const canvasContainer = document.getElementById('canvas').parentElement;
    const containerWidth = canvasContainer.offsetWidth;

    // Store original image data
    originalImageData = imageData;

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
    const perspectiveBtn = document.getElementById('perspectiveBtn');
    const downloadBtn = document.getElementById('downloadBtn');

    let operations = {
        brightness: 1,
        contrast: 1,
        grayscale: false,
        enhance: false,
        perspective_correction: false,
        show_boundaries: true
    };

    function updateImage() {
        if (!currentImage) return;

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
            fabric.Image.fromURL(`data:image/png;base64,${data.processed_image}`, function(img) {
                canvas.clear();
                img.scaleToWidth(canvas.width);
                canvas.add(img);
                canvas.centerObject(img);
                canvas.renderAll();
                currentImage = img;
            });
        })
        .catch(error => {
            alert(error.message || 'Error processing image');
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

    let perspectiveState = 'off'; // 'off', 'detecting', 'correcting'
    perspectiveBtn.addEventListener('click', function() {
        switch (perspectiveState) {
            case 'off':
                operations.perspective_correction = true;
                operations.show_boundaries = true;
                perspectiveState = 'detecting';
                this.innerHTML = '<i class="fas fa-check me-2"></i>Apply Correction';
                this.classList.add('btn-warning');
                break;
            case 'detecting':
                operations.show_boundaries = false;
                perspectiveState = 'correcting';
                this.innerHTML = '<i class="fas fa-crop-alt me-2"></i>Fix Perspective';
                this.classList.remove('btn-warning');
                this.classList.add('btn-primary');
                break;
            case 'correcting':
                operations.perspective_correction = false;
                operations.show_boundaries = true;
                perspectiveState = 'off';
                this.innerHTML = '<i class="fas fa-crop-alt me-2"></i>Fix Perspective';
                this.classList.remove('btn-primary');
                break;
        }
        updateImage();
    });

    downloadBtn.addEventListener('click', function() {
        if (!currentImage) return;

        const link = document.createElement('a');
        link.download = 'instagram-image.png';
        // Get the current processed image from the canvas
        link.href = canvas.toDataURL({
            format: 'png',
            quality: 1
        });
        link.click();
    });
}