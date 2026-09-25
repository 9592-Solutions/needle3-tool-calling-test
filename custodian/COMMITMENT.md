# Needle 3 sealed test: salted commitments

**Current: v2** (sealed 2026-09-22 15:23 CEST, labelled under CONTRACT.md v1.1, 54f5a4ff).

**Commitment v2: `f73c32e4807e793ab0be3bd1a943a01f4f9239a79fae1094ac9dda0e7ced55fe`** (179 files)

Why v1 was superseded: CONTRACT v1.1 (the configuration lead's clarifications, no action, value or
default changed) arrived after the v1 seal. The arms are configured and scored against v1.1, and gold
that followed v1.0 would score the contract change rather than the models, so m37-lead ruled to
relabel under v1.1 and re-seal before FREEZE (2026-09-22). The affected items were relabelled by a
blind pair plus an adjudicator; 10 gold labels on 4 items moved, and 3 test families that no longer
fitted their stratum were replaced whole. v1's files are kept unchanged, and both commitments are
revealed and verifiable at publication.

Same scheme for both: `sha256(salt_hex + "\n" + MANIFEST)`, where MANIFEST is the UTF-8 text of one
line per sealed file, `"<sha256>  <bytes>  <relative path>"`, sorted by path, each line ending in
`\n`; the salt is 32 random bytes as 64 lowercase hex characters, a separate salt per version. Salts
and manifests are revealed with the results; the manifests are not published before then, because
their file sizes and names would describe the test.

---

## Superseded: v1 (kept on record, not overwritten)


Sealed 2026-09-22 14:53 CEST by the test custodian (session 2ceae776).

**Commitment v1 (superseded by v2): `96d2bc70bbf917bbfdf1d2da8d1044a278fd4b8caf3f7c1596a96c3a2cb26367`**

Scheme: `sha256(salt_hex + "\n" + MANIFEST)`, where MANIFEST is the UTF-8 text of one line per
sealed file, `"<sha256>  <bytes>  <relative path>"`, sorted by path, each line ending in `\n`.
The salt is 32 random bytes as 64 lowercase hex characters. 150 files are sealed.
The salt and the manifest are revealed with the results; anyone can then recompute the
commitment and every file hash. The manifest itself is not published before then, because its
file sizes and names would describe the test.
