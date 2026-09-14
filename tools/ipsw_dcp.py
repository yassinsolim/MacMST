import argparse
import datetime
import hashlib
import io
import json
import pathlib
import plistlib
import re
import urllib.parse
import urllib.request
import zipfile


PRODUCT = "Mac17,2"
BUILD = "25G83"
VERSION = "26.6.2"
BOARD = "J704AP"
CPID = 0x8142
BDID = 0x22
MAX_MEMBER = 64 * 1024 * 1024
MAX_TRANSFER = 96 * 1024 * 1024


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def apple_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "updates.cdn-apple.com" or parsed.username or parsed.password:
        raise ValueError("Expected an official Apple HTTPS firmware URL")
    if parsed.port not in (None, 443) or parsed.fragment or parsed.query:
        raise ValueError("Unexpected firmware URL port, query or fragment")
    return url


class RemoteIPSW(io.RawIOBase):
    def __init__(self, url, size, opener=urllib.request.urlopen):
        super().__init__()
        self.url = apple_url(url)
        if type(size) is not int or not 22 <= size <= 64 * 1024 ** 3:
            raise ValueError("Invalid published IPSW size")
        self.size = size
        self.position = 0
        self.opener = opener
        self.requests = []
        self.transferred = 0
        self.validator = None

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        if whence not in (io.SEEK_SET, io.SEEK_CUR, io.SEEK_END) or type(offset) is not int:
            raise ValueError("Invalid range seek")
        position = offset + (self.position if whence == io.SEEK_CUR else self.size if whence == io.SEEK_END else 0)
        if not 0 <= position <= self.size:
            raise ValueError("Range seek outside IPSW")
        self.position = position
        return position

    def read(self, size=-1):
        if size == -1:
            size = self.size - self.position
        if type(size) is not int or size < 0 or size > 16 * 1024 * 1024:
            raise ValueError("Unbounded or excessive IPSW range read")
        size = min(size, self.size - self.position)
        if size == 0:
            return b""
        if len(self.requests) >= 256 or self.transferred + size > MAX_TRANSFER:
            raise ValueError("IPSW partial transfer budget exhausted")
        start, end = self.position, self.position + size - 1
        headers = {"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity", "User-Agent": "MacMST-static-firmware-research/1"}
        if self.validator:
            headers["If-Range"] = self.validator
        request = urllib.request.Request(self.url, headers=headers)
        receipt = {"started_utc": utc_now(), "range": headers["Range"], "body_bytes_read": 0}
        self.requests.append(receipt)
        with self.opener(request, timeout=30) as response:
            receipt.update(status=response.status, url=response.geturl(), headers=dict(response.headers.items()))
            apple_url(response.geturl())
            if response.status != 206:
                raise ValueError("Server did not honor Range; full IPSW download refused before reading body")
            if response.headers.get("Content-Range") != f"bytes {start}-{end}/{self.size}":
                raise ValueError("Incorrect Content-Range or changed archive size")
            if response.headers.get("Content-Encoding", "identity") != "identity":
                raise ValueError("Encoded HTTP range body is not supported")
            if response.headers.get("Content-Length") is not None and int(response.headers["Content-Length"]) != size:
                raise ValueError("Unexpected HTTP range body size")
            validator = response.headers.get("ETag")
            if validator and validator.startswith("W/"):
                validator = None
            validator = validator or response.headers.get("Last-Modified")
            if self.validator and validator != self.validator:
                raise ValueError("Remote IPSW validator changed during extraction")
            self.validator = validator
            raw = response.read(size + 1)
            self.transferred += len(raw)
            receipt.update(body_bytes_read=len(raw), completed_utc=utc_now(), sha256=sha256(raw))
            if len(raw) != size:
                raise ValueError("Truncated or excessive HTTP range body")
        self.position += size
        return raw


def extract_member(archive, name, limit=MAX_MEMBER):
    parsed = pathlib.PurePosixPath(name)
    if not name or parsed.is_absolute() or ".." in parsed.parts or "\\" in name or str(parsed) != name:
        raise ValueError("Invalid exact ZIP member path")
    matches = [entry for entry in archive.infolist() if entry.filename == name]
    if len(matches) != 1:
        raise ValueError("Missing or ambiguous ZIP member: " + name)
    entry = matches[0]
    if entry.is_dir() or entry.flag_bits & 1 or (entry.external_attr >> 16) & 0o170000 == 0o120000:
        raise ValueError("Encrypted, directory or symlink member is not supported")
    if not 0 < entry.file_size <= limit or not 0 < entry.compress_size <= MAX_MEMBER:
        raise ValueError("ZIP member exceeds bounded extraction size")
    if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        raise ValueError("Unsupported ZIP member compression")
    chunks = []
    with archive.open(entry) as stream:
        remaining = entry.file_size
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError("Truncated extracted member")
            chunks.append(chunk)
            remaining -= len(chunk)
        if stream.read(1):
            raise ValueError("Excess extracted member bytes")
    raw = b"".join(chunks)
    return raw, {"path": name, "compressed_size": entry.compress_size, "uncompressed_size": entry.file_size,
                 "zip_compression": entry.compress_type, "crc32_hex": hex(entry.CRC), "sha256": sha256(raw)}


