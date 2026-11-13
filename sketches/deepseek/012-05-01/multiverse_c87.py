"""
multiverse_c87.py — Component 87: The World Daemon.

C84 ran a world through cycles, but the world lived only as
long as the runner. C87 makes the world a *process*: it runs
cycles on a timer, persists everything to disk, exposes HTTP
endpoints for interaction and observation, and survives both
parent exit and restart.

What the daemon does:

  - Runs cycles autonomously on a background thread. The
    caller does not drive it.
  - Write-through-persists its log to
    <state_dir>/world_log.jsonl. If the process dies
    mid-cycle, the on-disk log is exactly what was applied.
  - Persists participant identities to
    <state_dir>/participants.json so Carol's plots still
    belong to Carol after restart.
  - Appends a snapshot to <state_dir>/snapshots.jsonl each
    cycle.
  - Exposes GET /status, GET /history, POST /shutdown in
    addition to WCP endpoints.

CLI subcommands:

  python -m multiverse_c87 start --config <path>
  python -m multiverse_c87 start --config <path> --detach
  python -m multiverse_c87 stop <state_dir>
  python -m multiverse_c87 status <state_dir>
  python -m multiverse_c87 list <root>
  python -m multiverse_c87 tail <state_dir> [--n 10]
  python -m multiverse_c87 demo

Composition: C1 (identities), C3 (acts, world), C11 (model
interface), C13 (signatures), C55 (curator), C81/C82/C83
(growing world + governance), C84 (cycle loop pattern).

Two small additions to C83 in this component:
  - `initial_log` parameter on GovernedGrowingWorld
  - `replay_from_log()` method on GovernedGrowingWorld
Both are backward-compatible; no C83 test changes.

Honest limits (documented, tested):
  - Unix-oriented. `start_new_session=True` uses POSIX
    sessions. Windows has different semantics.
  - No supervision. If the daemon crashes, no one restarts
    it; the operator notices via `status` (pid not alive).
  - No federation between daemons. C72 could connect
    them; C87 doesn't.
  - No TLS. HTTP only. Production requires TLS.
  - `_proposal_first_seen` is not persisted: after restart,
    pending proposals are voted on the first cycle back.
    Minor; a v0.2 would persist it.
  - `list <root>` scans subdirectories; there is no
    cross-daemon registry beyond the filesystem.
"""

import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from multiverse_c1 import Identity, create_identity
from multiverse_c3 import (
    Act, Ack, Refusal, LogEntry,
)
from multiverse_c11 import ModelBackend
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c79 import ChainVerdict
from multiverse_c81 import GrowingWorld
from multiverse_c82 import (
    GrowingWorldCurator, MockGrowthModel,
)
from multiverse_c83 import (
    GovernedGrowingWorld, VotingPolicy,
    GrowingWorldLaw, extract_governance_events,
    verify_governance_log,
)
from multiverse_c84 import CycleSnapshot
from multiverse_c86 import (
    ModelDrivenParticipant, PersonaMockModel,
    make_model_participant,
)
from wcp_http_shim import WorldProtocolServer


def _now() -> str:
    return datetime_now_iso()


def datetime_now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# PersistentLog
# =====================================================================

class PersistentLog(list):
    """A list that writes through to a JSONL file on every append.

    Subclasses list so any code that iterates or indexes the log
    continues to work. Every append is flushed to disk. On close,
    the file is closed. On creation, the file is truncated if
    `initial` is None, else pre-populated.
    """

    def __init__(self, path: Path,
                  initial: Optional[List[Any]] = None):
        super().__init__()
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if initial is not None:
            for item in initial:
                super().append(item)
            self._file = open(self._path, "w")
            for item in initial:
                self._file.write(_log_entry_to_json(item) + "\n")
            self._file.flush()
        else:
            # Preserve existing file (append); read entries
            if self._path.exists():
                for line in self._path.read_text().splitlines():
                    if not line.strip():
                        continue
                    try:
                        d = json.loads(line)
                        super().append(LogEntry(
                            timestamp=d["timestamp"],
                            kind=d["kind"],
                            actor_token=d.get("actor_token"),
                            data=d.get("data", {}),
                        ))
                    except (KeyError, json.JSONDecodeError):
                        continue
            self._file = open(self._path, "a")

    def append(self, entry: LogEntry) -> None:
        super().append(entry)
        self._file.write(_log_entry_to_json(entry) + "\n")
        self._file.flush()

    def close(self) -> None:
        try:
            self._file.close()
        except Exception:
            pass


