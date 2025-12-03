const API_BASE = 'http://localhost:5001/api';

let currentUrl = '';
let selectedSlug = '';
let slugOptions = [];
let authToken = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentUrl = tab.url;

  // Check if user is already logged in
  const storage = await chrome.storage.local.get(['authToken']);
  authToken = storage.authToken;

  if (authToken) {
    // User is logged in, show logout button and skip to shortening process
    document.getElementById('logout-btn').classList.remove('hidden');
    startShorteningProcess();
  } else {
    // Show login screen
    showContainer('login');
  }
});

// Event listeners
document.getElementById('login-btn').addEventListener('click', handleLogin);
document.getElementById('guest-btn').addEventListener('click', () => {
  authToken = null;
  startShorteningProcess();
});
document.getElementById('logout-btn').addEventListener('click', handleLogout);
document.getElementById('create-btn').addEventListener('click', createShortUrl);
document.getElementById('copy-btn').addEventListener('click', copyToClipboard);
document.getElementById('cancel-btn').addEventListener('click', () => window.close());
document.getElementById('retry-btn').addEventListener('click', startShorteningProcess);
document.getElementById('new-btn').addEventListener('click', startShorteningProcess);
document.getElementById('dashboard-btn').addEventListener('click', openDashboard);

// Handle Enter key in login form
document.getElementById('password').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    handleLogin();
  }
});

function showContainer(id) {
  document.querySelectorAll('.container').forEach(el => el.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function showError(message) {
  document.getElementById('error-message').textContent = message;
  showContainer('error');
}

async function startShorteningProcess() {
  showContainer('loading');
  slugOptions = [];
  selectedSlug = '';

  console.log('Starting shortening process for URL:', currentUrl);

  try {
    const response = await fetch(`${API_BASE}/generate-slugs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: currentUrl })
    });

    console.log('Response status:', response.status, response.statusText);

    if (!response.ok) {
      let errorMessage = 'Failed to generate slugs';
      try {
        const error = await response.json();
        errorMessage = error.error || errorMessage;
      } catch (e) {
        // If JSON parsing fails, use the response status text
        errorMessage = response.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6).trim();

          // Skip empty data lines
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);

            // Handle error responses
            if (data.status === 'error' || data.error) {
              throw new Error(data.message || data.error || 'Unknown error occurred');
            }

            // Update status message if present
            if (data.message) {
              document.getElementById('status-text').textContent = data.message;
            }

            // Handle successful slug generation
            if (data.status === 'success' && data.slugs) {
              slugOptions = data.slugs;
              if (slugOptions.length > 0) {
                displaySlugOptions(slugOptions);
                showContainer('slug-selection');
              } else {
                throw new Error('No available slugs generated');
              }
            }
          } catch (parseError) {
            if (parseError.message && !parseError.message.includes('JSON')) {
              // This is an intentional error from our code, rethrow it
              throw parseError;
            }
            console.error('Failed to parse SSE data:', jsonStr, parseError);
            // Continue processing other lines for JSON parse errors
          }
        }
      }
    }
  } catch (error) {
    showError(error.message);
  }
}

function displaySlugOptions(slugs) {
  const container = document.getElementById('slug-options');
  container.innerHTML = '';

  slugs.forEach(slug => {
    const option = document.createElement('div');
    option.className = 'slug-option';
    option.textContent = slug;
    option.addEventListener('click', () => selectSlug(slug, option));
    container.appendChild(option);
  });
}

function selectSlug(slug, element) {
  selectedSlug = slug;
  document.querySelectorAll('.slug-option').forEach(el => el.classList.remove('selected'));
  element.classList.add('selected');
  document.getElementById('create-btn').disabled = false;
}

async function createShortUrl() {
  if (!selectedSlug) return;

  showContainer('loading');
  document.getElementById('status-text').textContent = 'Creating short URL...';

  try {
    const headers = { 'Content-Type': 'application/json' };

    // Add auth token if available
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(`${API_BASE}/create-short-url`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        url: currentUrl,
        slug: selectedSlug
      })
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.error || 'Failed to create short URL');
    }

    document.getElementById('short-url').textContent = data.short_url;
    document.getElementById('original-url').textContent = data.original_url;
    showContainer('result');
  } catch (error) {
    showError(error.message);
  }
}

function copyToClipboard() {
  const shortUrl = document.getElementById('short-url').textContent;
  navigator.clipboard.writeText(shortUrl).then(() => {
    const btn = document.getElementById('copy-btn');
    const originalText = btn.textContent;
    btn.textContent = '✓ Copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = originalText;
      btn.classList.remove('copied');
    }, 2000);
  });
}

async function handleLogin() {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const errorDiv = document.getElementById('login-error');

  errorDiv.classList.add('hidden');

  if (!email || !password) {
    errorDiv.textContent = 'Please enter both email and password';
    errorDiv.classList.remove('hidden');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (data.success) {
      // Store token
      authToken = data.token;
      await chrome.storage.local.set({ authToken: data.token, user: data.user });

      // Show logout button
      document.getElementById('logout-btn').classList.remove('hidden');

      // Start shortening process
      startShorteningProcess();
    } else {
      errorDiv.textContent = data.error || 'Login failed';
      errorDiv.classList.remove('hidden');
    }
  } catch (error) {
    errorDiv.textContent = 'Failed to connect to server';
    errorDiv.classList.remove('hidden');
  }
}

async function handleLogout() {
  // Clear stored auth token
  authToken = null;
  await chrome.storage.local.remove(['authToken', 'user']);

  // Hide logout button
  document.getElementById('logout-btn').classList.add('hidden');

  // Clear form inputs
  document.getElementById('email').value = '';
  document.getElementById('password').value = '';

  // Show login screen
  showContainer('login');
}

async function openDashboard() {
  if (authToken) {
    // User is logged in - open dashboard with auto-login
    chrome.tabs.create({
      url: `http://localhost:5001/extension-auth?token=${authToken}`
    });
  } else {
    // Not logged in - open regular login page
    chrome.tabs.create({
      url: 'http://localhost:5001/login'
    });
  }
}