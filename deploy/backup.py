"""Big Wins backups (BF-D64): encrypted archives on the server and in OneDrive.

Run by the root host worker (``bigwins backup`` / the nightly timer / app jobs) with the
host's python3 (standard library only) and two well-maintained tools: ``age`` (file
encryption, X25519) and ``rclone`` (OneDrive). Nothing here reads a secret into the app.

    python3 backup.py keygen <key_file>
    python3 backup.py run <plan.json>                  -> one JSON line (the result)
    python3 backup.py restore <archive> <dest_dir> <key_file>
    python3 backup.py verify <archive> <key_file> [<work_dir>]   -> JSON (pass / fail)
    python3 backup.py keep <name> [<name>...]          -> the names retention keeps
    python3 backup.py latest <dir>                     -> the newest archive (not future-dated)
    python3 backup.py fingerprint <key_file>           -> the recovery key's short fingerprint
    python3 backup.py check-manifest <restore_dir> <key_file>   -> the signed manifest is intact

Review (22 Nov 2026, BF-D70): the manifest is signed (HMAC-SHA256 with a key derived from
the recovery key, so only its holder can sign or check it) and checked before a restore;
archive names dated in the future are ignored when picking and pruning; absolute symlinks
are refused; the upload is checked by size; leftover ``.part`` files are removed; local
and remote retention are separate (default 7 daily locally, 30 daily + 12 monthly in
OneDrive); an archive over 300 MB is flagged; the recovery key's fingerprint is in every
result.

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
import hmac
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
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

NAME_RE = re.compile(r"^bigwins-(\d{8})-(\d{6})\.tar\.age$")
DAILY, MONTHLY = 30, 12
LOCAL_DAILY, LOCAL_MONTHLY = 7, 0  # review F11: the server keeps a week
BIG = 300 * 1024 * 1024  # review F11: an archive above this is flagged
EXCLUDE = ("__pycache__", ".git")


def stamp(now: datetime | None = None) -> str:
    return (now or datetime.now(UTC)).astimezone(UTC).strftime("%Y%m%d-%H%M%S")


def _dated(names: Iterable[str], now: datetime | None = None) -> list[str]:
    """Archive names, newest first, without any dated in the future (review L1: a planted
    or clock-skewed name is neither restored nor allowed to push real archives out)."""
    limit = stamp((now or datetime.now(UTC)) + timedelta(days=1))
    return sorted((n for n in names if NAME_RE.match(n) and n[8:23] <= limit), reverse=True)


def latest(names: Iterable[str], now: datetime | None = None) -> str | None:
    d = _dated(names, now)
    return d[0] if d else None


def keep(names: Iterable[str], daily: int = DAILY, monthly: int = MONTHLY,
         now: datetime | None = None) -> list[str]:  # fmt: skip
    """Retention: the newest archive per day for the last ``daily`` days that have one,
    and the newest per month for the last ``monthly`` months that have one (future-dated
    names are not counted and never deleted here)."""
    arch = _dated(names, now)
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


def fingerprint(key_file: Path) -> str:
    """A short fingerprint of the recovery key's public recipient (shown in the app)."""
    return hashlib.sha256(recipient(key_file).encode()).hexdigest()[:12]


def _mac_key(key_file: Path) -> bytes:
    """The manifest-signing key, derived from the recovery key (root only)."""
    secret = "".join(x.strip() for x in key_file.read_text(encoding="utf-8").splitlines()
                     if x.startswith("AGE-SECRET-KEY-"))  # fmt: skip
    if not secret:
        raise RuntimeError("the recovery key file holds no AGE-SECRET-KEY line")
    return hashlib.sha256(b"bigwins-manifest-v1\0" + secret.encode()).digest()