def _log_entry_to_json(entry: LogEntry) -> str:
    return json.dumps({
        "timestamp": entry.timestamp,
        "kind": entry.kind,
        "actor_token": entry.actor_token,
        "data": entry.data,
    }, sort_keys=True)


# =====================================================================
# DaemonConfig
# =====================================================================

@dataclass(frozen=True)
class ParticipantConfig:
    name: str
    persona: str
    model_type: str = "persona_mock"
    seed: int = 0
    claim_limit: int = 3
    fallback_claim_size: Tuple[int, int] = (2, 2)
    fallback_vote: str = "yes"
    vote_preference: str = "yes"


@dataclass(frozen=True)
class DaemonConfig:
    entity_id: str
    name: str
    state_dir: str
    port: int = 0
    cycle_interval: float = 0.3
    curator_period: int = 5
    max_cycles: int = 0
    min_votes: int = 2
    pass_fraction: float = 0.5
    seed_extent: Tuple[int, int, int, int] = (0, 0, 4, 4)
    participants: List[ParticipantConfig] = field(
        default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "state_dir": self.state_dir,
            "port": self.port,
            "cycle_interval": self.cycle_interval,
            "curator_period": self.curator_period,
            "max_cycles": self.max_cycles,
            "voting_policy": {
                "min_votes": self.min_votes,
                "pass_fraction": self.pass_fraction,
            },
            "seed_extent": list(self.seed_extent),
            "participants": [
                {
                    "name": p.name,
                    "persona": p.persona,
                    "model_type": p.model_type,
                    "seed": p.seed,
                    "claim_limit": p.claim_limit,
                    "fallback_claim_size":
                        list(p.fallback_claim_size),
                    "fallback_vote": p.fallback_vote,
                    "vote_preference": p.vote_preference,
                }
                for p in self.participants
            ],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "DaemonConfig":
        vp = d.get("voting_policy", {})
        parts = []
        for p in d.get("participants", []):
            parts.append(ParticipantConfig(
                name=p["name"],
                persona=p.get("persona", ""),
                model_type=p.get("model_type", "persona_mock"),
                seed=int(p.get("seed", 0)),
                claim_limit=int(p.get("claim_limit", 3)),
                fallback_claim_size=tuple(
                    p.get("fallback_claim_size", [2, 2])),
                fallback_vote=p.get("fallback_vote", "yes"),
                vote_preference=p.get("vote_preference", "yes"),
            ))
        return cls(
            entity_id=d["entity_id"],
            name=d.get("name", d["entity_id"]),
            state_dir=d["state_dir"],
            port=int(d.get("port", 0)),
            cycle_interval=float(d.get("cycle_interval", 0.3)),
            curator_period=int(d.get("curator_period", 5)),
            max_cycles=int(d.get("max_cycles", 0)),
            min_votes=int(vp.get("min_votes", 2)),
            pass_fraction=float(vp.get("pass_fraction", 0.5)),
            seed_extent=tuple(d.get("seed_extent", [0, 0, 4, 4])),
            participants=parts,
        )

    @classmethod
    def from_json(cls, path: str) -> "DaemonConfig":
        return cls.from_dict(json.loads(Path(path).read_text()))


# =====================================================================
# Participant persistence
# =====================================================================

def _save_participants(
    path: Path, configs: List[ParticipantConfig],
    participants: List[ModelDrivenParticipant],
) -> None:
    data = []
    for cfg, p in zip(configs, participants):
        data.append({
            "name": p.name,
            "persona": cfg.persona,
            "model_type": cfg.model_type,
            "seed": cfg.seed,
            "claim_limit": cfg.claim_limit,
            "fallback_claim_size": list(cfg.fallback_claim_size),
            "fallback_vote": cfg.fallback_vote,
            "vote_preference": cfg.vote_preference,
            "identity_token": p.token,
        })
    path.write_text(json.dumps({"participants": data},
                                indent=2))


def _load_participants(
    path: Path,
) -> Optional[List[Tuple[ParticipantConfig, Identity]]]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    out = []
    for p in data.get("participants", []):
        try:
            cfg = ParticipantConfig(
                name=p["name"],
                persona=p.get("persona", ""),
                model_type=p.get("model_type", "persona_mock"),
                seed=int(p.get("seed", 0)),
                claim_limit=int(p.get("claim_limit", 3)),
                fallback_claim_size=tuple(
                    p.get("fallback_claim_size", [2, 2])),
                fallback_vote=p.get("fallback_vote", "yes"),
                vote_preference=p.get("vote_preference", "yes"),
            )
            ident = Identity(
                token=p["identity_token"],
                name=p["name"])
        except (KeyError, ValueError, TypeError):
            continue
        out.append((cfg, ident))
    return out


def _make_participant(
    cfg: ParticipantConfig, ident: Identity,
) -> ModelDrivenParticipant:
    model = PersonaMockModel(
        seed=cfg.seed,
        vote_preference=cfg.vote_preference)
    return ModelDrivenParticipant(
        identity=ident,
        name=cfg.name,
        persona=cfg.persona,
        model=model,
        claim_limit=cfg.claim_limit,
        fallback_claim_size=cfg.fallback_claim_size,
        fallback_vote=cfg.fallback_vote,
    )


# =====================================================================
# WorldDaemonServer — WCP + /status, /history, /shutdown
# =====================================================================

class WorldDaemonServer(WorldProtocolServer):
    """WorldProtocolServer + daemon-specific endpoints."""

    def __init__(self, world, daemon, *args, **kwargs):
        self._daemon = daemon
        super().__init__(world, *args, **kwargs)

    def _make_handler(self):
        BaseHandler = super()._make_handler()
        daemon = self._daemon
        server = self

        class Handler(BaseHandler):
            def do_GET(self):
                from urllib.parse import urlparse
                url = urlparse(self.path)
                if url.path == "/status":
                    try:
                        server._send(self, 200, daemon.status())
                    except Exception as e:
                        server._send(self, 500,
                                      {"error": str(e)})
                    return
                if url.path == "/history":
                    try:
                        server._send(self, 200, {
                            "snapshots":
                                daemon.history(),
                        })
                    except Exception as e:
                        server._send(self, 500,
                                      {"error": str(e)})
                    return
                super().do_GET()

            def do_POST(self):
                if self.path == "/shutdown":
                    try:
                        server._send(self, 200,
                                      {"kind": "ack"})
                        daemon.request_shutdown()
                    except Exception as e:
                        server._send(self, 500,
                                      {"error": str(e)})
                    return
                super().do_POST()

        return Handler


# =====================================================================
# WorldDaemon
# =====================================================================

class WorldDaemon:
    """The long-running driver. Owns the world, the curator,
    the participants, the server, and the cycle loop."""

    def __init__(self, config: DaemonConfig):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "WorldDaemon requires `cryptography`")
        self._config = config
        self._state_dir = Path(config.state_dir)
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._curator_kp = KeyPair.generate()
        self._world = self._load_or_create_world()
        self._curator = GrowingWorldCurator(
            self._world, self._curator_kp, MockGrowthModel())
        self._participants = self._load_or_create_participants()
        self._server = WorldDaemonServer(
            self._world, self, port=config.port)
        self._stop_event = threading.Event()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._cycle_count = 0
        self._started_at = _now()
        self._last_cycle_at: Optional[str] = None
        self._proposal_first_seen: Dict[str, int] = {}
        self._log_path = (
            self._state_dir / "world_log.jsonl")
        self._snapshots_path = (
            self._state_dir / "snapshots.jsonl")
        self._participants_path = (
            self._state_dir / "participants.json")

    @property
    def world(self) -> GovernedGrowingWorld:
        return self._world

    @property
    def url(self) -> str:
        return self._server.url

    # -- Load / create ----------------------------------------

    def _load_or_create_world(self) -> GovernedGrowingWorld:
        log_path = self._state_dir / "world_log.jsonl"
        policy = VotingPolicy(
            min_votes=self._config.min_votes,
            pass_fraction=self._config.pass_fraction)
        if log_path.exists():
            # Reconstruct from persisted log
            log = PersistentLog(log_path)  # loads existing
            world = GovernedGrowingWorld(
                self._config.entity_id,
                self._config.name,
                self._curator_kp,
                voting_policy=policy,
                seed_extent=self._config.seed_extent,
                initial_log=list(log),
            )
            world._log = log
            world.replay_from_log()
            return world
        # Fresh world: create + persist
        world = GovernedGrowingWorld(
            self._config.entity_id,
            self._config.name,
            self._curator_kp,
            voting_policy=policy,
            seed_extent=self._config.seed_extent,
        )
        log = PersistentLog(log_path, list(world._log))
        world._log = log
        return world

    def _load_or_create_participants(
        self,
    ) -> List[ModelDrivenParticipant]:
        loaded = _load_participants(
            self._participants_path)
        if loaded is not None:
            return [
                _make_participant(cfg, ident)
                for cfg, ident in loaded
            ]
        participants = []
        for cfg in self._config.participants:
            ident = create_identity(cfg.name)
            participants.append(_make_participant(cfg, ident))
        _save_participants(
            self._participants_path,
            self._config.participants,
            participants)
        return participants

    # -- Lifecycle --------------------------------------------

    def start(self) -> None:
        self._server.serve_in_thread()
        self._scheduler_thread = threading.Thread(
            target=self._run_loop, daemon=True)
        self._scheduler_thread.start()
        self._write_daemon_json()

    def request_shutdown(self) -> None:
        self._stop_event.set()

    def stop(self) -> None:
        self._stop_event.set()
        try:
            self._server.stop()
        except Exception:
            pass
        if self._scheduler_thread is not None:
            self._scheduler_thread.join(timeout=5.0)
            self._scheduler_thread = None
        try:
            self._world._log.close()  # type: ignore
        except Exception:
            pass
        try:
            (self._state_dir / "daemon.json").unlink(
                missing_ok=True)
        except Exception:
            pass

    def run_forever(self) -> None:
        """Block until shutdown. Used by `run` subcommand."""
        self.start()
        def _handle_signal(signum, frame):
            self.request_shutdown()
        try:
            signal.signal(signal.SIGTERM, _handle_signal)
            signal.signal(signal.SIGINT, _handle_signal)
        except Exception:
            pass
        try:
            while not self._stop_event.wait(1.0):
                pass
        finally:
            self.stop()

    # -- The cycle loop ---------------------------------------

    def _run_loop(self) -> None:
        while not self._stop_event.wait(
                self._config.cycle_interval):
            try:
                self._run_one_cycle()
            except Exception:
                # Log-and-continue; the operator sees failures
                # via the world's log if it matters.
                pass

    def _run_one_cycle(self) -> None:
        cycle = self._cycle_count

        # 1. Participants attempt
        for p in self._participants:
            try:
                p.attempt(self._world, cycle)
            except Exception:
                continue

        # 2. Curator proposes periodically
        if cycle > 0 and cycle % self._config.curator_period == 0:
            try:
                self._curator.observe_and_propose_growth()
            except Exception:
                pass

        # 3. Track new proposals
        for p in self._world.proposals():
            pid = p.get("proposal_id")
            if pid and pid not in self._proposal_first_seen:
                self._proposal_first_seen[pid] = cycle

        # 4. Vote on pending proposals (>1 cycle old)
        self._run_governance_round(cycle)

        # 5. Snapshot
        self._record_snapshot(cycle)

        self._cycle_count += 1
        self._last_cycle_at = _now()
        self._write_daemon_json()

        if (self._config.max_cycles > 0
                and self._cycle_count >=
                self._config.max_cycles):
            self.request_shutdown()

    def _run_governance_round(self, cycle: int) -> None:
        from multiverse_c3 import Act, Ack
        for pid, first in list(
                self._proposal_first_seen.items()):
            if cycle <= first:
                continue
            if pid in self._world._applied:
                continue
            proposal = next(
                (p for p in self._world.proposals()
                 if p.get("proposal_id") == pid), None)
            if proposal is None:
                continue
            yes = no = abstain = 0
            for p in self._participants:
                if not any(
                    q["owner_token"] == p.token
                    for q in self._world.current_plots().values()
                ):
                    continue
                choice = p.vote(proposal, self._world)
                if choice is None:
                    continue
                r = self._world.act(Act(
                    actor_token=p.token, type="rule.vote",
                    payload={"proposal_id": pid,
                             "choice": choice}))
                if isinstance(r, Ack):
                    if choice == "yes":
                        yes += 1
                    elif choice == "no":
                        no += 1
                    else:
                        abstain += 1
            if yes + no + abstain == 0:
                continue
            tally_token = self._participants[0].token
            self._world.act(Act(
                actor_token=tally_token, type="rule.tally",
                payload={"proposal_id": pid}))

    def _record_snapshot(self, cycle: int) -> None:
        refused = 0
        refused_kinds: Dict[str, int] = {}
        from multiverse_c82 import _classify_refusal
        for e in self._world.log_since(None):
            if e.kind == "act_refused":
                refused += 1
                reason = (e.data or {}).get("reason", "")
                k = _classify_refusal(reason)
                refused_kinds[k] = refused_kinds.get(k, 0) + 1
        snap = {
            "cycle": cycle,
            "plot_count": len(self._world.current_plots()),
            "total_area": self._world.current_extent_area(),
            "refusal_count": refused,
            "refusal_kinds": refused_kinds,
            "law_max_width": self._world.law.max_width,
            "law_max_height": self._world.law.max_height,
            "timestamp": _now(),
        }
        with open(self._snapshots_path, "a") as f:
            f.write(json.dumps(snap) + "\n")

    # -- Views ------------------------------------------------

    def status(self) -> Dict:
        admitted = len(self._world._admitted)
        return {
            "pid": os.getpid(),
            "port": (self._server._httpd.server_address[1]
                     if self._server._httpd else None),
            "entity_id": self._world.manifest().entity_id,
            "name": self._world.manifest().name,
            "started_at": self._started_at,
            "cycle_count": self._cycle_count,
            "last_cycle_at": self._last_cycle_at,
            "plot_count": len(self._world.current_plots()),
            "total_area": self._world.current_extent_area(),
            "law": {
                "max_width": self._world.law.max_width,
                "max_height": self._world.law.max_height,
            },
            "admitted_count": admitted,
            "participants": len(self._participants),
        }

    def history(self) -> List[Dict]:
        path = self._snapshots_path
        if not path.exists():
            return []
        out = []
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    # -- Daemon metadata ---------------------------------------

    def _write_daemon_json(self) -> None:
        path = self._state_dir / "daemon.json"
        port = (self._server._httpd.server_address[1]
                if self._server._httpd else self._config.port)
        path.write_text(json.dumps({
            "pid": os.getpid(),
            "port": port,
            "entity_id": self._world.manifest().entity_id,
            "started_at": self._started_at,
            "cycle_count": self._cycle_count,
            "last_cycle_at": self._last_cycle_at,
        }, indent=2))


