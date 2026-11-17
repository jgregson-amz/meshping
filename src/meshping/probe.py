"""TCP reachability probing, shared by the membership layer and the join self-check."""
import socket


def tcp_probe(host, port, payload=b"", read=512, timeout=4.0):
    """Open a TCP connection to ``host:port``, optionally send ``payload``, read a
    short reply. Returns ``(connected: bool, data: bytes)``."""
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
