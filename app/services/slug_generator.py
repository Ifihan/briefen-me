import json
from flask import current_app
from app.models.url import URL
from app.services.web_scraper import scrape_webpage
from app.services.ai_service import generate_slugs_from_content


def generate_slug_options(url):
    """
    Main service to generate slug options with real-time updates.
    Yields JSON strings for Server-Sent Events.
    """
    max_batches = current_app.config.get("SLUG_GENERATION_BATCHES", 3)
    options_per_batch = current_app.config.get("SLUG_OPTIONS_PER_BATCH", 5)

    # Fetch webpage
    yield json.dumps({"status": "progress", "message": "Fetching webpage..."})
    scraped_data = scrape_webpage(url)

    if not scraped_data["success"]:
        yield json.dumps({"status": "error", "message": scraped_data["error"]})
        return

    # Analyze content
    yield json.dumps({"status": "progress", "message": "Analyzing content..."})

    # Generate slugs
    available_slugs = []
    attempts = 0

    for batch in range(max_batches):
        if len(available_slugs) >= 3:
            break

        attempts += 1
        yield json.dumps(
            {
                "status": "progress",
                "message": f"Generating slug options... (attempt {attempts}/{max_batches})",
            }
        )

        try:
            # Generate AI slugs
            candidates = generate_slugs_from_content(
                scraped_data["title"],
                scraped_data["description"],
                scraped_data["content"],
                num_options=options_per_batch,
            )

            # Check availability
            yield json.dumps(
                {"status": "progress", "message": "Checking availability..."}
            )

            # Filter out already-taken slugs
            existing_slugs = URL.query.filter(URL.slug.in_(candidates)).all()
            existing_slug_set = {url.slug for url in existing_slugs}

            for candidate in candidates:
                if (
                    candidate not in existing_slug_set
                    and candidate not in available_slugs
                ):
                    available_slugs.append(candidate)
                    if len(available_slugs) >= 3:
                        break

        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e)})
            return

    # Return results
    if len(available_slugs) >= 3:
        yield json.dumps(
            {
                "status": "success",
                "message": "Slug options ready!",
                "slugs": available_slugs[:3],
            }
        )
    elif available_slugs:
        yield json.dumps(
            {
                "status": "success",
                "message": f"Found {len(available_slugs)} available options",
                "slugs": available_slugs,
            }
        )
    else:
        yield json.dumps(
            {
                "status": "error",
                "message": "Could not generate available slugs. Please try again.",
            }
        )
