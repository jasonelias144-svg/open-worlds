# WorldPin gains a kind field
@dataclass
class WorldPin:
    world_id: str
    url: str
    world_signer: str
    description: str = ""
    cluster: str = "Uncategorized"
    kind: str = "world"   # NEW: "world" | "map"


# MapRegistry gains a helper
class MapRegistry:
    # ... existing ...
    def map_pins(self) -> List[WorldPin]:
        return [p for p in self._pins.values() if p.kind == "map"]


# Module-level HTTP helper (was previously inside demo)
def _get_json(url, timeout=5.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError, OSError):
        return None


# MultiversalMap._route_to_pin becomes a router
class MultiversalMap:
    def _route_to_pin(self, p: Petition):
        pin = self._registry.get_pin(p.target)
        via_map = None
        if pin is None:
            pin, via_map = self._find_in_submaps(p.target)
        if pin is None:
            return Refusal(reason=f"unknown pin: {p.target}")
        self._log.append({
            "kind": "navigate",
            "actor": p.petitioner_token,
            "target": p.target,
            "via": via_map,
            "ts": _now(),
        })
        try:
            m = _get_json(f"{pin.url.rstrip('/')}/manifest")
            if m is None:
                return Refusal(
                    reason=f"world {p.target} unreachable")
        except Exception as e:
            return Refusal(reason=f"world unavailable: {e}")
        target_manifest = Manifest(
            entity_id=m["entity_id"], name=m["name"],
            protocol_version=m["protocol_version"],
            law_url=m["law_url"],
            act_endpoint=m["act_endpoint"],
            log_endpoint=m["log_endpoint"],
            sub_registry_endpoint=m.get("sub_registry_endpoint"),
        )
        reason = (f"entering {p.target}"
                  + (f" (via map {via_map})" if via_map else ""))
        return Route(target_manifest=target_manifest,
                      reason=reason)

    def _find_in_submaps(self, target_world_id: str):
        """Ask each map-pin's /pin/<target>. First match wins.
        Returns (pin, via_map_id) or (None, None)."""
        for map_pin in self._registry.map_pins():
            sub = _get_json(
                f"{map_pin.url.rstrip('/')}/pin/{target_world_id}")
            if sub is None:
                continue
            if sub.get("status") == "not_registered":
                continue
            url = sub.get("url")
            signer = sub.get("world_signer")
            if not url or not signer:
                continue
            return (WorldPin(
                world_id=target_world_id,
                url=url, world_signer=signer,
                description=sub.get("description", ""),
                cluster=sub.get("cluster", ""),
                kind="world",
            ), map_pin.world_id)
        return (None, None)
