document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const pdfInput = document.getElementById('pdfInput');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = uploadProgress.querySelector('.progress-bar');
    const imageList = document.getElementById('imageList');

    uploadArea.addEventListener('click', () => pdfInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('border-primary');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('border-primary');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('border-primary');
        
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'application/pdf') {
            handleFile(file);
        } else {
            alert('Please upload a PDF file');
        }
    });

    pdfInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFile(file);
        }
    });

    function handleFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        uploadProgress.classList.remove('d-none');
        progressBar.style.width = '0%';

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            displayImages(data.images);
            uploadProgress.classList.add('d-none');
        })
        .catch(error => {
            alert(error.message || 'Error uploading file');
            uploadProgress.classList.add('d-none');
        });
    }

    function displayImages(images) {
        imageList.innerHTML = '';
        images.forEach((image, index) => {
            const col = document.createElement('div');
            col.className = 'col-md-4 mb-4';
            col.innerHTML = `
                <div class="card">
                    <img src="data:image/png;base64,${image.data}" 
                         class="card-img-top thumbnail" 
                         data-image="${image.data}"
                         alt="Page ${index + 1}">
                    <div class="card-body">
                        <h5 class="card-title">Page ${index + 1}</h5>
                        <button class="btn btn-primary edit-btn">Edit</button>
                    </div>
                </div>
            `;
            imageList.appendChild(col);

            col.querySelector('.edit-btn').addEventListener('click', () => {
                document.getElementById('imageEditor').classList.remove('d-none');
                initializeEditor(image.data);
            });
        });
    }
});