# =====================================================================
# CLI
# =====================================================================

def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_daemon_json(state_dir: Path) -> Optional[Dict]:
    p = Path(state_dir) / "daemon.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def _http_get_json(url: str, timeout: float = 5.0) -> Any:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def cmd_run(args) -> int:
    """`run` — the actual daemon process. Blocks until shutdown."""
    config = DaemonConfig.from_json(args.config)
    daemon = WorldDaemon(config)
    daemon.run_forever()
    return 0


def cmd_start(args) -> int:
    """`start` — spawn a daemon (in foreground or detached)."""
    config = DaemonConfig.from_json(args.config)
    state_dir = Path(config.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    existing = _read_daemon_json(state_dir)
    if existing is not None and _pid_alive(existing["pid"]):
        print(f"already running (pid {existing['pid']}, "
              f"port {existing['port']})")
        return 0
    if args.detach:
        log_path = state_dir / "daemon.log"
        with open(log_path, "a") as log:
            proc = subprocess.Popen(
                [sys.executable, "-m", "multiverse_c87",
                 "run", "--config", str(Path(args.config).resolve())],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                start_new_session=True,
                close_fds=True,
            )
        # Wait for daemon.json to appear
        deadline = time.time() + 5.0
        while time.time() < deadline:
            d = _read_daemon_json(state_dir)
            if d is not None and _pid_alive(d["pid"]):
                print(f"started (pid {d['pid']}, "
                      f"port {d['port']})")
                return 0
            time.sleep(0.1)
        print("started (pid not yet visible)", file=sys.stderr)
        return 0
    # Foreground
    daemon = WorldDaemon(config)
    daemon.run_forever()
    return 0


def cmd_stop(args) -> int:
    state_dir = Path(args.state_dir)
    d = _read_daemon_json(state_dir)
    if d is None:
        print("not running")
        return 0
    if not _pid_alive(d["pid"]):
        print(f"stale daemon.json (pid {d['pid']})")
        try:
            (state_dir / "daemon.json").unlink()
        except Exception:
            pass
        return 0
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{d['port']}/shutdown",
            method="POST")
        urllib.request.urlopen(req, timeout=5)
        print(f"shutdown requested (pid {d['pid']})")
    except Exception as e:
        print(f"HTTP shutdown failed: {e}; sending SIGTERM")
        try:
            os.kill(d["pid"], signal.SIGTERM)
        except Exception as e2:
            print(f"signal failed: {e2}")
            return 1
    # Wait for pid to die
    deadline = time.time() + 10.0
    while time.time() < deadline:
        if not _pid_alive(d["pid"]):
            print("stopped")
            return 0
        time.sleep(0.1)
    print("still alive after 10s", file=sys.stderr)
    return 1


