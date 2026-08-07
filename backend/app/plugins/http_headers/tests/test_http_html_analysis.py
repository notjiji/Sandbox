from app.plugins.http_headers.html_analysis import find_mixed_content_html


def test_find_mixed_content_html_parses_tags_and_css() -> None:
    body = """
    <html><head><link rel="stylesheet" href="http://cdn.example.com/style.css"></head>
    <body><img src="http://img.example.com/a.png">
    <style>body { background: url(http://bg.example.com/bg.png); }</style></body></html>
    """
    urls = find_mixed_content_html(body, page_url="https://example.com/", is_https=True)
    assert "http://cdn.example.com/style.css" in urls
    assert "http://img.example.com/a.png" in urls
    assert "http://bg.example.com/bg.png" in urls
