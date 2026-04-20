"""Tests for logging configuration."""

import json
import logging

from src.utils.logging_config import setup_logging, JSONFormatter


class TestJSONFormatter:
    def test_formats_log_record(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Hello %s",
            args=("world",),
            exc_info=None,
        )
        result = formatter.format(record)
        parsed = json.loads(result)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Hello world"
        assert "timestamp" in parsed
        assert "module" in parsed

    def test_includes_exception(self):
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except Exception:
            import sys
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
            )
            result = formatter.format(record)
            parsed = json.loads(result)
            assert "exception" in parsed
            assert "test error" in parsed["exception"]


class TestSetupLogging:
    def test_returns_root_logger(self):
        logger = setup_logging(log_level="DEBUG")
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.DEBUG

    def test_sets_info_level(self):
        logger = setup_logging(log_level="INFO")
        assert logger.level == logging.INFO

    def test_json_format(self, capsys):
        logger = setup_logging(log_level="DEBUG", json_format=True)
        logger.debug("test json")
        captured = capsys.readouterr()
        assert "test json" in captured.out
        assert '"level": "DEBUG"' in captured.out

    def test_clears_existing_handlers(self):
        logger1 = setup_logging(log_level="INFO")
        handler_count_1 = len(logger1.handlers)
        logger2 = setup_logging(log_level="WARNING")
        handler_count_2 = len(logger2.handlers)
        assert handler_count_1 == handler_count_2
        assert logger2.level == logging.WARNING

    def test_file_handler_created(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_level="DEBUG", log_file=str(log_file))
        logger.info("file test")
        assert log_file.exists()
        content = log_file.read_text()
        assert "file test" in content
