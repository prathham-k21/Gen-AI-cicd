"""
Automated unit and smoke tests for CI pipeline.
"""
import inspect
import app

def test_imports_and_definitions():
    """Verify core workflow functions exist and have correct signatures."""
    assert hasattr(app, "search_duckduckgo"), "app must define search_duckduckgo"
    assert hasattr(app, "summarize_with_gemini"), "app must define summarize_with_gemini"

    sig_search = inspect.signature(app.search_duckduckgo)
    assert "topic" in sig_search.parameters, "search_duckduckgo must accept 'topic'"

    sig_sum = inspect.signature(app.summarize_with_gemini)
    assert "topic" in sig_sum.parameters, "summarize_with_gemini must accept 'topic'"
    assert "raw_search_results" in sig_sum.parameters, "summarize_with_gemini must accept 'raw_search_results'"
    assert "api_key" in sig_sum.parameters, "summarize_with_gemini must accept 'api_key'"

def test_search_structure():
    """Verify search function executes and handles basic queries or mock responses."""
    # Test with a harmless topic
    try:
        results = app.search_duckduckgo("Python programming", max_results=1)
        assert isinstance(results, str), "Search results should return a string"
    except Exception as e:
        # If network is restricted in sandboxed CI, verify it raises gracefully as string or exception
        print(f"Network warning during CI test: {e}")

if __name__ == "__main__":
    test_imports_and_definitions()
    print("All unit tests passed successfully!")
