from assistant.research.perplexity import _parse


def test_parse_extracts_answer_and_citations():
    data = {
        "choices": [{"message": {"content": "The answer is 42."}}],
        "citations": ["http://a.com", "http://b.com"],
    }
    out = _parse(data)
    assert out["answer"] == "The answer is 42."
    assert out["citations"] == ["http://a.com", "http://b.com"]


def test_parse_handles_missing_citations():
    data = {"choices": [{"message": {"content": "No sources here."}}]}
    out = _parse(data)
    assert out["citations"] == []
