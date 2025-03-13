let canvas;
let currentImage;

function initializeEditor(imageData) {
    const canvasContainer = document.getElementById('canvas').parentElement;
    const containerWidth = canvasContainer.offsetWidth;
    
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
    const downloadBtn = document.getElementById('downloadBtn');

    let operations = {
        brightness: 1,
        contrast: 1,
        grayscale: false,
        enhance: false
    };

    function updateImage() {
        fetch('/process_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image: canvas.toDataURL(),
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

    downloadBtn.addEventListener('click', function() {
        const link = document.createElement('a');
        link.download = 'instagram-image.png';
        link.href = canvas.toDataURL({
            format: 'png',
            quality: 1
        });
        link.click();
    });
}