def fetch_metadata(url):
    request = urllib.request.Request(url, headers={"Accept-Encoding": "identity", "User-Agent": "MacMST-static-firmware-research/1"})
    started = utc_now()
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200 or urllib.parse.urlsplit(response.geturl()).hostname != "api.ipsw.me":
            raise ValueError("Unexpected public firmware metadata response")
        raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Excessive metadata response")
        receipt = {"url": response.geturl(), "status": response.status, "started_utc": started,
                   "completed_utc": utc_now(), "body_bytes_read": len(raw), "sha256": sha256(raw)}
    return raw, receipt


def select_metadata(device, firmware):
    if device.get("identifier") != PRODUCT or firmware.get("identifier") != PRODUCT:
        raise ValueError("Public metadata ProductType mismatch")
    boards = [board for board in device.get("boards", []) if board.get("boardconfig", "").upper() == BOARD]
    if len(boards) != 1 or boards[0].get("platform", "").lower() != "t8142" or boards[0].get("cpid") != CPID or boards[0].get("bdid") != BDID:
        raise ValueError("Public board/CPID/BDID mapping mismatch or ambiguity")
    if firmware.get("buildid") != BUILD or firmware.get("version") != VERSION or firmware.get("signed") is not True:
        raise ValueError("Exact signed production build is not present in metadata")
    records = [entry for entry in device.get("firmwares", []) if entry.get("buildid") == BUILD]
    if len(records) != 1 or records[0] != firmware:
        raise ValueError("Device and build metadata disagree")
    apple_url(firmware["url"])
    if pathlib.PurePosixPath(urllib.parse.urlsplit(firmware["url"]).path).name != f"UniversalMac_{VERSION}_{BUILD}_Restore.ipsw":
        raise ValueError("Unexpected target IPSW filename")
    for name, length in (("sha1sum", 40), ("md5sum", 32), ("sha256sum", 64)):
        if firmware.get(name) and not re.fullmatch("[0-9a-fA-F]{" + str(length) + "}", firmware[name]):
            raise ValueError("Invalid published archive hash")
    return {"product_type": PRODUCT, "board_config": BOARD, "cpid_hex": hex(CPID), "bdid_hex": hex(BDID),
            "firmware": firmware, "signed_status_scope": "IPSW.me public metadata, not an independent Apple TSS authorization test",
            "whole_archive_hash_scope": "Published values retained; not locally verified because the full IPSW is not downloaded"}


def integer(value):
    if isinstance(value, str):
        return int(value, 0)
    if type(value) is not int:
        raise ValueError("Invalid manifest integer")
    return value


def json_value(value):
    if isinstance(value, bytes):
        return {"hex": value.hex(), "bytes": len(value)}
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_value(item) for item in value]
    return value


def select_identity(manifest, product=PRODUCT, board=BOARD, cpid=CPID, bdid=BDID):
    if manifest.get("ProductBuildVersion") != BUILD or manifest.get("ProductVersion") != VERSION:
        raise ValueError("Wrong manifest build/version")
    matches = []
    for index, identity in enumerate(manifest["BuildIdentities"]):
        info = identity.get("Info", {})
        if info.get("DeviceClass", "").upper() != board.upper():
            continue
        if identity.get("Ap,ProductType") != product or identity.get("Ap,Target", "").upper() != board.upper():
            continue
        if integer(identity.get("ApChipID")) != cpid or integer(identity.get("ApBoardID")) != bdid:
            continue
        if info.get("Variant") != "macOS Customer" or info.get("RestoreBehavior") != "Erase":
            continue
        if info.get("BuildNumber") != BUILD or info.get("VariantContents", {}).get("DCP") != "macOSProduction":
            continue
        matches.append((index, identity))
    if len(matches) != 1:
        raise ValueError("Missing or ambiguous exact production BuildIdentity")
    return matches[0]


