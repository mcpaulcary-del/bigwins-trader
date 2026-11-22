"""Big Wins backups (BF-D64): encrypted archives on the server and in OneDrive.

Run by the root host worker (``bigwins backup`` / the nightly timer / app jobs) with the
host's python3 (standard library only) and two well-maintained tools: ``age`` (file
encryption, X25519) and ``rclone`` (OneDrive). Nothing here reads a secret into the app.

    python3 backup.py keygen <key_file>
    python3 backup.py run <plan.json>                  -> one JSON line (the result)
    python3 backup.py restore <archive> <dest_dir> <key_file>
    python3 backup.py verify <archive> <key_file> [<work_dir>]   -> JSON (pass / fail)
    python3 backup.py keep <name> [<name>...]          -> the names retention keeps

* **Archive**: one tar stream of every source (journal dump, config incl. the server's
  ``bfast.local.yaml``, trader output, forward record, forward store, ``deploy/.env``,
  ``deploy/secrets/``, worker state), piped through ``age -r <recipient>``: the whole
  archive, secrets included, is encrypted; only the recovery key decrypts it. A manifest
  (``*.json``: names, sizes, SHA-256 of every file, the journal's row counts; no secret
  values) is written next to it and inside it.
* **Key**: ``age-keygen`` into a root-only file (0600 in a 0700 folder). Backups need only
  its public recipient; restores need the key (the "recovery key").
* **Retention**: the newest archive of each of the last 30 days with one, plus the newest
  of each of the last 12 months with one; the rest is deleted, locally and in OneDrive.
* **Destinations**: the local folder (``/var/backups/bigwins``) and an rclone remote
  (``bigwins-onedrive:Big Wins server backups``); a plain local path also works as the
  remote (tests, a USB disk).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

NAME_RE = re.compile(r"^bigwins-(\d{8})-(\d{6})\.tar\.age$")
DAILY, MONTHLY = 30, 12
EXCLUDE = ("__pycache__", ".git")


def stamp(now: datetime | None = None) -> str:
    return (now or datetime.now(UTC)).astimezone(UTC).strftime("%Y%m%d-%H%M%S")


def keep(names: Iterable[str], daily: int = DAILY, monthly: int = MONTHLY) -> list[str]:
    """Retention: the newest archive per day for the last ``daily`` days that have one,
    and the newest per month for the last ``monthly`` months that have one."""
    arch = sorted((n for n in names if NAME_RE.match(n)), reverse=True)
    by_day: dict[str, str] = {}
    by_month: dict[str, str] = {}
    for n in arch:
        m = NAME_RE.match(n)
        assert m is not None
        by_day.setdefault(m.group(1), n)
        by_month.setdefault(m.group(1)[:6], n)
    out = set(sorted(by_day.values(), reverse=True)[:daily])
    out |= set(sorted(by_month.values(), reverse=True)[:monthly])
    return sorted(out, reverse=True)


def keygen(key_file: Path) -> str:
    """A new age key in a root-only file; returns its public recipient."""
    key_file.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(key_file.parent, 0o700)
    if not key_file.exists():
        subprocess.run(["age-keygen", "-o", str(key_file)], check=True, capture_output=True)
    os.chmod(key_file, 0o600)
    return recipient(key_file)


def recipient(key_file: Path) -> str:
    for line in key_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("# public key: "):
            return line.split(": ", 1)[1].strip()
    r = subprocess.run(["age-keygen", "-y", str(key_file)], check=True, capture_output=True)
    return r.stdout.decode().strip()


def _files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(x in p.parts for x in EXCLUDE):
            yield p


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(sources: Sequence[tuple[str, Path]], extra: dict[str, Any]) -> dict[str, Any]:
    files = []
    for name, root in sources:
        if not root.exists():
            continue
        for p in _files(root):
            rel = name if root.is_file() else f"{name}/{p.relative_to(root).as_posix()}"
            files.append({"path": rel, "size": p.stat().st_size, "sha256": _sha(p)})
    return {"files": files, **extra}


def make_archive(
    sources: Sequence[tuple[str, Path]],
    out_dir: Path,
    recipient_: str,
    extra: dict[str, Any],
    now: datetime | None = None,
) -> tuple[Path, dict[str, Any]]:
    """One encrypted archive of ``sources`` (name, path) and its manifest."""
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"bigwins-{stamp(now)}.tar.age"
    arch = out_dir / name
    man = build_manifest(sources, {"archive": name, "created": stamp(now), **extra})
    tmp = arch.with_suffix(".part")
    with tmp.open("wb") as fout:
        p = subprocess.Popen(["age", "-r", recipient_], stdin=subprocess.PIPE, stdout=fout)
        assert p.stdin is not None
        with tarfile.open(fileobj=p.stdin, mode="w|gz") as tar:
            data = json.dumps(man, indent=1).encode()
            ti = tarfile.TarInfo("MANIFEST.json")
            ti.size = len(data)
            ti.mtime = int(time.time())
            import io

            tar.addfile(ti, io.BytesIO(data))
            for nm, root in sources:
                if root.exists():
                    tar.add(str(root), arcname=nm, filter=_no_junk)
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("age failed")
    tmp.rename(arch)
    os.chmod(arch, 0o600)
    man["size"] = arch.stat().st_size
    summary = {k: v for k, v in man.items() if k != "files"} | {"n_files": len(man["files"])}
    (out_dir / (name + ".json")).write_text(json.dumps(summary))
    return arch, man


def _no_junk(ti: tarfile.TarInfo) -> tarfile.TarInfo | None:
    return None if any(x in ti.name.split("/") for x in EXCLUDE) else ti


def restore(archive: Path, dest: Path, key_file: Path) -> None:
    """Decrypt and unpack ``archive`` into ``dest`` (paths stay inside ``dest``)."""
    dest.mkdir(parents=True, exist_ok=True)
    with subprocess.Popen(
        ["age", "-d", "-i", str(key_file), str(archive)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ) as p:
        assert p.stdout is not None
        try:
            with tarfile.open(fileobj=p.stdout, mode="r|gz") as tar:
                tar.extractall(dest, filter="data")
        except tarfile.TarError as e:
            p.wait()
            raise RuntimeError("age could not decrypt the archive (wrong key?)") from e
        if p.wait() != 0:
            raise RuntimeError("age could not decrypt the archive (wrong key?)")


def verify(archive: Path, key_file: Path, work: Path | None = None) -> dict[str, Any]:
    """Restore into a temporary folder and compare every file with the manifest; the
    journal dump must be there and the LEDGER files of the record byte-identical."""
    tmp = Path(tempfile.mkdtemp(prefix="bigwins-verify-", dir=work))
    try:
        restore(archive, tmp, key_file)
        man = json.loads((tmp / "MANIFEST.json").read_text())
        bad = []
        for f in man["files"]:
            p = tmp / f["path"]
            if not p.is_file() or _sha(p) != f["sha256"]:
                bad.append(f["path"])
        ledger = [f["path"] for f in man["files"] if "LEDGER" in Path(f["path"]).name]
        dump = any(f["path"].startswith("journal/") for f in man["files"])
        ok = not bad and dump
        return {"ok": ok, "files": len(man["files"]), "bad": bad[:20], "ledger_files": len(ledger),
                "journal_dump": dump, "row_counts": man.get("row_counts", {}),
                "archive": archive.name, "restore_dir": str(tmp)}  # fmt: skip
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _remote_list(remote: str) -> list[str]:
    if remote.startswith("/"):
        p = Path(remote)
        return sorted(x.name for x in p.iterdir()) if p.is_dir() else []
    r = subprocess.run(["rclone", "lsf", remote], check=True, capture_output=True, text=True)
    return [x.strip() for x in r.stdout.splitlines() if x.strip()]


def _remote_put(path: Path, remote: str) -> None:
    if remote.startswith("/"):
        Path(remote).mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, Path(remote) / path.name)
        return
    subprocess.run(["rclone", "copyto", str(path), f"{remote}/{path.name}"], check=True,
                   capture_output=True)  # fmt: skip


def _remote_delete(remote: str, name: str) -> None:
    if remote.startswith("/"):
        (Path(remote) / name).unlink(missing_ok=True)
        return
    subprocess.run(["rclone", "deletefile", f"{remote}/{name}"], check=True, capture_output=True)


def prune(names: Sequence[str], delete: Any) -> list[str]:
    """Delete archives (and their manifests) retention does not keep; returns them."""
    kept = set(keep(names))
    gone = [n for n in names if NAME_RE.match(n) and n not in kept]
    for n in gone:
        delete(n)
        if n + ".json" in names:
            delete(n + ".json")
    return gone


def run(plan: dict[str, Any]) -> dict[str, Any]:
    """The nightly backup (also "Back up now"): archive, prune, upload, prune remote."""
    t0 = time.time()
    out = Path(plan["out_dir"])
    stage = Path(tempfile.mkdtemp(prefix="bigwins-stage-", dir=plan.get("work_dir")))
    res: dict[str, Any] = {"ok": False, "local": None, "remote": None, "at": stamp()}
    try:
        dump = stage / "journal"
        dump.mkdir()
        if plan.get("pg_dump"):
            with (dump / "journal.sql").open("wb") as f:
                subprocess.run(plan["pg_dump"], check=True, stdout=f)
        counts = plan.get("row_counts") or {}
        sources = [("journal", dump)] + [(n, Path(p)) for n, p in plan["sources"]]
        arch, man = make_archive(sources, out, recipient(Path(plan["key_file"])),
                                 {"row_counts": counts})  # fmt: skip
        res["local"] = {"archive": arch.name, "size": man["size"], "files": len(man["files"])}
        res["pruned_local"] = prune(sorted(x.name for x in out.iterdir()),
                                    lambda n: (out / n).unlink(missing_ok=True))  # fmt: skip
        remote = plan.get("remote")
        if remote:
            try:
                _remote_put(arch, remote)
                _remote_put(out / (arch.name + ".json"), remote)
                names = _remote_list(remote)
                res["pruned_remote"] = prune(names, lambda n: _remote_delete(remote, n))
                res["remote"] = {"archive": arch.name, "ok": True}
            except (OSError, subprocess.CalledProcessError) as e:
                res["remote"] = {"ok": False, "error": type(e).__name__}
        res["ok"] = res["remote"] is None or bool(res["remote"].get("ok"))
    except (OSError, subprocess.CalledProcessError, RuntimeError) as e:
        res["error"] = f"{type(e).__name__}: {str(e)[:200]}"
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    res["seconds"] = round(time.time() - t0, 1)
    return res


def main(argv: list[str]) -> int:
    op = argv[1] if len(argv) > 1 else ""
    if op == "keygen":
        print(keygen(Path(argv[2])))
        return 0
    if op == "run":
        r = run(json.loads(Path(argv[2]).read_text()))
        print(json.dumps(r))
        return 0 if r["ok"] else 1
    if op == "restore":
        restore(Path(argv[2]), Path(argv[3]), Path(argv[4]))
        return 0
    if op == "verify":
        v = verify(Path(argv[2]), Path(argv[3]), Path(argv[4]) if len(argv) > 4 else None)
        print(json.dumps(v))
        return 0 if v["ok"] else 1
    if op == "keep":
        print("\n".join(keep(argv[2:])))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
