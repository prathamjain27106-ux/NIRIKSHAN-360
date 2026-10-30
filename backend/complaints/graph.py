"""
NIRIKSHAN 360 — Neo4j Case Graph Adapter with PostgreSQL Fallback
===================================================================
Builds and retrieves the relationship network across complaints, institutions, and cells.

SECURITY & ETHICS MANDATE:
  - Neo4j stores ONLY reference identifiers: complaint tracking_id, institution reference,
    cell reference, and issue category.
  - NEVER stores reporter identity (name, email, phone) or sensitive complaint text (narrative).
  - PostgreSQL / Django ORM fallback is always available when Neo4j credentials are missing
    or connection fails.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__name__)

# Check neo4j library
try:
    from neo4j import GraphDatabase, exceptions as neo4j_exceptions
    HAS_NEO4J_LIB = True
except ImportError:
    HAS_NEO4J_LIB = False
    neo4j_exceptions = None


class Neo4jAdapter:
    """Configurable Neo4j adapter for case relationships."""

    def __init__(self):
        self.uri = os.getenv("NEO4J_URI") or getattr(settings, "NEO4J_URI", None)
        self.user = os.getenv("NEO4J_USER") or getattr(settings, "NEO4J_USER", None)
        self.password = os.getenv("NEO4J_PASSWORD") or getattr(settings, "NEO4J_PASSWORD", None)
        self._driver = None

    @property
    def is_configured(self) -> bool:
        return bool(self.uri and self.user and self.password and HAS_NEO4J_LIB)

    def get_driver(self):
        if not self.is_configured:
            return None
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self.uri, auth=(self.user, self.password),
                    connection_timeout=3.0,
                )
            except Exception as e:
                logger.warning(f"Failed to create Neo4j driver: {e}")
                self._driver = None
        return self._driver

    def check_connection(self) -> bool:
        driver = self.get_driver()
        if not driver:
            return False
        try:
            driver.verify_connectivity()
            return True
        except Exception as e:
            logger.info(f"Neo4j connection unavailable: {e}. Falling back to PostgreSQL.")
            return False

    def sync_complaint(self, complaint) -> bool:
        """
        Store ONLY non-sensitive references in Neo4j.
        Never store reporter name, contact, or full complaint text!
        """
        if not self.check_connection():
            return False

        cypher = """
        MERGE (c:Complaint {tracking_id: $tracking_id})
        SET c.category = $category,
            c.urgency = $urgency,
            c.status = $status,
            c.state = $state

        FOREACH (_ IN CASE WHEN $institution_id IS NOT NULL THEN [1] ELSE [] END |
            MERGE (i:Institution {aicte_id: $aicte_id})
            SET i.name = $institution_name, i.state = $state
            MERGE (c)-[:AGAINST]->(i)
        )

        FOREACH (_ IN CASE WHEN $cell <> '' THEN [1] ELSE [] END |
            MERGE (cell:Cell {code: $cell})
            MERGE (c)-[:ROUTED_TO]->(cell)
        )

        FOREACH (_ IN CASE WHEN $duplicate_of IS NOT NULL THEN [1] ELSE [] END |
            MERGE (canon:Complaint {tracking_id: $duplicate_of})
            MERGE (c)-[:POSSIBLE_DUPLICATE_OF]->(canon)
        )
        """
        driver = self.get_driver()
        try:
            with driver.session() as session:
                session.run(
                    cypher,
                    tracking_id=complaint.tracking_id,
                    category=complaint.category,
                    urgency=complaint.urgency,
                    status=complaint.status,
                    state=complaint.state or "",
                    institution_id=str(complaint.institution.id) if complaint.institution else None,
                    aicte_id=complaint.institution.aicte_id if complaint.institution else "UNKNOWN",
                    institution_name=complaint.institution.name if complaint.institution else complaint.institution_name_text,
                    cell=complaint.cell or "",
                    duplicate_of=complaint.duplicate_family.tracking_id if complaint.duplicate_family else None,
                )
            return True
        except Exception as e:
            logger.warning(f"Neo4j sync failed: {e}")
            return False

    def get_graph(
        self,
        complaint_id: Optional[str] = None,
        institution_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Query Neo4j graph. Returns None on connection failure to trigger SQL fallback."""
        if not self.check_connection():
            return None

        driver = self.get_driver()
        nodes_dict = {}
        edges_list = []

        try:
            with driver.session() as session:
                query = """
                MATCH (c:Complaint)
                OPTIONAL MATCH (c)-[r:AGAINST]->(i:Institution)
                OPTIONAL MATCH (c)-[r2:ROUTED_TO]->(cell:Cell)
                OPTIONAL MATCH (c)-[r3:POSSIBLE_DUPLICATE_OF]->(dup:Complaint)
                RETURN c, i, cell, dup
                LIMIT 50
                """
                result = session.run(query)
                for record in result:
                    c = record.get("c")
                    if c:
                        cid = c["tracking_id"]
                        if cid not in nodes_dict:
                            nodes_dict[cid] = {
                                "id": cid,
                                "label": f"{cid}\n{c.get('category', '')}",
                                "type": "complaint",
                                "metadata": {
                                    "status": c.get("status", ""),
                                    "urgency": c.get("urgency", ""),
                                }
                            }
                    i = record.get("i")
                    if i and c:
                        iid = f"INST-{i.get('aicte_id', 'UNKNOWN')}"
                        if iid not in nodes_dict:
                            nodes_dict[iid] = {
                                "id": iid,
                                "label": f"{i.get('name', 'Institution')}\n({i.get('state', '')})",
                                "type": "institution",
                                "metadata": {"aicte_id": i.get("aicte_id", "")}
                            }
                        edges_list.append({
                            "source": c["tracking_id"],
                            "target": iid,
                            "label": "against"
                        })
                    cell = record.get("cell")
                    if cell and c:
                        cell_id = f"CELL-{cell.get('code', '')}"
                        if cell_id not in nodes_dict:
                            nodes_dict[cell_id] = {
                                "id": cell_id,
                                "label": f"Cell: {cell.get('code', '')}",
                                "type": "cell",
                                "metadata": {}
                            }
                        edges_list.append({
                            "source": c["tracking_id"],
                            "target": cell_id,
                            "label": "routed to"
                        })
                    dup = record.get("dup")
                    if dup and c:
                        dup_id = dup["tracking_id"]
                        edges_list.append({
                            "source": c["tracking_id"],
                            "target": dup_id,
                            "label": "potential duplicate"
                        })

            return {
                "nodes": list(nodes_dict.values()),
                "edges": edges_list,
                "fallback": False,
                "engine": "neo4j",
            }
        except Exception as e:
            logger.warning(f"Neo4j query error: {e}. Falling back to PostgreSQL.")
            return None