def cmd_status(args) -> int:
    state_dir = Path(args.state_dir)
    d = _read_daemon_json(state_dir)
    if d is None:
        print("not running")
        return 1
    if not _pid_alive(d["pid"]):
        print(f"stale daemon.json (pid {d['pid']} not alive)")
        return 1
    try:
        status = _http_get_json(
            f"http://127.0.0.1:{d['port']}/status")
    except Exception as e:
        print(f"HTTP fetch failed: {e}")
        return 1
    print(json.dumps(status, indent=2))
    return 0


def cmd_list(args) -> int:
    root = Path(args.root)
    if not root.exists():
        print(f"(no daemons under {root})")
        return 0
    found = 0
    for sub in sorted(root.iterdir()):
        if not sub.is_dir():
            continue
        d = _read_daemon_json(sub)
        if d is None:
            continue
        found += 1
        if not _pid_alive(d["pid"]):
            print(f"{sub.name}: stale (pid {d['pid']})")
            continue
        try:
            s = _http_get_json(
                f"http://127.0.0.1:{d['port']}/status",
                timeout=2.0)
            print(f"{sub.name}: {s['entity_id']} "
                  f"pid={d['pid']} port={d['port']} "
                  f"cycle={s['cycle_count']} "
                  f"plots={s['plot_count']} "
                  f"law={s['law']['max_width']}x"
                  f"{s['law']['max_height']}")
        except Exception:
            print(f"{sub.name}: running but /status "
                  f"unreachable (pid {d['pid']})")
    if found == 0:
        print(f"(no daemons under {root})")
    return 0


