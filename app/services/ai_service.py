import google.generativeai as genai
from flask import current_app
import re
import json
import time


def configure_gemini():
    """Configure Gemini AI with API key."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")
    genai.configure(api_key=api_key)


def generate_slugs_with_thinking(title, description, content, num_options=5):
    """
    Use Gemini AI to generate slug options with chain-of-thought streaming.
    Yields thinking messages and final slugs.
    """
    configure_gemini()

    yield json.dumps(
        {
            "type": "thinking",
            "message": (
                f'🤔 Analyzing the page... Looks like it\'s about: "{title[:60]}..."'
                if title
                else "🤔 Analyzing the page content..."
            ),
        }
    )
    time.sleep(1)

    if description:
        yield json.dumps(
            {
                "type": "thinking",
                "message": f'📝 I see a description: "{description[:70]}..."',
            }
        )
        time.sleep(1)

    yield json.dumps(
        {
            "type": "thinking",
            "message": "💭 Thinking about relevant keywords and concepts...",
        }
    )
    time.sleep(1)

    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    prompt = f"""
        You are a URL slug generator. Based on the following webpage information, generate {num_options} short, descriptive, SEO-friendly URL slugs.

        Title: {title}
        Description: {description}
        Content preview: {content[:1000]}

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
        yield json.dumps(
            {
                "type": "thinking",
                "message": "✨ Generating creative and meaningful slug options...",
            }
        )

        response = model.generate_content(prompt)
        slugs_text = response.text.strip()

        slugs = []
        for line in slugs_text.split("\n"):
            slug = line.strip()

            slug = re.sub(r"[^a-z0-9-]", "", slug.lower())
            slug = re.sub(r"-+", "-", slug)
            slug = slug.strip("-")

            if slug and len(slug) <= 50:
                slugs.append(slug)

        valid_slugs = slugs[:num_options]

        yield json.dumps(
            {
                "type": "thinking",
                "message": f"✅ Generated {len(valid_slugs)} slug options!",
            }
        )

        yield json.dumps({"type": "slugs", "slugs": valid_slugs})

    except Exception as e:
        raise Exception(f"AI generation failed: {str(e)}")


def generate_slugs_with_ai_thinking(title, description, content, num_options=5):
    """
    Use Gemini AI to generate slug options with REAL AI-generated chain-of-thought.
    This uses Gemini's streaming API to get actual AI reasoning.
    """
    configure_gemini()

    model = genai.GenerativeModel("gemini-2.0-flash-exp")

    prompt = f"""
        You are a URL slug generator. I want you to think out loud about the webpage and then generate {num_options} short URL slugs.

        Title: {title}
        Description: {description}
        Content preview: {content[:1000]}

        Please follow this format:
        1. First, share your observations about what this page is about (2-3 sentences)
        2. Then, identify key concepts and keywords
        3. Finally, generate {num_options} slug options

        Requirements for slugs:
        - Maximum 50 characters
        - Only lowercase letters (a-z), numbers (0-9), and hyphens (-)
        - No leading or trailing hyphens
        - No consecutive hyphens
        - Descriptive and memorable
        - Each slug should be semantically different

        Format your response as:
        THINKING: [your analysis here]
        KEYWORDS: [key concepts]
        SLUGS:
        slug-one
        slug-two
        slug-three
    """

    try:
        response = model.generate_content(prompt, stream=True)

        full_response = ""
        thinking_shown = False
        keywords_shown = False

        for chunk in response:
            if chunk.text:
                full_response += chunk.text

                if (
                    "THINKING:" in full_response
                    and "KEYWORDS:" not in full_response
                    and not thinking_shown
                ):
                    thinking = full_response.split("THINKING:")[1].strip()
                    if thinking and len(thinking) > 10:
                        yield json.dumps(
                            {"type": "thinking", "message": f"🤔 {thinking[:150]}..."}
                        )
                        time.sleep(1.0)
                        thinking_shown = True

                elif (
                    "KEYWORDS:" in full_response
                    and "SLUGS:" not in full_response
                    and not keywords_shown
                ):
                    keywords = (
                        full_response.split("KEYWORDS:")[1].split("SLUGS:")[0].strip()
                    )
                    if keywords and len(keywords) > 5:
                        yield json.dumps(
                            {
                                "type": "thinking",
                                "message": f"💭 Key concepts: {keywords[:100]}...",
                            }
                        )
                        time.sleep(1.0)
                        keywords_shown = True

        if "SLUGS:" in full_response:
            yield json.dumps(
                {
                    "type": "thinking",
                    "message": "✨ Crafting the perfect slug options...",
                }
            )
            time.sleep(1)

        slugs = []
        if "SLUGS:" in full_response:
            slugs_section = full_response.split("SLUGS:")[1].strip()
            for line in slugs_section.split("\n"):
                slug = line.strip()
                slug = re.sub(r"[^a-z0-9-]", "", slug.lower())
                slug = re.sub(r"-+", "-", slug)
                slug = slug.strip("-")

                if slug and len(slug) <= 50:
                    slugs.append(slug)

        valid_slugs = slugs[:num_options]

        yield json.dumps(
            {
                "type": "thinking",
                "message": f"✅ Generated {len(valid_slugs)} slug options!",
            }
        )
        time.sleep(1)

        yield json.dumps({"type": "slugs", "slugs": valid_slugs})

    except Exception as e:
        raise Exception(f"AI generation failed: {str(e)}")


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
        Content preview: {content[:1000]}

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
