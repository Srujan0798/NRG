"""Graph Service - Knowledge graph traversal for research network visualization."""

import logging
import os
import sqlite3


logger = logging.getLogger(__name__)

DEFAULT_NODE_LIMIT = 100
DEFAULT_EDGE_LIMIT = 300


def get_db_connection():
    """Get database connection with row factory."""
    db_path = os.getenv("DATABASE_URL", "sqlite:///nrg_research.db")
    if db_path.startswith("postgresql://"):
        logger.warning("Graph service using SQLite fallback; PostgreSQL primary")
        db_path = "nrg_research.db"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _add_node(nodes: list[dict], node_id_map: dict[str, str], label: str, ntype: str, counter: int, **props) -> str:
    """Add a node to the graph if not already present."""
    key = f"{ntype}:{label}"
    if key in node_id_map:
        return node_id_map[key]

    node_id = f"{ntype[0]}{counter}"
    node_id_map[key] = node_id
    nodes.append({
        "id": node_id,
        "label": label[:100],
        "type": ntype,
        **props
    })
    return node_id


def build_topic_graph(
    topic: str,
    user_tier: int = 1,
    node_limit: int = DEFAULT_NODE_LIMIT,
    edge_limit: int = DEFAULT_EDGE_LIMIT,
) -> dict:
    """Build research network graph for a topic.

    Expands from keyword → papers → authors → institutions.
    Tier determines data visibility bounds.
    """
    nodes: list[dict] = []
    edges: list[dict] = []
    node_id_map: dict[str, str] = {}
    node_counter = 0

    conn = get_db_connection()
    try:
        topic_lower = topic.lower()

        cursor = conn.execute("""
            SELECT keyword_id FROM keywords
            WHERE LOWER(term) LIKE ?
            LIMIT 20
        """, (f"%{topic_lower}%",))
        keyword_ids = [row["keyword_id"] for row in cursor.fetchall()]

        if not keyword_ids:
            cursor = conn.execute("""
                SELECT DISTINCT p.publication_id, p.title, p.year, p.access_tier
                FROM publications p
                WHERE LOWER(p.title) LIKE ? OR LOWER(p.abstract) LIKE ?
                LIMIT 50
            """, (f"%{topic_lower}%", f"%{topic_lower}%"))
        else:
            cursor = conn.execute("""
                SELECT DISTINCT p.publication_id, p.title, p.year, p.access_tier
                FROM publications p
                JOIN publication_keywords pk ON p.publication_id = pk.publication_id
                WHERE pk.keyword_id IN ({})
                LIMIT 50
            """.format(",".join("?" * len(keyword_ids))), tuple(keyword_ids))

        publications = {}
        for row in cursor.fetchall():
            if row["access_tier"] <= user_tier:
                pub_id = row["publication_id"]
                pid = _add_node(
                    nodes, node_id_map,
                    row["title"][:80], "paper", node_counter,
                    year=row["year"]
                )
                publications[pub_id] = pid
                node_counter += 1

            if node_counter >= node_limit:
                break

        if node_counter < node_limit:
            cursor = conn.execute("""
                SELECT DISTINCT r.researcher_id, r.name, r.research_area, r.state,
                       r.access_tier
                FROM researchers r
                JOIN researcher_publications rp ON r.researcher_id = rp.researcher_id
                WHERE rp.publication_id IN ({})
                LIMIT 50
            """.format("," .join("?" * len(publications.keys()))),
                tuple(publications.keys()))

            for row in cursor.fetchall():
                if row["access_tier"] <= user_tier:
                    rid = _add_node(
                        nodes, node_id_map,
                        row["name"], "author", node_counter,
                        area=row["research_area"],
                        state=row["state"]
                    )
                    node_counter += 1

                    if rid in node_id_map.values():
                        continue

                    for pub_id, pid in publications.items():
                        if len(edges) >= edge_limit:
                            break
                        edges.append({
                            "source": rid,
                            "target": pid,
                            "type": "authored",
                            "weight": 1
                        })

                if node_counter >= node_limit:
                    break

        if node_counter < node_limit:
            cursor = conn.execute("""
                SELECT institution_id, name, state
                FROM institutions
                LIMIT 30
            """)

            for row in cursor.fetchall():
                if node_counter >= node_limit:
                    break

                iid = _add_node(
                    nodes, node_id_map,
                    row["name"], "institution", node_counter,
                    state=row["state"]
                )

                if len(edges) >= edge_limit:
                    break

                if row["institution_id"]:
                    cursor2 = conn.execute("""
                        SELECT researcher_id FROM researchers
                        WHERE institution_id = ?
                        LIMIT 10
                    """, (row["institution_id"],))

                    for rrow in cursor2.fetchall():
                        rid_key = "author:UNKNOWN"
                        for k, v in node_id_map.items():
                            if k.startswith("author:") and v not in [e["source"] for e in edges if "source" in e]:
                                rid_key = k
                                break

                        if rid_key in node_id_map:
                            edges.append({
                                "source": node_id_map[rid_key],
                                "target": iid,
                                "type": "affiliated",
                                "weight": 1
                            })

                node_counter += 1

    finally:
        conn.close()

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "topic": topic,
            "tier": user_tier
        }
    }


def build_institution_graph(
    institution_id: str,
    user_tier: int = 1,
    depth: int = 2,
    node_limit: int = DEFAULT_NODE_LIMIT,
) -> dict:
    """Build graph for an institution and its connections."""
    nodes: list[dict] = []
    edges = []
    node_id_map: dict[str, str] = {}
    node_counter = 0

    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT * FROM institutions WHERE institution_id = ?
        """, (institution_id,))
        inst_row = cursor.fetchone()

        if inst_row:
            _add_node(nodes, node_id_map, inst_row["name"], "institution", node_counter,
                     state=inst_row["state"])

        cursor = conn.execute("""
            SELECT r.* FROM researchers r
            WHERE r.institution_id = ? AND r.access_tier <= ?
        """, (institution_id, user_tier))

        for row in cursor.fetchall():
            rid = _add_node(nodes, node_id_map, row["name"], "author", node_counter,
                          area=row["research_area"], state=row["state"])
            edges.append({
                "source": node_id_map.get(f"institution:{inst_row['name']}", ""),
                "target": rid,
                "type": "affiliated",
                "weight": 1
            })
            node_counter += 1

        cursor = conn.execute("""
            SELECT p.* FROM publications p
            JOIN researcher_publications rp ON p.publication_id = rp.publication_id
            JOIN researchers r ON rp.researcher_id = r.researcher_id
            WHERE r.institution_id = ? AND p.access_tier <= ?
        """, (institution_id, user_tier))

        for row in cursor.fetchall():
            _add_node(nodes, node_id_map, row["title"][:50], "paper", node_counter,
                      year=row["year"])
            node_counter += 1

    finally:
        conn.close()

    return {"nodes": nodes, "edges": edges}