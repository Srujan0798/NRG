import src.security.pii as pii_module


def test_scan_detects_aadhaar_with_regex_fallback(monkeypatch):
    monkeypatch.setattr(pii_module, "_load_spacy_model", lambda: None)
    result = pii_module.scan("My Aadhaar is 1234 5678 9010")

    assert result["detected_pii"] is True
    assert any(entity["type"] == "aadhaar" for entity in result["entities"])
    assert result["mode"] == "regex_only"


def test_scan_works_when_spacy_model_is_available(monkeypatch):
    class _Token:
        def __init__(self, text: str, idx: int):
            self.text = text
            self.idx = idx
            self.like_email = "@" in text

    class _Ent:
        def __init__(self, label_: str, text: str, start: int, end: int):
            self.label_ = label_
            self.text = text
            self.start_char = start
            self.end_char = end

    class _Doc:
        def __init__(self):
            self.ents = [_Ent("EMAIL", "test@example.com", 11, 27)]
            self._tokens = [_Token("test@example.com", 11)]

        def __iter__(self):
            return iter(self._tokens)

    class _NLP:
        def __call__(self, _text: str):
            return _Doc()

    monkeypatch.setattr(pii_module, "_load_spacy_model", lambda: _NLP())
    result = pii_module.scan("Contact me: test@example.com")

    assert result["detected_pii"] is True
    assert result["mode"] == "spacy+regex"