def get_postgres_graph(
    complaint_id: Optional[str] = None,
    institution_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    PostgreSQL / Django ORM fallback for relationship graph display.
    Guaranteed to return relationship network regardless of Neo4j availability.
    """
    from .models import Complaint
    from institutions.models import Institution

    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    qs = Complaint.objects.select_related("institution", "duplicate_family")
    if complaint_id:
        try:
            import uuid
            uuid.UUID(str(complaint_id))
            qs = qs.filter(Q(tracking_id=complaint_id) | Q(id=complaint_id))
        except (ValueError, AttributeError):
            qs = qs.filter(tracking_id=complaint_id)
    elif institution_id:
        qs = qs.filter(institution_id=institution_id)
    else:
        qs = qs.order_by("-created_at")[:25]

    for c in qs:
        # Complaint node
        c_node_id = c.tracking_id
        if c_node_id not in nodes:
            nodes[c_node_id] = {
                "id": c_node_id,
                "label": f"{c.tracking_id}\n{c.get_category_display()}",
                "type": "complaint",
                "metadata": {
                    "status": c.status,
                    "urgency": c.urgency,
                    "category": c.category,
                    "state": c.state,
                }
            }

        # Institution node & edge
        if c.institution:
            inst_node_id = f"INST-{c.institution.aicte_id}"
            if inst_node_id not in nodes:
                nodes[inst_node_id] = {
                    "id": inst_node_id,
                    "label": f"{c.institution.name}\n({c.institution.state})",
                    "type": "institution",
                    "metadata": {
                        "aicte_id": c.institution.aicte_id,
                        "state": c.institution.state,
                        "type": c.institution.institution_type,
                    }
                }
            edges.append({
                "source": c_node_id,
                "target": inst_node_id,
                "label": "against",
            })
        elif c.institution_name_text:
            text_inst_id = f"INST-{c.institution_name_text[:12].strip()}"
            if text_inst_id not in nodes:
                nodes[text_inst_id] = {
                    "id": text_inst_id,
                    "label": f"{c.institution_name_text}\n({c.state})",
                    "type": "institution",
                    "metadata": {"name": c.institution_name_text}
                }
            edges.append({
                "source": c_node_id,
                "target": text_inst_id,
                "label": "against",
            })

        # Cell node & edge
        if c.cell:
            cell_node_id = f"CELL-{c.cell}"
            if cell_node_id not in nodes:
                nodes[cell_node_id] = {
                    "id": cell_node_id,
                    "label": f"{c.get_cell_display() or c.cell}",
                    "type": "cell",
                    "metadata": {"cell_code": c.cell}
                }
            edges.append({
                "source": c_node_id,
                "target": cell_node_id,
                "label": "routed to",
            })

        # Duplicate edge
        if c.duplicate_family:
            dup_id = c.duplicate_family.tracking_id
            if dup_id not in nodes:
                nodes[dup_id] = {
                    "id": dup_id,
                    "label": f"{c.duplicate_family.tracking_id}\n{c.duplicate_family.get_category_display()}",
                    "type": "complaint",
                    "metadata": {
                        "status": c.duplicate_family.status,
                        "urgency": c.duplicate_family.urgency,
                    }
                }
            edges.append({
                "source": c_node_id,
                "target": dup_id,
                "label": "potential duplicate" if not c.is_duplicate_flagged else "confirmed duplicate",
            })

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "fallback": True,
        "engine": "postgres",
        "status": "POSTGRES_FALLBACK_ACTIVE",
        "relationships": edges,
    }


class CaseGraphAdapter:
    """Public graph adapter that keeps Neo4j optional and fallback-safe."""

    def __init__(self):
        self.neo4j = Neo4jAdapter()

    def sync_complaint(self, complaint) -> str:
        """Sync safe complaint references, or report that SQL remains active."""
        if self.neo4j.sync_complaint(complaint):
            return "NEO4J_ACTIVE"
        return "POSTGRES_FALLBACK_ACTIVE"

    def get_graph(
        self,
        complaint_id: Optional[str] = None,
        institution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        graph_data = self.neo4j.get_graph(
            complaint_id=complaint_id,
            institution_id=institution_id,
        )
        if graph_data is not None:
            return graph_data
        return get_postgres_graph(
            complaint_id=complaint_id,
            institution_id=institution_id,
        )


def get_case_graph(
    complaint_id: Optional[str] = None,
    institution_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get relationship graph. Tries Neo4j first, falls back seamlessly
    to PostgreSQL when disconnected or credentials not configured.
    """
    return CaseGraphAdapter().get_graph(
        complaint_id=complaint_id,
        institution_id=institution_id,
    )
