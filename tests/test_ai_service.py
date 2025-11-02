import pytest

import runpy
import sys
import types


def _load_ai_service_with_stubs():
    """Dynamically load ai_service.py with minimal stubs, cleaning up after import.

    This avoids polluting sys.modules for other tests.
    """
    added = []
    if "google" not in sys.modules:
        sys.modules["google"] = types.ModuleType("google")
        added.append("google")
    if "google.generativeai" not in sys.modules:
        sys.modules["google.generativeai"] = types.ModuleType("google.generativeai")
        added.append("google.generativeai")
    # Stub a minimal flask module only if one isn't installed in the test env
    flask_stub_added = False
    if "flask" not in sys.modules:
        flask_stub = types.ModuleType("flask")
        # Minimal attribute used by ai_service.configure_gemini (current_app)
        flask_stub.current_app = None
        sys.modules["flask"] = flask_stub
        added.append("flask")
        flask_stub_added = True

    try:
        ai_service = runpy.run_path("app/services/ai_service.py")
    finally:
        # Remove only modules we added earlier to avoid affecting other tests
        for name in added:
            try:
                del sys.modules[name]
            except KeyError:
                pass

    return ai_service


ai_service = _load_ai_service_with_stubs()


def test_content_is_placeholder_positive():
    assert ai_service["content_is_placeholder"]("Enable JavaScript to view this page")
    assert ai_service["content_is_placeholder"]("JS-Disabled")
    assert ai_service["content_is_placeholder"]("Please enable JavaScript")


def test_generate_slugs_from_content_rejects_placeholder():
    with pytest.raises(Exception):
        ai_service["generate_slugs_from_content"](
            title="",
            description="",
            content="Enable JavaScript to view this page",
            num_options=3,
        )