def identity_receipt(index, identity):
    fields = {key: value for key, value in identity.items() if key in
              ("Ap,ProductType", "Ap,Target", "Ap,TargetType", "ApChipID", "ApBoardID", "ApSecurityDomain", "UniqueBuildID")}
    info = identity["Info"]
    fields["Info"] = {key: info[key] for key in ("DeviceClass", "Variant", "RestoreBehavior", "BuildNumber", "BuildTrain", "VariantContents") if key in info}
    return {"index": index, "fields": json_value(fields),
            "identity_binary_plist_sha256": sha256(plistlib.dumps(identity, fmt=plistlib.FMT_BINARY, sort_keys=True)),
            "display_components": {key: json_value(value) for key, value in identity["Manifest"].items()
                                   if re.search(r"dcp|display|devicetree", key + " " + value.get("Info", {}).get("Path", ""), re.IGNORECASE)}}


def resolve_mapping(manifest):
    index, identity = select_identity(manifest)
    components = {key: entry for key, entry in identity["Manifest"].items() if "dcp" in key.lower() and "restore" not in key.lower()}
    paths = {entry["Info"]["Path"] for entry in components.values()}
    if len(paths) != 1 or not components:
        raise ValueError("Normal DCP component path remains ambiguous")
    if any(entry.get("Trusted") is not True or not isinstance(entry.get("Digest"), bytes) or len(entry["Digest"]) != 48 for entry in components.values()):
        raise ValueError("DCP component lacks expected trusted SHA-384 digest")
    variants = [identity_receipt(position, candidate) for position, candidate in enumerate(manifest["BuildIdentities"])
                if candidate.get("Info", {}).get("DeviceClass", "").upper() == BOARD]
    comparison = []
    for board, cpid in (("j604ap", 0x8132), ("j714sap", 0x6050), ("j614sap", 0x6040)):
        candidates = [(position, candidate) for position, candidate in enumerate(manifest["BuildIdentities"])
                      if candidate.get("Info", {}).get("DeviceClass") == board and
                      integer(candidate.get("ApChipID")) == cpid and candidate["Info"].get("Variant") == "macOS Customer" and
                      candidate["Info"].get("RestoreBehavior") == "Erase"]
        if not candidates:
            comparison.append({"board": board, "cpid_hex": hex(cpid), "result": "IDENTITY_NOT_PRESENT"})
            continue
        if len(candidates) != 1:
            raise ValueError("Ambiguous cross-generation comparison identity")
        position, candidate = candidates[0]
        select_identity(manifest, candidate["Ap,ProductType"], board, cpid, integer(candidate["ApBoardID"]))
        comparison.append(identity_receipt(position, candidate))
    return {"result": "M5_DCP_FIRMWARE_PATH_RESOLVED", "selected": identity_receipt(index, identity),
            "dcp_path": next(iter(paths)), "normal_dcp_components": list(components),
            "devicetree_path": identity["Manifest"]["DeviceTree"]["Info"]["Path"],
            "selection_policy": "Offline macOS Customer / Erase with DCP macOSProduction; no erase or restore operation is performed",
            "j704_variants": variants, "comparison": comparison}


def m4_comparison_mapping(mapping):
    matches = [record for record in mapping["comparison"] if record.get("fields", {}).get("Ap,ProductType") == "Mac16,1"
               and record["fields"].get("Ap,Target", "").upper() == "J604AP"
               and integer(record["fields"].get("ApChipID")) == 0x8132
               and integer(record["fields"].get("ApBoardID")) == 0x22]
    if len(matches) != 1:
        raise ValueError("Missing or ambiguous exact M4 comparison identity")
    selected = matches[0]
    components = {key: value for key, value in selected["display_components"].items()
                  if "dcp" in key.lower() and "restore" not in key.lower()}
    paths = {entry["Info"]["Path"] for entry in components.values()}
    if len(paths) != 1:
        raise ValueError("Ambiguous M4 comparison DCP component")
    return {"result": "M4_COMPARISON_FIRMWARE_PATH_RESOLVED", "selected": selected,
            "dcp_path": next(iter(paths)), "normal_dcp_components": list(components),
            "devicetree_path": None, "purpose": "SAME_BUILD_M4_COMPARISON_ONLY_NOT_M5_FIRMWARE",
            "m5_identity_digest": mapping["selected"]["identity_binary_plist_sha256"]}


