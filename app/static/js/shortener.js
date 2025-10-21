// Main shortener functionality
let selectedSlug = null;
let currentUrl = null;

const urlInput = document.getElementById('url-input');
const generateBtn = document.getElementById('generate-btn');
const progressSection = document.getElementById('progress-section');
const statusMessage = document.getElementById('status-message');
const optionsSection = document.getElementById('options-section');
const slugOptionsContainer = document.getElementById('slug-options');
const createBtn = document.getElementById('create-btn');
const resultSection = document.getElementById('result-section');
const shortUrlResult = document.getElementById('short-url-result');
const originalUrl = document.getElementById('original-url');
const copyBtn = document.getElementById('copy-btn');
const createAnotherBtn = document.getElementById('create-another');

// Generate slug options
generateBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();

    if (!url) {
        alert('Please enter a URL');
        return;
    }

    // Validate URL format
    try {
        new URL(url);
    } catch (e) {
        alert('Please enter a valid URL');
        return;
    }

    currentUrl = url;
    selectedSlug = null;

    // Reset and show progress
    progressSection.classList.remove('hidden');
    optionsSection.classList.add('hidden');
    resultSection.classList.add('hidden');
    generateBtn.disabled = true;

    // Create EventSource for Server-Sent Events
    const eventSource = new EventSource('/api/generate-slugs?' + new URLSearchParams({
        url: url
    }));

    // Note: We're using GET with query params for SSE compatibility
    // Let's update to use POST with proper SSE
    eventSource.close(); // Close the GET attempt

    // Use fetch with streaming for POST
    try {
        const response = await fetch('/api/generate-slugs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    handleUpdate(data);
                }
            }
        }
    } catch (error) {
        statusMessage.textContent = 'Error: ' + error.message;
        generateBtn.disabled = false;
    }
});

function handleUpdate(data) {
    if (data.status === 'progress') {
        statusMessage.textContent = data.message;
        statusMessage.classList.remove('error');
        progressSection.classList.remove('error-card');
    } else if (data.status === 'success') {
        statusMessage.textContent = data.message;
        displaySlugOptions(data.slugs);
        progressSection.classList.add('hidden');
        optionsSection.classList.remove('hidden');
        generateBtn.disabled = false;
    } else if (data.status === 'error') {
        showError(data.message);
        generateBtn.disabled = false;
    }
}

function showError(message) {
    // Add error styling
    statusMessage.classList.add('error');
    progressSection.classList.add('error-card');

    // Create better error message with icon
    const errorHtml = `
        <div style="text-align: center;">
            <div class="error-icon">⚠️</div>
            <div class="error-title">Oops! Something went wrong</div>
            <div class="error-message">${message}</div>
            <div class="error-actions">
                <button type="button" onclick="retryGeneration()" class="btn-secondary">Try Again</button>
            </div>
        </div>
    `;

    progressSection.innerHTML = errorHtml;
}

function retryGeneration() {
    progressSection.innerHTML = '<div class="progress-messages"><p id="status-message">Processing...</p></div>';
    progressSection.classList.remove('error-card');
    progressSection.classList.add('hidden');
    generateBtn.click();
}

function displaySlugOptions(slugs) {
    slugOptionsContainer.innerHTML = '';

    slugs.forEach((slug, index) => {
        const option = document.createElement('div');
        option.className = 'slug-option';
        option.innerHTML = `
            <input type="radio" name="slug" id="slug-${index}" value="${slug}">
            <label for="slug-${index}">${slug}</label>
        `;

        option.addEventListener('click', () => {
            document.querySelectorAll('.slug-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            option.classList.add('selected');
            document.getElementById(`slug-${index}`).checked = true;
            selectedSlug = slug;
            createBtn.classList.remove('hidden');
        });

        slugOptionsContainer.appendChild(option);
    });
}

// Create short URL
createBtn.addEventListener('click', async () => {
    if (!selectedSlug) {
        alert('Please select a slug option');
        return;
    }

    createBtn.disabled = true;

    try {
        const response = await fetch('/api/create-short-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: currentUrl,
                slug: selectedSlug
            })
        });

        const data = await response.json();

        if (data.success) {
            shortUrlResult.value = data.short_url;
            originalUrl.textContent = data.original_url;
            optionsSection.classList.add('hidden');
            resultSection.classList.remove('hidden');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error creating short URL: ' + error.message);
    } finally {
        createBtn.disabled = false;
    }
});

// Copy to clipboard
copyBtn.addEventListener('click', async () => {
    try {
        await navigator.clipboard.writeText(shortUrlResult.value);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyBtn.textContent = 'Copy';
        }, 2000);
    } catch (err) {
        // Fallback for older browsers
        shortUrlResult.select();
        document.execCommand('copy');
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyBtn.textContent = 'Copy';
        }, 2000);
    }
});

// Create another
createAnotherBtn.addEventListener('click', () => {
    urlInput.value = '';
    currentUrl = null;
    selectedSlug = null;
    resultSection.classList.add('hidden');
    urlInput.focus();
});