def sign_manifest(man: dict[str, Any], key_file: Path) -> str:
    body = json.dumps(man, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(_mac_key(key_file), body, hashlib.sha256).hexdigest()


def check_manifest(restore_dir: Path, key_file: Path) -> dict[str, Any]:
    """The unpacked archive's manifest and its signature (review L1). Raises if they do
    not match (a tampered or foreign archive is never restored)."""
    man = json.loads((restore_dir / "MANIFEST.json").read_text())
    sig_p = restore_dir / "MANIFEST.sig"
    if not sig_p.is_file():
        raise RuntimeError("the archive has no signed manifest (made before review L1?)")
    if not hmac.compare_digest(sig_p.read_text().strip(), sign_manifest(man, key_file)):
        raise RuntimeError("the manifest signature does not match: archive refused")
    out: dict[str, Any] = man
    return out


def _files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(x in p.parts for x in EXCLUDE):
            yield p


def absolute_links(sources: Sequence[tuple[str, Path]]) -> list[str]:
    """Review L4: symlinks with an absolute target, or one leaving their source folder."""
    bad = []
    for _, root in sources:
        if not root.is_dir():
            continue
        top = root.resolve()
        for p in root.rglob("*"):
            if p.is_symlink():
                t = os.readlink(p)
                if os.path.isabs(t) or not str(p.resolve()).startswith(str(top)):
                    bad.append(str(p))
    return bad


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
    bad = absolute_links(sources)
    if bad:
        raise RuntimeError("absolute or escaping symlinks refused: " + ", ".join(bad[:5]))
    name = f"bigwins-{stamp(now)}.tar.age"
    arch = out_dir / name
    man = build_manifest(sources, {"archive": name, "created": stamp(now), **extra})
    key_file = extra.pop("_key_file", None) if isinstance(extra, dict) else None
    man.pop("_key_file", None)
    sig = sign_manifest(man, Path(key_file)) if key_file else ""
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
            if sig:
                ts = tarfile.TarInfo("MANIFEST.sig")
                ts.size = len(sig)
                ts.mtime = ti.mtime
                tar.addfile(ts, io.BytesIO(sig.encode()))
            for nm, root in sources:
                if root.exists():
                    tar.add(str(root), arcname=nm, filter=_no_junk)
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("age failed")
    tmp.rename(arch)
    os.chmod(arch, 0o600)
    man["size"] = arch.stat().st_size
    summary = {k: v for k, v in man.items() if k != "files"} | {"n_files": len(man["files"]),
                                                                 "sig": sig}  # fmt: skip
    (out_dir / (name + ".json")).write_text(json.dumps(summary))
    return arch, man


def _no_junk(ti: tarfile.TarInfo) -> tarfile.TarInfo | None:
    return None if any(x in ti.name.split("/") for x in EXCLUDE) else ti


def _age_error(err: bytes) -> str:
    """Review L4: say what went wrong, not always "wrong key?"."""
    t = err.decode(errors="replace").lower()
    if "no identity matched" in t:
        return "this recovery key does not open the archive (wrong key)"
    if "header" in t or "parse" in t or "invalid" in t:
        return "the archive is damaged or not an age file"
    return "age could not decrypt the archive: " + (t.strip()[:120] or "unknown error")


def restore(archive: Path, dest: Path, key_file: Path, *, check: bool = True) -> None:
    """Decrypt and unpack ``archive`` into ``dest`` (paths stay inside ``dest``); with
    ``check`` the signed manifest must match (review L1)."""
    dest.mkdir(parents=True, exist_ok=True)
    with subprocess.Popen(
        ["age", "-d", "-i", str(key_file), str(archive)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as p:
        assert p.stdout is not None
        assert p.stderr is not None
        try:
            with tarfile.open(fileobj=p.stdout, mode="r|gz") as tar:
                tar.extractall(dest, filter="data")
        except tarfile.TarError as e:
            p.wait()
            raise RuntimeError(_age_error(p.stderr.read())) from e
        if p.wait() != 0:
            raise RuntimeError(_age_error(p.stderr.read()))
    if check:
        check_manifest(dest, key_file)


def verify(archive: Path, key_file: Path, work: Path | None = None,
           keep_dir: bool = False) -> dict[str, Any]:  # fmt: skip
    """Restore into a temporary folder and compare every file with the signed manifest;
    the journal dump must be there and the LEDGER files of the record byte-identical.
    ``keep_dir``: leave the folder for the caller (the restore test's database load: the
    archive is unpacked once, review L3); the caller deletes it."""
    tmp = Path(tempfile.mkdtemp(prefix="bigwins-verify-", dir=work))
    os.chmod(tmp, 0o700)
    try:
        try:
            restore(archive, tmp, key_file)
        except RuntimeError as e:
            return {"ok": False, "error": str(e), "archive": archive.name}
        man = json.loads((tmp / "MANIFEST.json").read_text())
        bad = []
        for f in man["files"]:
            p = tmp / f["path"]
            if not p.is_file() or _sha(p) != f["sha256"]:
                bad.append(f["path"])
        ledger = [f["path"] for f in man["files"] if "LEDGER" in Path(f["path"]).name]
        dump = any(f["path"].startswith("journal/") for f in man["files"])
        ok = not bad and dump
        need = [s for s in man.get("required", []) if not any(
            f["path"] == s or f["path"].startswith(s + "/") for f in man["files"])]  # fmt: skip
        ok = ok and not need
        return {"ok": ok, "files": len(man["files"]), "bad": bad[:20], "ledger_files": len(ledger),
                "journal_dump": dump, "row_counts": man.get("row_counts", {}),
                "missing_sources": need, "commit": man.get("commit", ""),
                "key_fp": man.get("key_fp", ""), "archive": archive.name,
                "restore_dir": str(tmp) if keep_dir else ""}  # fmt: skip
    finally:
        if not keep_dir:
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
    else:
        subprocess.run(["rclone", "copyto", str(path), f"{remote}/{path.name}"], check=True,
                       capture_output=True)  # fmt: skip
    if _remote_size(remote, path.name) != path.stat().st_size:  # review L4: checked upload
        raise OSError(f"uploaded {path.name} has a different size")


def _remote_size(remote: str, name: str) -> int | None:
    if remote.startswith("/"):
        p = Path(remote) / name
        return p.stat().st_size if p.is_file() else None
    r = subprocess.run(["rclone", "lsjson", f"{remote}/{name}"], check=True, capture_output=True,
                       text=True)  # fmt: skip
    items = json.loads(r.stdout or "[]")
    return int(items[0]["Size"]) if items else None


def _remote_delete(remote: str, name: str) -> None:
    if remote.startswith("/"):
        (Path(remote) / name).unlink(missing_ok=True)
        return
    subprocess.run(["rclone", "deletefile", f"{remote}/{name}"], check=True, capture_output=True)


def prune(names: Sequence[str], delete: Any, daily: int = DAILY, monthly: int = MONTHLY,
          now: datetime | None = None) -> list[str]:  # fmt: skip
    """Delete archives (and their manifests) retention does not keep; returns them.
    Future-dated names are left alone (review L1)."""
    kept = set(keep(names, daily, monthly, now))
    dated = set(_dated(names, now))
    gone = [n for n in names if n in dated and n not in kept]
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
        key = Path(plan["key_file"])
        res["key_fp"] = fingerprint(key)  # security review M3: shown with every result
        for part in out.glob("*.part"):  # review L4: leftovers of an interrupted run
            part.unlink(missing_ok=True)
        arch, man = make_archive(sources, out, recipient(key), {
            "row_counts": counts, "key_fp": res["key_fp"], "commit": plan.get("commit", ""),
            "required": [n for n, _ in plan["sources"]], "_key_file": str(key)})  # fmt: skip
        res["local"] = {"archive": arch.name, "size": man["size"], "files": len(man["files"])}
        if man["size"] > BIG:
            res["warn"] = f"archive is {man['size'] // (1024 * 1024)} MB (over 300 MB)"
        ld, lm = plan.get("local_keep", [LOCAL_DAILY, LOCAL_MONTHLY])
        names = sorted(x.name for x in out.iterdir())
        res["pruned_local"] = prune(names, lambda n: (out / n).unlink(missing_ok=True), ld, lm)
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


def main(argv: list[str]) -> int:  # noqa: PLR0911 - one return per command
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
        kd = "--keep" in argv
        args = [a for a in argv if a != "--keep"]
        v = verify(Path(args[2]), Path(args[3]), Path(args[4]) if len(args) > 4 else None, kd)
        print(json.dumps(v))
        return 0 if v["ok"] else 1
    if op == "keep":
        print("\n".join(keep(argv[2:])))
        return 0
    if op == "latest":
        d = Path(argv[2])
        n = latest(x.name for x in d.iterdir()) if d.is_dir() else None
        print(str(d / n) if n else "")
        return 0 if n else 1
    if op == "fingerprint":
        print(fingerprint(Path(argv[2])))
        return 0
    if op == "check-manifest":
        try:
            m = check_manifest(Path(argv[2]), Path(argv[3]))
        except (RuntimeError, OSError, ValueError) as e:
            print(json.dumps({"ok": False, "error": str(e)}))
            return 1
        print(
            json.dumps(
                {
                    "ok": True,
                    "commit": m.get("commit", ""),
                    "row_counts": m.get("row_counts", {}),
                    "created": m.get("created"),
                }
            )
        )
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
