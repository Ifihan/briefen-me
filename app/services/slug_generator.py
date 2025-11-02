import json
from typing import Iterator

from flask import current_app

from app.models.url import URL
from app.services.ai_service import (
    generate_slugs_with_ai_thinking,
    generate_slugs_with_thinking,
)
from app.services.web_scraper import scrape_webpage


def generate_slug_options(url: str) -> Iterator[str]:
    """
    Main service to generate slug options with real-time updates and chain-of-thought.
    """
    max_batches = current_app.config.get("SLUG_GENERATION_BATCHES", 3)
    options_per_batch = current_app.config.get("SLUG_OPTIONS_PER_BATCH", 5)

    # Fetch webpage
    yield json.dumps({"status": "progress", "message": "🌐 Fetching webpage content..."})
    scraped_data = scrape_webpage(url)

    if not scraped_data["success"]:
        error_type = scraped_data.get("error_type", "unknown")
        error_message = scraped_data["error"]

        yield json.dumps({"status": "error", "message": error_message, "error_type": error_type})
        return

    available_slugs = []
    attempts = 0

    for batch in range(max_batches):
        if len(available_slugs) >= 3:
            break

        attempts += 1

        try:
            thinking_mode = current_app.config.get("AI_THINKING_MODE", "hardcoded")

            if thinking_mode == "ai_generated":
                ai_generator = generate_slugs_with_ai_thinking
            else:
                ai_generator = generate_slugs_with_thinking

            ai_slugs = []
            for ai_update in ai_generator(
                scraped_data["title"],
                scraped_data["description"],
                scraped_data["content"],
                num_options=options_per_batch,
            ):
                update_data = json.loads(ai_update)

                if update_data["type"] == "thinking":
                    yield json.dumps({"status": "progress", "message": update_data["message"]})
                elif update_data["type"] == "slugs":
                    ai_slugs = update_data["slugs"]

            if not ai_slugs:
                continue

            # Check availability
            yield json.dumps(
                {
                    "status": "progress",
                    "message": "🔍 Checking if these slugs are available...",
                }
            )

            # Filter out already-taken slugs
            existing_slugs = URL.query.filter(URL.slug.in_(ai_slugs)).all()
            existing_slug_set = {url.slug for url in existing_slugs}

            for candidate in ai_slugs:
                if candidate not in existing_slug_set and candidate not in available_slugs:
                    available_slugs.append(candidate)
                    if len(available_slugs) >= 3:
                        break

            if len(available_slugs) < 3 and batch < max_batches - 1:
                yield json.dumps(
                    {
                        "status": "progress",
                        "message": f"⚡ Some slugs were taken, generating more... (attempt {batch + 2}/{max_batches})",
                    }
                )

        except Exception as e:
            yield json.dumps(
                {
                    "status": "error",
                    "message": f"AI generation error: {str(e)}. Please try again.",
                    "error_type": "ai_error",
                }
            )
            return

    # Return results
    if len(available_slugs) >= 3:
        yield json.dumps(
            {
                "status": "success",
                "message": "🎉 Your smart links are ready!",
                "slugs": available_slugs[:3],
            }
        )
    elif available_slugs:
        yield json.dumps(
            {
                "status": "success",
                "message": f"Found {len(available_slugs)} available option{'s' if len(available_slugs) > 1 else ''}",
                "slugs": available_slugs,
            }
        )
    else:
        yield json.dumps(
            {
                "status": "error",
                "message": "Unable to generate available slugs at this time. All generated options were already taken. Please try again.",
                "error_type": "no_available_slugs",
            }
        )