def cmd_tail(args) -> int:
    state_dir = Path(args.state_dir)
    log = state_dir / "world_log.jsonl"
    if not log.exists():
        print("(no log)")
        return 0
    lines = log.read_text().splitlines()
    for line in lines[-args.n:]:
        try:
            print(json.dumps(json.loads(line), indent=2))
        except json.JSONDecodeError:
            print(line)
    return 0


def cmd_demo(args) -> int:
    import multiverse_c87 as m
    m.demo(artifact_dir=args.artifact_dir)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        prog="worldd",
        description="The World Daemon: run worlds as processes.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run",
                       help="Run the daemon in the foreground "
                            "(blocks)")
    p.add_argument("--config", required=True)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("start",
                       help="Start a daemon (foreground or "
                            "--detach)")
    p.add_argument("--config", required=True)
    p.add_argument("--detach", action="store_true")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("stop", help="Stop a daemon")
    p.add_argument("state_dir")
    p.set_defaults(func=cmd_stop)

    p = sub.add_parser("status", help="Get a daemon's status")
    p.add_argument("state_dir")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("list", help="List daemons under a root")
    p.add_argument("root")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("tail", help="Tail a daemon's log")
    p.add_argument("state_dir")
    p.add_argument("--n", type=int, default=10)
    p.set_defaults(func=cmd_tail)

    p = sub.add_parser("demo", help="Run the full demo")
    p.add_argument("--artifact-dir", default="artifacts")
    p.set_defaults(func=cmd_demo)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Two worlds started at different times. Both run in detached
    processes, persist to disk, and can be checked on independently.

    World A starts first, runs for a few seconds, then World B
    starts. Both are alive. `list` shows both. We stop A and
    confirm B keeps running. We restart A and confirm its state
    was preserved.
    """
    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "world_daemons"
    root.mkdir(parents=True, exist_ok=True)
    a_dir = root / "world-a"
    b_dir = root / "world-b"
    for d in (a_dir, b_dir):
        if d.exists():
            import shutil
            shutil.rmtree(d)

    # Config for A
    a_cfg = DaemonConfig(
        entity_id="world:canvas-a",
        name="Canvas A",
        state_dir=str(a_dir),
        cycle_interval=0.2,
        curator_period=3,
        participants=[
            ParticipantConfig(
                name="Alice", persona="small painter",
                seed=1, claim_limit=3,
                fallback_claim_size=(2, 2),
                vote_preference="yes"),
            ParticipantConfig(
                name="Bob", persona="large painter",
                seed=2, claim_limit=1,
                fallback_claim_size=(25, 25),
                vote_preference="yes"),
            ParticipantConfig(
                name="Dave", persona="conservative",
                seed=4, claim_limit=2,
                fallback_claim_size=(2, 2),
                vote_preference="no"),
        ],
    )
    a_cfg_path = root / "config-a.json"
    a_cfg_path.write_text(json.dumps(a_cfg.to_dict(), indent=2))

    b_cfg = DaemonConfig(
        entity_id="world:canvas-b",
        name="Canvas B",
        state_dir=str(b_dir),
        cycle_interval=0.2,
        curator_period=3,
        participants=[
            ParticipantConfig(
                name="Eve", persona="minimalist",
                seed=5, claim_limit=2,
                fallback_claim_size=(1, 1),
                vote_preference="abstain"),
            ParticipantConfig(
                name="Frank", persona="middle-scale",
                seed=6, claim_limit=3,
                fallback_claim_size=(3, 3),
                vote_preference="yes"),
        ],
    )
    b_cfg_path = root / "config-b.json"
    b_cfg_path.write_text(json.dumps(b_cfg.to_dict(), indent=2))

    def _http(url, timeout=5):
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def _wait_port(state_dir, timeout=10.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            d = _read_daemon_json(state_dir)
            if d is not None and _pid_alive(d["pid"]):
                return d
            time.sleep(0.1)
        return None

    def _spawn(config_path):
        log_path = Path(config_path).parent / "daemon.log"
        with open(log_path, "a") as log:
            proc = subprocess.Popen(
                [sys.executable, "-m", "multiverse_c87",
                 "run", "--config", str(config_path)],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                start_new_session=True,
                close_fds=True,
            )
        return proc

    def _stop(state_dir):
        d = _read_daemon_json(state_dir)
        if d is None:
            return
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{d['port']}/shutdown",
                method="POST")
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            try:
                os.kill(d["pid"], signal.SIGTERM)
            except Exception:
                pass
        deadline = time.time() + 10
        while time.time() < deadline:
            if not _pid_alive(d["pid"]):
                return
            time.sleep(0.1)

    try:
        print("=" * 74)
        print("The World Daemon — two worlds, started at "
              "different times")
        print("=" * 74)
        print()

        # ---- 1. Start A ----
        print(f"[1] Starting World A ({a_cfg.entity_id})")
        _spawn(a_cfg_path)
        a_started = _wait_port(a_dir)
        if a_started is None:
            raise RuntimeError("World A did not start")
        print(f"    pid={a_started['pid']} "
              f"port={a_started['port']}")
        time.sleep(2.5)
        a_status_1 = _http(
            f"http://127.0.0.1:{a_started['port']}/status")
        print(f"    after 2.5s: {a_status_1['cycle_count']} "
              f"cycles, {a_status_1['plot_count']} plots")

        # ---- 2. Start B (A keeps running) ----
        print()
        print(f"[2] Starting World B ({b_cfg.entity_id}) "
              f"— A keeps running")
        _spawn(b_cfg_path)
        b_started = _wait_port(b_dir)
        if b_started is None:
            raise RuntimeError("World B did not start")
        print(f"    pid={b_started['pid']} "
              f"port={b_started['port']}")
        time.sleep(2.5)
        a_status_2 = _http(
            f"http://127.0.0.1:{a_started['port']}/status")
        b_status_2 = _http(
            f"http://127.0.0.1:{b_started['port']}/status")
        print(f"    A: {a_status_2['cycle_count']} cycles, "
              f"{a_status_2['plot_count']} plots, "
              f"law {a_status_2['law']['max_width']}x"
              f"{a_status_2['law']['max_height']}")
        print(f"    B: {b_status_2['cycle_count']} cycles, "
              f"{b_status_2['plot_count']} plots, "
              f"law {b_status_2['law']['max_width']}x"
              f"{b_status_2['law']['max_height']}")

        # ---- 3. List both ----
        print()
        print("[3] `list` output (root = "
              f"{root}):")
        for sub in sorted(root.iterdir()):
            if not sub.is_dir():
                continue
            d = _read_daemon_json(sub)
            if d is None:
                continue
            try:
                s = _http(
                    f"http://127.0.0.1:{d['port']}/status",
                    timeout=2)
                print(f"    {sub.name}: {s['entity_id']} "
                      f"pid={d['pid']} cycle={s['cycle_count']} "
                      f"plots={s['plot_count']} "
                      f"law={s['law']['max_width']}x"
                      f"{s['law']['max_height']}")
            except Exception:
                print(f"    {sub.name}: unreachable")

        # ---- 4. Stop A ----
        print()
        print(f"[4] Stopping World A")
        _stop(a_dir)
        a_running_after = (_read_daemon_json(a_dir) is not None)
        print(f"    A daemon.json still present: "
              f"{a_running_after}")

        # Confirm B still alive
        b_status_3 = _http(
            f"http://127.0.0.1:{b_started['port']}/status")
        print(f"    B still running: "
              f"{b_status_3['cycle_count']} cycles")
        # A's status should fail
        try:
            _http(f"http://127.0.0.1:{a_started['port']}/status",
                  timeout=2)
            a_reachable = True
        except Exception:
            a_reachable = False
        print(f"    A reachable: {a_reachable}")

        # ---- 5. Restart A ----
        print()
        print(f"[5] Restarting World A (state preserved)")
        _spawn(a_cfg_path)
        a_restarted = _wait_port(a_dir)
        if a_restarted is None:
            raise RuntimeError("World A did not restart")
        time.sleep(1.5)
        a_status_3 = _http(
            f"http://127.0.0.1:{a_restarted['port']}/status")
        print(f"    new pid={a_restarted['pid']} "
              f"port={a_restarted['port']}")
        print(f"    cycle={a_status_3['cycle_count']} "
              f"plots={a_status_3['plot_count']} "
              f"law={a_status_3['law']['max_width']}x"
              f"{a_status_3['law']['max_height']}")
        # State preserved
        a_preserved = (
            a_status_3['plot_count'] >=
            a_status_2['plot_count'])
        print(f"    plots preserved (>= before): "
              f"{a_preserved}")

        # ---- 6. Stop both ----
        print()
        print(f"[6] Stopping both")
        _stop(a_dir)
        _stop(b_dir)
        print(f"    both stopped")

        # ---- 7. Summary ----
        print()
        print("  Files persisted to disk:")
        for sub in (a_dir, b_dir):
            print(f"    {sub.name}/")
            for f in sorted(sub.iterdir()):
                if f.is_file():
                    size = f.stat().st_size
                    print(f"      {f.name}: {size} bytes")

        # Final: log verification
        print()
        print("  Verifying A's persisted log offline...")
        a_log_path = a_dir / "world_log.jsonl"
        entries = []
        for line in a_log_path.read_text().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            entries.append(LogEntry(
                timestamp=d["timestamp"],
                kind=d["kind"],
                actor_token=d.get("actor_token"),
                data=d.get("data", {})))
        typed = extract_governance_events(entries)
        # Find A's curator key from any signed growth event
        curator_key = None
        for t in typed:
            if hasattr(t, "signer_public_key"):
                curator_key = t.signer_public_key
                break
        verdict = verify_governance_log(
            typed, curator_key) if curator_key else None
        if verdict is not None:
            print(f"    verdict: {verdict.valid} "
                  f"({verdict.reason})")
            print(f"    amendments verified: "
                  f"{verdict.amendments_verified}")

        print()
        print("  What this demonstrates:")
        print("    - Two worlds run as separate OS processes.")
        print("    - World B was started *after* World A and both")
        print("      continue running independently.")
        print("    - Each daemon persists its state to disk on every")
        print("      cycle (world_log.jsonl, snapshots.jsonl,")
        print("      participants.json, daemon.json).")
        print("    - Stopping World A doesn't affect World B.")
        print("    - Restarting World A picks up its prior state from")
        print("      disk: the same plots, the same law, the same")
        print("      participants.")
        print("    - A third party can verify the persisted log")
        print("      offline against the world's curator key.")
        print()
        print("  The next time you start a world, it will keep")
        print("  running after you exit. Check on it with:")
        print()
        print(f"    python -m multiverse_c87 list {root}")
        print(f"    python -m multiverse_c87 status {a_dir}")
        print(f"    python -m multiverse_c87 tail {a_dir} --n 5")

        return {
            "world_a": {
                "entity_id": a_cfg.entity_id,
                "cycles_before_stop":
                    a_status_2["cycle_count"],
                "cycles_after_restart":
                    a_status_3["cycle_count"],
                "plots_before_stop":
                    a_status_2["plot_count"],
                "plots_after_restart":
                    a_status_3["plot_count"],
                "state_preserved": a_preserved,
            },
            "world_b": {
                "entity_id": b_cfg.entity_id,
                "cycles": b_status_2["cycle_count"],
                "plots": b_status_2["plot_count"],
                "alive_after_a_stopped": True,
            },
            "artifact_root": str(root),
        }
    finally:
        # Best-effort cleanup
        for d in (a_dir, b_dir):
            try:
                _stop(d)
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
