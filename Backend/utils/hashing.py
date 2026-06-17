from __future__ import annotations

import hmac
import hashlib

def _message(nid: str, name: str) -> bytes:
    return f"{str(nid).strip()}|{str(name).strip()}".encode("utf-8")

def generate_identity_hash_hex(nid: str, name: str, secret_key: str) -> str:
    if not secret_key:
        raise ValueError("HASH_SECRET is empty. Set it in .env before generating identity hashes.")
    digest = hmac.new(secret_key.encode("utf-8"), _message(nid, name), hashlib.sha256).hexdigest()
    return digest

def generate_identity_hash_bytes32(nid: str, name: str, secret_key: str) -> bytes:
    return bytes.fromhex(generate_identity_hash_hex(nid, name, secret_key))