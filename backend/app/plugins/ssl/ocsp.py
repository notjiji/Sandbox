"""OCSP stapling detection via pyOpenSSL with OpenSSL CLI fallback."""

from __future__ import annotations

import ctypes
import shutil
import socket
import subprocess


def probe_ocsp_pyopenssl(host: str, port: int, timeout: float) -> bool | None:
    try:
        from OpenSSL import SSL
        from OpenSSL._util import lib as openssl_lib
    except ImportError:
        return None

    try:
        context = SSL.Context(SSL.TLS_CLIENT_METHOD)
        context.set_verify(SSL.VERIFY_NONE, lambda *_: True)
        connection = SSL.Connection(context)
        connection.set_connect_state()
        connection.set_tlsext_host_name(host.encode())

        sock = socket.create_connection((host, port), timeout=timeout)
        connection.set_socket(sock)
        connection.do_handshake()

        data_ptr = ctypes.POINTER(ctypes.c_ubyte)()
        length = openssl_lib.SSL_get0_ocsp_response(connection._ssl, ctypes.byref(data_ptr))  # noqa: SLF001
        sock.close()
        if length > 0:
            return True
        return False
    except Exception:
        return None


def probe_ocsp_openssl_cli(host: str, port: int, timeout: float) -> bool | None:
    openssl = shutil.which("openssl")
    if not openssl:
        return None
    try:
        result = subprocess.run(
            [openssl, "s_client", "-connect", f"{host}:{port}", "-servername", host, "-status"],
            input=b"",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        output = result.stdout.decode("utf-8", errors="replace").lower()
        if "ocsp response:" in output and "no response sent" not in output:
            return True
        if "no response sent" in output:
            return False
    except Exception:
        return None
    return None


def probe_ocsp_stapling(host: str, port: int, timeout: float) -> bool | None:
    result = probe_ocsp_pyopenssl(host, port, timeout)
    if result is not None:
        return result
    return probe_ocsp_openssl_cli(host, port, timeout)
