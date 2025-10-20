import google.generativeai as genai
from flask import current_app
import re


def configure_gemini():
    """Configure Gemini AI with API key."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")
    genai.configure(api_key=api_key)


def generate_slugs_from_content(title, description, content, num_options=5):
    """
    Use Gemini AI to generate slug options based on webpage content.
    Returns list of slug strings.
    """
    configure_gemini()

    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    prompt = f"""
You are a URL slug generator. Based on the following webpage information, generate {num_options} short, descriptive, SEO-friendly URL slugs.

Title: {title}
Description: {description}
Content preview: {content[:500]}

Requirements:
- Maximum 50 characters
- Only lowercase letters (a-z), numbers (0-9), and hyphens (-)
- No leading or trailing hyphens
- No consecutive hyphens
- Descriptive and memorable
- Each slug should be semantically different from the others

Return ONLY the slugs, one per line, nothing else.
"""

    try:
        response = model.generate_content(prompt)
        slugs_text = response.text.strip()

        # Parse slugs from response
        slugs = []
        for line in slugs_text.split("\n"):
            slug = line.strip()
            # Clean and validate slug format
            slug = re.sub(r"[^a-z0-9-]", "", slug.lower())
            slug = re.sub(r"-+", "-", slug)
            slug = slug.strip("-")

            if slug and len(slug) <= 50:
                slugs.append(slug)

        return slugs[:num_options]

    except Exception as e:
        raise Exception(f"AI generation failed: {str(e)}")
