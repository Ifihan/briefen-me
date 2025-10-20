# Briefen.me - AI-Powered URL Shortener

An intelligent URL shortener that uses AI to generate readable, SEO-friendly short links based on webpage content.

## Features

- AI-powered slug generation using Google Gemini
- Real-time progress updates during link creation
- User accounts with dashboard (optional)
- Anonymous link creation
- Click tracking
- Secure URL validation (SSRF protection)

## Tech Stack

- **Backend**: Flask
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI**: Google Gemini API
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Auth**: Flask-Login

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/Ifihan/briefen-me.git
cd briefen-me
```

```bash
# Install dependencies using uv
uv sync
```

### 2. Set Up Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```env
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key-here
DATABASE_URL=sqlite:///briefen_me.db
```

To get a Gemini API key:

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

### 3. Run the Application

```bash
# Using uv
uv run python main.py

# Or activate virtual environment first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python main.py
```

The application will be available at `http://localhost:5000`

## How It Works

1. **User submits a long URL**
2. **Backend validates the URL** (security checks for SSRF, private IPs, etc.)
3. **Web scraper extracts content** (title, description, main text)
4. **AI generates 5 slug candidates** using Gemini
5. **Database check** - filters out taken slugs
6. **Retry logic** - up to 3 batches if needed
7. **User selects from 3 options**
8. **Short link created** and stored in database

All steps are streamed to the frontend in real-time using Server-Sent Events.

## Configuration

Edit `config.py` to customize:

- `MAX_SLUG_LENGTH`: Maximum characters for slugs (default: 50)
- `SLUG_GENERATION_BATCHES`: Number of retry attempts (default: 3)
- `SLUG_OPTIONS_PER_BATCH`: Slugs generated per batch (default: 5)

## Future Features

- [ ] Link claiming for anonymous users
- [ ] Analytics dashboard
- [ ] Custom slug override
- [ ] Rate limiting implementation
- [ ] Caching layer
- [ ] QR code generation
- [ ] Link expiration
