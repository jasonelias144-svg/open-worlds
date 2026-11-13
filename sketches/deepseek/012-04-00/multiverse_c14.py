# multiverse_c14.py — demo entities for the V02 conformance test.

"""
multiverse_c14.py — demo entities.

A PermissiveWorld is a WCP entity that admits anyone and acks
any act. It exists to let the conformance test exercise signed
Ack verification, which a Law-bound world like Poetry World
will refuse (because "conformance.test" is not a poem.turn).
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Ack,
)


class PermissiveWorld:
    """A WCP entity with the most permissive Law possible.

    - Admits every identity.
    - Acks every act.
    - Never converges.
    """

    def __init__(self, entity_id: str = "world:permissive",
                 name: str = "The Permissive World"):
        self._manifest = Manifest(
            entity_id=entity_id, name=name,
            protocol_version="WCP/0.1",
            law_url=f"permissive://{entity_id}/law",
            act_endpoint=f"permissive://{entity_id}/act",
            log_endpoint=f"permissive://{entity_id}/log",
            sub_registry_endpoint=None,
        )
        self._log: List[LogEntry] = []

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition) -> Union[WCPAdmission, Refusal]:
        ts = datetime.now(timezone.utc).isoformat()
        self._log.append(LogEntry(
            timestamp=ts, kind="admission",
            actor_token=petition.petitioner_token,
            data={"name": petition.petitioner_name},
        ))
        return WCPAdmission(entity_id=self._manifest.entity_id,
                            timestamp=ts)

    def act(self, act: Act) -> Union[Ack, Refusal]:
        ts = datetime.now(timezone.utc).isoformat()
        self._log.append(LogEntry(
            timestamp=ts, kind="act",
            actor_token=act.actor_token,
            data={"type": act.type, "payload": act.payload},
        ))
        return Ack(entity_id=self._manifest.entity_id, timestamp=ts)

    def log_since(self, timestamp: Optional[str] = None) -> List[LogEntry]:
        if timestamp is None:
            return list(self._log)
        return [e for e in self._log if e.timestamp > timestamp]
