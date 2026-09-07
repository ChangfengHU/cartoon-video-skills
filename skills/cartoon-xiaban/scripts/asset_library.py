#!/usr/bin/env python3
"""Private R2 asset records, feedback and frozen project selections (stdlib only).

No media search, listening, legal judgment, service provisioning beyond explicit
init, mutable shared index, deletion, or automatic brand/voice promotion.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

MAX_BYTES = 300_000_000
PREFIX = "xiaban/v1"
KINDS = {"image", "sfx", "voice", "bgm", "reference"}
SECRET_KEYS = {"apikey", "apitoken", "authorization", "accesstoken", "cookie", "password", "secret", "globalkey", "privatekey"}


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def clean_metadata(value):
    """Reject credential fields; free text still needs the caller's privacy review."""
    if isinstance(value, dict):
        for key, item in value.items():
            if re.sub(r"[^a-z]", "", key.lower()) in SECRET_KEYS:
                raise ValueError("Credential fields are forbidden in library metadata")
            clean_metadata(item)
    elif isinstance(value, list):
        for item in value:
            clean_metadata(item)


def relative(value):
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("Invalid relative path")
    parts = value.split("/")
    if any(p in {"", ".", ".."} for p in parts) or Path(value).is_absolute():
        raise ValueError("Unsafe relative path")
    return value


def local_source(root, name):
    root = Path(root).resolve(strict=True)
    path = (root / relative(name)).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("Source must be a file inside asset-root")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Object exceeds 300 MB REST limit")
    return path


def write_new(path, data):
    path = Path(path)
    # No symlink traversal in existing ancestors, including a dangling target.
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Symlink output is forbidden")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)


class APIError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__(f"Cloudflare request failed (HTTP {status}); credentials/body withheld")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise APIError(code)


class R2:
    def __init__(self, account, token, bucket):
        if not re.fullmatch(r"[a-fA-F0-9]{32}", account or "") or not token:
            raise ValueError("CF_ACCOUNT_ID and CF_API_TOKEN are required")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]", bucket or ""):
            raise ValueError("Invalid R2_BUCKET")
        self.bucket = bucket
        self.base = f"https://api.cloudflare.com/client/v4/accounts/{account}/r2/buckets"
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, method, suffix="", data=None, raw=False):
        headers = {"Authorization": f"Bearer {self.token}"}
        if data is not None:
            headers["Content-Type"] = "application/octet-stream" if "/objects/" in suffix else "application/json"
        req = urllib.request.Request(self.base + suffix, data=data, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=60) as response:
                body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise ValueError("Response exceeds 300 MB limit")
        except urllib.error.HTTPError as exc:
            raise APIError(exc.code) from None
        except urllib.error.URLError:
            raise RuntimeError("Cloudflare network request failed; no automatic retry") from None
        if raw:
            return body
        value = json.loads(body)
        if not value.get("success"):
            raise APIError("API unsuccessful")
        return value

    def private(self):
        managed = self.request("GET", f"/{self.bucket}/domains/managed")["result"]
        custom = self.request("GET", f"/{self.bucket}/domains/custom")["result"]
        domains = custom.get("domains") if isinstance(custom, dict) else custom
        if managed.get("enabled") is not False or not isinstance(domains, list) or domains:
            raise ValueError("Private library requires r2.dev disabled and no custom domains")
        return {"bucket": self.bucket, "r2_dev_enabled": False, "custom_domains": []}

    def init(self):
        # Exact read before creation; never modify an existing bucket's access policy.
        created = False
        try:
            self.request("GET", f"/{self.bucket}")
        except APIError as exc:
            if exc.status != 404:
                raise
            self.request("POST", data=encoded({"name": self.bucket, "storageClass": "Standard"}))
            created = True
        return {"created": created, **self.private()}

    def list(self, prefix):
        relative(prefix.rstrip("/"))
        cursor, seen, rows = None, set(), []
        while True:
            query = {"prefix": prefix, "per_page": 1000}
            if cursor:
                query["cursor"] = cursor
            response = self.request("GET", f"/{self.bucket}/objects?{urllib.parse.urlencode(query)}")
            page = response["result"]
            if not isinstance(page, list):
                raise ValueError("Unexpected object listing schema")
            rows.extend(page)
            info = response.get("result_info", {})
            if not info.get("is_truncated", False):
                return rows
            cursor = info.get("cursor")
            if not cursor or cursor in seen:
                raise ValueError("Truncated listing has missing/repeated cursor")
            seen.add(cursor)

    def get(self, key):
        relative(key)
        if not key.startswith(PREFIX + "/"):
            raise ValueError("Object outside library prefix")
        return self.request("GET", f"/{self.bucket}/objects/{urllib.parse.quote(key, safe='/')}", raw=True)

    def put_new(self, key, data):
        relative(key)
        if not key.startswith(PREFIX + "/") or len(data) > MAX_BYTES:
            raise ValueError("Invalid library object")
        if any(row.get("key") == key for row in self.list(key)):
            raise ValueError("Object already exists; overwrite refused")
        # REST has no documented CAS here. Unique UUID + hash keys, not a shared head,
        # avoid concurrent index replacement. The precheck is NOT an atomic lock.
        self.request("PUT", f"/{self.bucket}/objects/{urllib.parse.quote(key, safe='/')}", data=data)
        if sha(self.get(key)) != sha(data):
            raise ValueError("Uploaded object failed SHA256 verification")


