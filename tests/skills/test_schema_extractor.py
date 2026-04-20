"""Tests for Text-to-SQL Schema Extractor."""

import src.skills.text_to_sql.schema_extractor as schema_extractor_module


class FakeInspector:
    def __init__(self, tables):
        self._tables = tables

    def get_table_names(self):
        return list(self._tables.keys())

    def get_columns(self, table_name):
        return self._tables[table_name]["columns"]

    def get_pk_constraint(self, table_name):
        return self._tables[table_name].get("pk", {})

    def get_foreign_keys(self, table_name):
        return self._tables[table_name].get("fks", [])

    def get_indexes(self, table_name):
        return self._tables[table_name].get("indexes", [])


class FakeEngine:
    pass


def _make_extractor(monkeypatch, tables):
    monkeypatch.setattr(
        schema_extractor_module, "create_engine", lambda cs, **kw: FakeEngine()
    )
    monkeypatch.setattr(
        schema_extractor_module, "inspect", lambda engine: FakeInspector(tables)
    )
    return schema_extractor_module.SchemaExtractor("sqlite:///:memory:")


def test_get_schema_metadata(monkeypatch):
    tables = {
        "researchers": {
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False, "default": None},
                {"name": "name", "type": "VARCHAR", "nullable": True, "default": None},
            ],
            "pk": {"constrained_columns": ["id"]},
            "fks": [],
            "indexes": [{"name": "idx_name", "column_names": ["name"]}],
        }
    }
    extractor = _make_extractor(monkeypatch, tables)
    schema = extractor.get_schema_metadata()
    assert "researchers" in schema["tables"]
    assert schema["tables"]["researchers"]["columns"][0]["name"] == "id"
    assert schema["tables"]["researchers"]["primary_keys"] == ["id"]
    assert schema["tables"]["researchers"]["indexes"][0]["name"] == "idx_name"


def test_generate_llm_prompt(monkeypatch):
    tables = {
        "researchers": {
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False, "default": None},
            ],
            "pk": {"constrained_columns": ["id"]},
            "fks": [],
            "indexes": [],
        }
    }
    extractor = _make_extractor(monkeypatch, tables)
    schema = extractor.get_schema_metadata()
    prompt = extractor.generate_llm_prompt(schema)
    assert "DATABASE SCHEMA" in prompt
    assert "Table: researchers" in prompt
    assert "id: INTEGER NOT NULL" in prompt


def test_get_relevant_tables_researcher_query(monkeypatch):
    tables = {
        "researchers": {
            "columns": [],
            "pk": {},
            "fks": [],
            "indexes": [],
        },
        "publications": {
            "columns": [],
            "pk": {},
            "fks": [],
            "indexes": [],
        },
    }
    extractor = _make_extractor(monkeypatch, tables)
    relevant = extractor.get_relevant_tables("Find researchers in Gujarat")
    assert "researchers" in relevant


def test_get_relevant_tables_default_fallback(monkeypatch):
    tables = {
        "researchers": {
            "columns": [],
            "pk": {},
            "fks": [],
            "indexes": [],
        },
        "unknown_table": {
            "columns": [],
            "pk": {},
            "fks": [],
            "indexes": [],
        },
    }
    extractor = _make_extractor(monkeypatch, tables)
    relevant = extractor.get_relevant_tables("xyz unrelated query")
    assert "researchers" in relevant


def test_close_disposes_engine(monkeypatch):
    disposed = []

    class TrackEngine:
        pass

    def track_dispose():
        disposed.append(True)

    monkeypatch.setattr(
        schema_extractor_module, "create_engine", lambda cs, **kw: TrackEngine()
    )
    monkeypatch.setattr(
        schema_extractor_module, "inspect", lambda engine: FakeInspector({})
    )
    extractor = schema_extractor_module.SchemaExtractor("sqlite:///:memory:")
    extractor.engine.dispose = track_dispose
    extractor.close()
    assert disposed == [True]
