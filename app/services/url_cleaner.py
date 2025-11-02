from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

FUNCTIONAL_PARAMS = {
    "id",
    "article_id",
    "post_id",
    "video_id",
    "product_id",
    "item_id",
    "p",
    "page",
    "post",
    "v",
    "watch",
    "tab",
    "section",
    "category",
    "sort",
    "order",
    "filter",
    "search",
    "q",
    "query",
    "keywords",
    "offset",
    "limit",
    "start",
    "variant",
    "color",
    "size",
    "quantity",
    "sku",
    "asin",
    "action",
    "mode",
    "view",
    "format",
    "t",
    "time",
    "timestamp",
    "version",
    "feature",
    "ab_test",
}


def remove_tracking_parameters(url):
    """Remove tracking parameters by keeping only functional ones."""
    if not url:
        return url

    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)

        cleaned = {
            k: v for k, v in query_params.items() if k.lower() in FUNCTIONAL_PARAMS
        }

        new_query = urlencode(cleaned, doseq=True) if cleaned else ""

        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
        )
    except Exception:
        return url