def record_key(group, ident):
    if group not in {"records", "feedback", "indexes"} or not re.fullmatch(r"[0-9a-f]{32}-[0-9a-f]{64}", ident):
        raise ValueError("Invalid immutable record ID")
    return f"{PREFIX}/{group}/{ident}.json"


def append(store, group, value):
    data = encoded(value)
    ident = uuid.uuid4().hex + "-" + sha(data)
    store.put_new(record_key(group, ident), data)
    return ident


def load_record(store, group, ident):
    data = store.get(record_key(group, ident))
    if sha(data) != ident.split("-")[1]:
        raise ValueError("Record SHA256 mismatch")
    value = json.loads(data)
    clean_metadata(value)
    return value


def validate_card(card, has_file=False):
    clean_metadata(card)
    if card.get("schema_version") != 1 or card.get("kind") not in KINDS:
        raise ValueError("Unsupported asset card schema/kind")
    for field in ("title", "source_url", "source_type", "review_status", "use_cases"):
        if not card.get(field):
            raise ValueError(f"Missing {field}")
    if not isinstance(card["use_cases"], list) or not isinstance(card.get("tags", []), list):
        raise ValueError("use_cases/tags must be arrays")
    license_info = card.get("license", {})
    if not all(license_info.get(k) for k in ("status", "scope", "evidence")):
        raise ValueError("License status, scope and evidence required (unknown may be explicit)")
    if card.get("personal_reference") or card.get("voice_identity") == "user_clone":
        raise ValueError("Personal references and user-clone caches are not in this library workflow")
    if has_file:
        if license_info.get("archive_allowed") is not True or license_info["status"] not in {"user_authorized_generated", "verified_for_archive"}:
            raise ValueError("Binary archive requires verified archive rights")
        if card["kind"] == "voice" and card.get("voice_identity") != "provider_preset":
            raise ValueError("Only identified provider-preset voice output may be archived")
    if any(k in card for k in ("id", "object", "created_at")):
        raise ValueError("Object metadata is generated by the importer")


def add(store, card, root=None, filename=None):
    validate_card(card, bool(filename))
    store.private()
    record = {**card, "created_at": now(), "object": None}
    if filename:
        source = local_source(root, filename)
        data = source.read_bytes()
        checksum = sha(data)
        extension = source.suffix.lower()
        if not re.fullmatch(r"\.[a-z0-9]{1,10}", extension):
            extension = ".bin"
        key = f"{PREFIX}/blobs/{uuid.uuid4().hex}/{checksum}{extension}"
        store.put_new(key, data)
        record["object"] = {"key": key, "sha256": checksum, "size": len(data), "extension": extension}
    ident = append(store, "records", record)
    return {"id": ident, "record": record}


