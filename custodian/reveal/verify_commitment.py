"""Check the salted commitments in custodian/COMMITMENT.md against the revealed salts and manifests.

Scheme (COMMITMENT.md): commitment = sha256(salt_hex + "\n" + MANIFEST), where MANIFEST is the manifest file's
bytes as published here and salt_hex is the 64 hex characters in the salt file.
Also checks every sealed-v2 file published in sealed-v2/ against its own manifest line (sha256 and byte count).
The other manifest lines name the custodian's construction record, which is not published; for those the manifest
is the record of what was sealed.

usage (from the repository root): python3 custodian/reveal/verify_commitment.py
"""
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
COMMITMENTS = {
    "v1": ("salt.hex", "MANIFEST.sealed.txt", "96d2bc70bbf917bbfdf1d2da8d1044a278fd4b8caf3f7c1596a96c3a2cb26367"),
    "v2": ("salt-v2.hex", "MANIFEST.sealed-v2.txt", "f73c32e4807e793ab0be3bd1a943a01f4f9239a79fae1094ac9dda0e7ced55fe"),
}
failed = False
for version, (salt_file, manifest_file, expected) in COMMITMENTS.items():
    salt = (HERE / salt_file).read_text().strip()
    if len(salt) != 64 or any(c not in "0123456789abcdef" for c in salt):
        raise SystemExit(f"{salt_file}: not 64 lowercase hex characters")
    manifest = (HERE / manifest_file).read_bytes()
    got = hashlib.sha256((salt + "\n").encode() + manifest).hexdigest()
    ok = got == expected
    failed |= not ok
    print(f"{version}: sha256(salt + '\\n' + manifest) = {got}  {'MATCHES' if ok else 'DOES NOT MATCH'} COMMITMENT.md")

lines = {}
for line in (HERE / "MANIFEST.sealed-v2.txt").read_text().splitlines():
    digest, size, path = line.split("  ", 2)
    lines[path] = (digest, int(size))
published = sorted(p.name for p in (ROOT / "sealed-v2").iterdir() if p.is_file())
for name in published:
    if name not in lines:
        raise SystemExit(f"sealed-v2/{name} is not in the v2 manifest")
    data = (ROOT / "sealed-v2" / name).read_bytes()
    ok = hashlib.sha256(data).hexdigest() == lines[name][0] and len(data) == lines[name][1]
    failed |= not ok
    print(f"sealed-v2/{name}: {'matches' if ok else 'DIFFERS FROM'} its manifest line")
print(f"{len(published)} of {len(lines)} manifest entries are published in sealed-v2/; the rest are the unpublished construction record")
raise SystemExit(1 if failed else 0)
