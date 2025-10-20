import requests
from bs4 import BeautifulSoup


def scrape_webpage(url, timeout=10):
    """
    Scrape webpage content for AI analysis.
    Returns dict with title, description, and main content.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; BriefenMe/1.0; +http://briefen.me)"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = ""
        if soup.title:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()

        # Extract meta description
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"].strip()

        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        main_text = soup.get_text(separator=" ", strip=True)[:1000]

        return {
            "success": True,
            "title": title,
            "description": description,
            "content": main_text,
            "url": url,
        }

    except requests.RequestException as e:
        return {"success": False, "error": f"Failed to fetch webpage: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error processing webpage: {str(e)}"}
