#!/usr/bin/env python3
"""Check BBR's self-reported version on a new loopback TCP connection.

Run after booting the custom kernel. Does not change global TCP settings.
The appended inet_diag BBR ABI reports bbr_version at byte offset 39.
"""
import socket
import sys

TCP_CONGESTION = getattr(socket, "TCP_CONGESTION", 13)
TCP_CC_INFO = getattr(socket, "TCP_CC_INFO", 26)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.settimeout(5)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.settimeout(5)
            client.setsockopt(socket.IPPROTO_TCP, TCP_CONGESTION, b"bbr")
            client.connect(server.getsockname())
            peer, _ = server.accept()
            with peer:
                peer.settimeout(5)
                client.sendall(b"bbr-v3-local-test")
                remaining = len(b"bbr-v3-local-test")
                while remaining:
                    data = peer.recv(remaining)
                    if not data:
                        raise RuntimeError("Unexpected EOF on test connection")
                    remaining -= len(data)
                algorithm = client.getsockopt(socket.IPPROTO_TCP, TCP_CONGESTION, 16).split(b"\0", 1)[0].decode()
                info = client.getsockopt(socket.IPPROTO_TCP, TCP_CC_INFO, 256)
    print(f"Algorithm: {algorithm}; TCP_CC_INFO length: {len(info)} bytes")
    if len(info) < 40:
        print("No BBRv3 version field. This does not verify BBRv3 (expected on the old kernel).")
        return 1
    version = info[39]
    print(f"BBR diagnostic version: {version}")
    if version != 3:
        print("FAIL: BBR does not report version 3")
        return 1
    print("PASS: This new TCP connection reports BBR version 3.")
    print("This is a version check, not a stability or network-performance test.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError) as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        sys.exit(1)
