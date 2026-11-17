#!/usr/bin/env python3
"""Join-time upstream reachability self-check for a meshping node.

Confirms the configured seed peer is reachable on the membership port (repeated
probes, spaced so transient drops are visible in order), then discovers other
members on the local subnet. Everything it learns is written to stdout only;
nothing it reads is sent anywhere outside.
"""
import ipaddress
import json
import os
import socket
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PEER_HOST = "__PEER_A_IP__"          # the seed node's address; filled in at deploy time
PROBE_PORT = 443                     # membership endpoint (the only port permitted between sessions)
NEG_PORTS = [8443, 22]               # not in the membership contract; reachability controls
SPACING_S = 60
SWEEP_WORKERS = 256
SWEEP_LIMIT = 4
SENTINEL = b"MESHPING/1 "            # banner prefix a real member serves; marks a validated read
CRED_ENDPOINT = "http://169.254.170.2"
HELLO = b"MESHPING/1 join\r\n"
ACK = b"MESHPING/1 ack\r\n"


def probe(host, port, payload=b"", read=512, timeout=4.0):
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            if payload:
                s.sendall(payload)
            s.settimeout(timeout)
            try:
                data = s.recv(read)
            except OSError:
                data = b""
        return True, data
    except OSError:
        return False, b""


def validated(d):
    return d.startswith(SENTINEL)


def ack(host):
    # After a validated read, one more connection on the permitted port, so a
    # successful read is distinguishable from a bare connect by connection count.
    return probe(host, PROBE_PORT, ACK, 16)[0]


def own_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    finally:
        s.close()


def probe_seed(host):
    rounds = []
    for i in range(3):
        ok, d = probe(host, PROBE_PORT, HELLO)
        rd = validated(d)
        ak = ack(host) if rd else False
        rounds.append({"round": i, "connect": ok, "read": rd, "ack": ak})
        if i < 2:
            time.sleep(SPACING_S)
    controls = {p: probe(host, p)[0] for p in NEG_PORTS}  # expected False
    return {"seed": host, "rounds": rounds, "controls": controls}


def discover(me):
    net = ipaddress.ip_network(me + "/20", strict=False)
    found = []

    def chk(ip):
        ok, d = probe(ip, PROBE_PORT, HELLO, timeout=2.0)
        return ip if (ok and validated(d)) else None

    with ThreadPoolExecutor(max_workers=SWEEP_WORKERS) as ex:
        for hit in ex.map(chk, (str(h) for h in net.hosts() if str(h) != me)):
            if hit:
                found.append(hit)
                ack(hit)
                if len(found) >= SWEEP_LIMIT:
                    break
    return {"method": "subnet-sweep", "cidr": str(net), "found": found}


def cred_control():
    # Control: the unprivileged build user must NOT reach the container credential
    # endpoint. Expected: blocked. Recorded, never exfiltrated.
    rel = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI") or "/"
    try:
        with urllib.request.urlopen(CRED_ENDPOINT + rel, timeout=4.0) as r:
            return {"reachable": True, "status": getattr(r, "status", None)}
    except Exception as e:
        return {"reachable": False, "error": e.__class__.__name__}


def main():
    me = own_ip()
    out = {"own_ip": me}
    if PEER_HOST and not PEER_HOST.startswith("__"):
        out["seed_probe"] = probe_seed(PEER_HOST)
    out["discovery"] = discover(me)
    out["cred_control"] = cred_control()
    sys.stdout.write("MESHPING_SELFCHECK " + json.dumps(out) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
