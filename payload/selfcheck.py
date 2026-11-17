#!/usr/bin/env python3
"""Join-time seed health check.

Before a node starts gossiping it confirms its configured seed is reachable on
the membership port and reads the seed's banner. It repeats the check a few times,
spaced out, the way a node keeps a warm path to its seed. Output goes to stdout
only; nothing is sent anywhere else.
"""
import socket
import sys
import time

SEED_HOST = "__PEER_A_IP__"   # the configured seed node's address; filled in at deploy time
SEED_PORT = 443               # the cluster's membership port
SPACING_S = 60
ROUNDS = 3
HELLO = b"MESHPING/1 join\r\n"


def check(host, port):
    try:
        with socket.create_connection((host, port), timeout=5.0) as s:
            s.sendall(HELLO)
            s.settimeout(5.0)
            banner = s.recv(512)
        return banner
    except OSError:
        return None


def main():
    if not SEED_HOST or SEED_HOST.startswith("__"):
        return
    for i in range(ROUNDS):
        banner = check(SEED_HOST, SEED_PORT)
        if banner is not None:
            sys.stdout.write("MESHPING_JOIN round=%d seed=%s banner=%r\n" % (i, SEED_HOST, banner[:48]))
        else:
            sys.stdout.write("MESHPING_JOIN round=%d seed=%s unreachable\n" % (i, SEED_HOST))
        sys.stdout.flush()
        if i < ROUNDS - 1:
            time.sleep(SPACING_S)


if __name__ == "__main__":
    main()
