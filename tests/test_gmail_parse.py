from assistant.connectors.gmail_client import _header


def test_header_lookup_is_case_insensitive():
    headers = [{"name": "From", "value": "a@b.com"}, {"name": "Subject", "value": "Hi"}]
    assert _header(headers, "from") == "a@b.com"
    assert _header(headers, "subject") == "Hi"
    assert _header(headers, "Date") == ""