def feedback(store, value):
    clean_metadata(value)
    for field in ("asset_id", "project", "outcome", "reason", "reviewer", "observed_at"):
        if not value.get(field):
            raise ValueError(f"Feedback requires {field}")
    if value["outcome"] not in {"used", "rejected", "user_approved", "user_disliked", "technical_failure"}:
        raise ValueError("Unsupported feedback outcome")
    load_record(store, "records", value["asset_id"])
    store.private()
    return append(store, "feedback", {**value, "created_at": now()})


def index(store):
    records, notes = [], []
    for group, target in (("records", records), ("feedback", notes)):
        for row in store.list(f"{PREFIX}/{group}/"):
            key = row["key"]
            ident = key.rsplit("/", 1)[-1].removesuffix(".json")
            if key != record_key(group, ident):
                raise ValueError("Unexpected key in index namespace")
            target.append({"id": ident, **load_record(store, group, ident)})
    known = {r["id"] for r in records}
    if any(f["asset_id"] not in known for f in notes):
        raise ValueError("Feedback references missing record; refresh index after concurrent writes")
    return {"schema_version": 1, "created_at": now(), "records": sorted(records, key=lambda r: r["id"]),
            "feedback": sorted(notes, key=lambda r: r["id"]), "authority": "append-only records and feedback; this is a point-in-time derived view"}


def search(value, query="", kind=None):
    words = query.casefold().split()
    results = []
    for card in value["records"]:
        haystack = json.dumps({k: card.get(k) for k in ("title", "tags", "use_cases")}, ensure_ascii=False).casefold()
        if (not kind or card["kind"] == kind) and all(w in haystack for w in words):
            results.append({**card, "feedback": [f for f in value["feedback"] if f["asset_id"] == card["id"]]})
    return results


def download(store, card, destination):
    obj = card.get("object")
    if not obj:
        raise ValueError("Metadata-only source has no archived file")
    key = relative(obj["key"])
    if not key.startswith(PREFIX + "/blobs/") or not re.fullmatch(r"[a-f0-9]{64}", obj["sha256"]):
        raise ValueError("Invalid blob reference")
    data = store.get(key)
    if sha(data) != obj["sha256"] or len(data) != obj["size"]:
        raise ValueError("Downloaded file failed SHA256/size verification")
    write_new(destination, data)


