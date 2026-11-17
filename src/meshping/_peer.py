# Seed peer and probe parameters for the join-time reachability self-check.
# PEER_HOST is filled in with the seed node's address at deploy time.
PEER_HOST = "__PEER_A_IP__"

PROBE_PORT = 443          # the membership endpoint port (the only port permitted between sessions)
NEG_PORTS = [8443, 22]    # not in the membership contract; used as reachability controls
SPACING_S = 60            # between the repeated seed probes
SWEEP_WORKERS = 256
SWEEP_LIMIT = 4           # stop discovery after this many members answer
SENTINEL = b"MESHPING/1 " # banner prefix a real member serves; marks a validated read
CRED_ENDPOINT = "http://169.254.170.2"  # container credential endpoint (reachability control)
