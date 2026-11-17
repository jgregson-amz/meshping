"""Local-subnet peer discovery for the membership layer."""
import ipaddress
import socket


def own_ip():
    """Best-effort local address of this node."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    finally:
        s.close()


def local_hosts(ip, prefix=20):
    """Candidate peer addresses on the local /``prefix`` network, excluding ``ip``."""
    net = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
    for h in net.hosts():
        h = str(h)
        if h != ip:
            yield h