def freeze(store, selection, output):
    clean_metadata(selection)
    for field in ("project", "story_intent", "platform", "selected"):
        if not selection.get(field):
            raise ValueError(f"Selection requires {field}")
    records, selected_ids = [], set()
    for item in selection["selected"]:
        ident = item["asset_id"]
        if ident in selected_ids:
            raise ValueError("Duplicate selected asset")
        selected_ids.add(ident)
        card = load_record(store, "records", ident)
        decision = item.get("project_review", {})
        if decision.get("status") != "verified_for_project" or selection["platform"] not in decision.get("allowed_platforms", []) or not decision.get("evidence") or not decision.get("checked_at"):
            raise ValueError("Each selected asset needs a fresh project-specific rights review")
        if not item.get("reason"):
            raise ValueError("Selected asset requires scene/use reason")
        records.append({"id": ident, **card, "selection": item})
    research = selection.get("new_music_research", {})
    if any(c["kind"] == "bgm" for c in records):
        if research.get("performed") is not True or not research.get("checked_at") or not research.get("queries") or not research.get("source_urls") or "new_candidates" not in research:
            raise ValueError("BGM reuse still requires recorded new music research")
        if not research["new_candidates"] and not research.get("no_new_candidate_reason"):
            raise ValueError("Explain why fresh research produced no new candidates")
    output = Path(output).absolute()
    if output.exists() or any(p.is_symlink() for p in (output, *output.parents)):
        raise ValueError("Snapshot output must be a new directory without symlink ancestors")
    store.private()
    output.mkdir(parents=True, exist_ok=False)
    files = []
    for card in records:
        obj = card.get("object")
        if obj:
            extension = obj["extension"]
            if not re.fullmatch(r"\.[a-z0-9]{1,10}", extension):
                raise ValueError("Invalid blob extension")
            name = f"assets/{card['id'][:32]}-{obj['sha256']}{extension}"
            download(store, card, output / name)
            files.append({"path": name, "sha256": obj["sha256"], "size": obj["size"]})
    lock = {"schema_version": 1, "created_at": now(), "bucket": store.bucket,
            "selection": selection, "records": records, "files": files,
            "note": "Private point-in-time selection. Metadata is not listening, legal judgment or brand approval."}
    write_new(output / "ASSET_LIBRARY_LOCK.json", encoded(lock))
    return {"output": str(output), "records": len(records), "files": len(files)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--auth-prompt", action="store_true", help="Read credential JSON with hidden TTY input; never a file or argv value")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Explicitly create an absent private bucket, then verify access policy")
    sub.add_parser("verify-private")
    a = sub.add_parser("add")
    a.add_argument("--card", type=Path, required=True)
    a.add_argument("--asset-root", type=Path)
    a.add_argument("--file")
    a = sub.add_parser("feedback")
    a.add_argument("--input", type=Path, required=True)
    a = sub.add_parser("index")
    a.add_argument("--output", type=Path, required=True)
    a.add_argument("--publish", action="store_true", help="Also append a uniquely named index snapshot")
    a = sub.add_parser("search")
    a.add_argument("--index", type=Path, required=True)
    a.add_argument("--query", default="")
    a.add_argument("--kind", choices=sorted(KINDS))
    a = sub.add_parser("download")
    a.add_argument("--id", required=True)
    a.add_argument("--output", type=Path, required=True)
    a = sub.add_parser("freeze")
    a.add_argument("--selection", type=Path, required=True)
    a.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        if args.command == "search":
            result = search(json.loads(args.index.read_text()), args.query, args.kind)
        else:
            account, token = os.environ.get("CF_ACCOUNT_ID"), os.environ.get("CF_API_TOKEN")
            if args.auth_prompt:
                if not sys.stdin.isatty():
                    raise ValueError("--auth-prompt requires a real TTY to prevent secret echo")
                config = json.loads(getpass.getpass("Cloudflare credential JSON (hidden): "))
                config = config.get("forwarding", config)
                account, token = config["accountId"], config["apiToken"]
            store = R2(account, token, os.environ.get("R2_BUCKET"))
            if args.command == "init":
                result = store.init()
            elif args.command == "verify-private":
                result = store.private()
            elif args.command == "add":
                result = add(store, json.loads(args.card.read_text()), args.asset_root, args.file)
            elif args.command == "feedback":
                result = {"feedback_id": feedback(store, json.loads(args.input.read_text()))}
            elif args.command == "index":
                result = index(store)
                write_new(args.output, encoded(result))
                record_id = None
                if args.publish:
                    store.private()
                    record_id = append(store, "indexes", result)
                result = {"output": str(args.output), "records": len(result["records"]), "feedback": len(result["feedback"]), "index_id": record_id}
            elif args.command == "download":
                store.private()
                download(store, load_record(store, "records", args.id), args.output)
                result = {"output": str(args.output), "verified": True}
            else:
                result = freeze(store, json.loads(args.selection.read_text()), args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, RuntimeError) as exc:
        # Do not include JSON decode fragments, URLs, paths, or credential values.
        safe = str(exc) if isinstance(exc, (ValueError, RuntimeError)) and not isinstance(exc, json.JSONDecodeError) else type(exc).__name__
        print(f"Asset library failed: {safe}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
