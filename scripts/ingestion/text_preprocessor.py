#!/usr/bin/env python3
"""
Text preprocessing utilities for vector ingestion
"""

import re
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Preprocess text for vector embedding"""

    def __init__(self):
        self.html_pattern = re.compile(r"<[^>]+>")
        self.whitespace_pattern = re.compile(r"\s+")
        self.url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )

    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return ""
        return self.html_pattern.sub(" ", text)

    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text"""
        if not text:
            return ""
        return self.whitespace_pattern.sub(" ", text).strip()

    def remove_urls(self, text: str) -> str:
        """Remove URLs from text"""
        if not text:
            return ""
        return self.url_pattern.sub("", text)

    def preprocess_for_embedding(self, text: str) -> str:
        """Full preprocessing pipeline for embedding"""
        if not text:
            return ""

        # Apply all preprocessing steps
        text = self.clean_html(text)
        text = self.remove_urls(text)
        text = self.normalize_whitespace(text)

        return text

    def batch_preprocess(self, texts: List[str]) -> List[str]:
        """Preprocess a batch of texts"""
        return [self.preprocess_for_embedding(text) for text in texts]


if __name__ == "__main__":
    preprocessor = TextPreprocessor()

    # Test preprocessing
    test_text = "<p>This is a <b>test</b> text with HTML.</p> Visit https://example.com"
    cleaned = preprocessor.preprocess_for_embedding(test_text)
    logger.info(f"Cleaned: '{cleaned}'")