def main():
    parser = argparse.ArgumentParser(description="M3B exact-build manifest extraction using bounded HTTP ranges; no restore or firmware execution.")
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--manifest-directory", type=pathlib.Path)
    parser.add_argument("--comparison-m4", action="store_true")
    args = parser.parse_args()
    if args.comparison_m4 and not args.manifest_directory:
        parser.error("M4 comparison requires the retained verified M5 build manifest")
    repository = pathlib.Path(__file__).resolve().parents[1]
    root = (repository / "artifacts/sources/m3b").resolve()
    output = args.output.resolve()
    if not output.is_relative_to(root) or output == root or output.exists():
        parser.error("output must be a new directory under artifacts/sources/m3b")
    output.mkdir(parents=True)
    report = {"schema_version": 1, "started_utc": utc_now(), "tool_sha256": sha256(pathlib.Path(__file__).read_bytes()),
              "safety": "Public metadata and bounded Apple CDN range reads only; no full IPSW, restore, firmware execution or private display operation",
              "metadata_requests": [], "archive_requests": [], "members": [], "errors": []}
    remote = None
    try:
        documents = {}
        if args.manifest_directory:
            source = args.manifest_directory.resolve()
            if not source.is_relative_to(root):
                raise ValueError("Manifest inputs must be retained under artifacts/sources/m3b")
            previous = json.loads((source / "extraction.json").read_bytes())
            for label in ("device", "build"):
                raw = (source / (label + ".json")).read_bytes()
                if not any(receipt["sha256"] == sha256(raw) for receipt in previous["metadata_requests"]):
                    raise ValueError("Retained public metadata hash mismatch")
                documents[label] = json.loads(raw)
            raw = (source / "BuildManifest.plist").read_bytes()
            if not any(member["path"] == "BuildManifest.plist" and member["sha256"] == sha256(raw) for member in previous["members"]):
                raise ValueError("Retained manifest hash mismatch")
            manifest = plistlib.loads(raw)
            report["manifest_sha256"] = sha256(raw)
            report["manifest_receipt_sha256"] = sha256((source / "extraction.json").read_bytes())
            report["mapping"] = resolve_mapping(manifest)
            if args.comparison_m4:
                report["mapping"] = m4_comparison_mapping(report["mapping"])
        else:
            for label, url in (("device", f"https://api.ipsw.me/v4/device/{PRODUCT}?type=ipsw"),
                               ("build", f"https://api.ipsw.me/v4/ipsw/{PRODUCT}/{BUILD}")):
                raw, receipt = fetch_metadata(url)
                report["metadata_requests"].append(receipt)
                with (output / (label + ".json")).open("xb") as stream:
                    stream.write(raw)
                documents[label] = json.loads(raw)
        report["target"] = select_metadata(documents["device"], documents["build"])
        firmware = documents["build"]
        remote = RemoteIPSW(firmware["url"], firmware["filesize"])
        with zipfile.ZipFile(remote) as archive:
            report["zip_member_count"] = len(archive.infolist())
            names = [report["mapping"]["devicetree_path"], report["mapping"]["dcp_path"]] if args.manifest_directory else ["BuildManifest.plist"]
            if args.comparison_m4:
                names = [report["mapping"]["dcp_path"]]
            for name in names:
                raw, member = extract_member(archive, name)
                destination = output / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb") as stream:
                    stream.write(raw)
                report["members"].append(member)
                if name == "BuildManifest.plist":
                    manifest = plistlib.loads(raw)
        if manifest.get("ProductBuildVersion") != BUILD or manifest.get("ProductVersion") != VERSION or PRODUCT not in manifest.get("SupportedProductTypes", []):
            raise ValueError("Apple BuildManifest does not match requested product/build/version")
        report["manifest_identity_count"] = len(manifest["BuildIdentities"])
        report["result"] = "IDENTIFIED_DCP_AND_DEVICETREE_EXTRACTED" if args.manifest_directory else "EXACT_BUILD_MANIFEST_EXTRACTED_MAPPING_NOT_YET_SELECTED"
        if args.comparison_m4:
            report["result"] = "IDENTIFIED_M4_COMPARISON_DCP_EXTRACTED"
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        report["errors"].append(str(error))
        report["result"] = "M5_DCP_FIRMWARE_PATH_UNRESOLVED"
    finally:
        if remote:
            report["archive_requests"] = remote.requests
            report["archive_body_bytes_read"] = remote.transferred
        report["completed_utc"] = utc_now()
        with (output / "extraction.json").open("x") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    print(json.dumps({"output": str(args.output), "result": report["result"], "errors": report["errors"],
                      "archive_body_bytes_read": report.get("archive_body_bytes_read", 0)}))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()