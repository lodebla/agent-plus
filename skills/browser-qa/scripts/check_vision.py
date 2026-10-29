#!/usr/bin/env python3
"""Check whether the active model accepts image input."""

import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import sqlite3
import struct
import subprocess
import sys
import time
import zlib
from pathlib import Path


EXIT_CODES = {"yes": 0, "no": 1, "unknown": 2}
SESSION_MAX_AGE_SECONDS = 3600
PROBE_TTL_SECONDS = 300
PROBE_CODE_LENGTH = 8
PROBE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
PROBE_WIDTH = 960
PROBE_HEIGHT = 180
PROBE_PNG_MAX_BYTES = 2 * 1024 * 1024

_FONT = {
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}


def _png_chunk(chunk_type, data):
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def _render_probe_png(answer):
    """Render a high-contrast RGB PNG using only the standard library."""
    scale = 14
    gap = 12
    text_width = len(answer) * 5 * scale + (len(answer) - 1) * gap
    origin_x = (PROBE_WIDTH - text_width) // 2
    origin_y = (PROBE_HEIGHT - 7 * scale) // 2
    rows = []
    for y in range(PROBE_HEIGHT):
        row = bytearray([255]) * (PROBE_WIDTH * 3)
        for index, char in enumerate(answer):
            glyph = _FONT[char]
            char_x = origin_x + index * (5 * scale + gap)
            for glyph_y, glyph_row in enumerate(glyph):
                pixel_y = origin_y + glyph_y * scale
                if not pixel_y <= y < pixel_y + scale:
                    continue
                for glyph_x, filled in enumerate(glyph_row):
                    if filled == "1":
                        pixel_x = char_x + glyph_x * scale
                        for scaled_x in range(pixel_x, pixel_x + scale):
                            offset = scaled_x * 3
                            row[offset : offset + 3] = b"\x18\x24\x35"
        rows.append(b"\x00" + row)

    header = struct.pack(">2I5B", PROBE_WIDTH, PROBE_HEIGHT, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(b"".join(rows), level=9))
        + _png_chunk(b"IEND", b"")
    )


def _artifact_directory(directory, create=False):
    """Resolve a directory strictly below this workspace's .artifacts folder."""
    workspace = Path.cwd().resolve()
    artifact_root = workspace / ".artifacts"
    supplied = Path(directory)
    if ".." in supplied.parts:
        raise ValueError("path traversal is not allowed")

    if artifact_root.is_symlink():
        raise ValueError("artifact root must not be a symlink")
    if create:
        artifact_root.mkdir(mode=0o700, exist_ok=True)
    if not artifact_root.is_dir():
        raise ValueError("artifact root is unavailable")

    candidate = supplied if supplied.is_absolute() else workspace / supplied
    candidate = Path(os.path.abspath(candidate))
    try:
        relative = candidate.relative_to(artifact_root)
    except ValueError as error:
        raise ValueError("probe path must be inside .artifacts") from error

    current = artifact_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("probe path must not contain symlinks")
        if current.exists():
            if not current.is_dir():
                raise ValueError("probe path must contain directories only")
        elif create:
            current.mkdir(mode=0o700)
        else:
            raise ValueError("probe directory is missing")
    return candidate


def _write_exclusive(path, contents):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(contents)
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def create_probe(directory, now=None):
    """Create a short-lived image challenge and return its paths (never its code)."""
    parent = _artifact_directory(directory, create=True)
    current_time = int(time.time() if now is None else now)
    for _ in range(8):
        challenge_dir = parent / f"vision-probe-{secrets.token_hex(12)}"
        try:
            challenge_dir.mkdir(mode=0o700)
            break
        except FileExistsError:
            continue
    else:
        raise ValueError("could not allocate a unique probe directory")

    answer = "".join(secrets.choice(PROBE_ALPHABET) for _ in range(PROBE_CODE_LENGTH))
    salt = secrets.token_hex(32)
    image_data = _render_probe_png(answer)
    metadata = {
        "created_at": current_time,
        "expires_at": current_time + PROBE_TTL_SECONDS,
        "format": 1,
        "hash": hashlib.sha256(bytes.fromhex(salt) + answer.encode("ascii")).hexdigest(),
        "image": "probe.png",
        "image_hash": hashlib.sha256(image_data).hexdigest(),
        "salt": salt,
    }
    metadata_data = json.dumps(metadata, separators=(",", ":"), sort_keys=True).encode("utf-8")
    image_path = challenge_dir / "probe.png"
    metadata_path = challenge_dir / "probe.json"
    image_created = False
    metadata_created = False
    try:
        _write_exclusive(image_path, image_data)
        image_created = True
        _write_exclusive(metadata_path, metadata_data)
        metadata_created = True
    except Exception:
        for path, created in (
            (image_path, image_created),
            (metadata_path, metadata_created),
        ):
            if not created:
                continue
            try:
                path.unlink()
            except OSError:
                pass
        try:
            challenge_dir.rmdir()
        except OSError:
            pass
        raise
    return challenge_dir, image_path, metadata_path


def _validate_probe_png(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) > PROBE_PNG_MAX_BYTES:
        return False
    offset = 8
    compressed = bytearray()
    saw_header = False
    saw_end = False
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            return False
        contents = data[offset + 8 : offset + 8 + length]
        checksum = struct.unpack(">I", data[offset + 8 + length : end])[0]
        if zlib.crc32(chunk_type + contents) & 0xFFFFFFFF != checksum:
            return False
        if chunk_type == b"IHDR":
            if saw_header or length != 13:
                return False
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">2I5B", contents
            )
            if (width, height, bit_depth, color_type, compression, filtering, interlace) != (
                PROBE_WIDTH,
                PROBE_HEIGHT,
                8,
                2,
                0,
                0,
                0,
            ):
                return False
            saw_header = True
        elif chunk_type == b"IDAT":
            if not saw_header or saw_end:
                return False
            compressed.extend(contents)
        elif chunk_type == b"IEND":
            if length != 0:
                return False
            saw_end = True
            offset = end
            break
        offset = end

    if not saw_header or not saw_end or offset != len(data):
        return False
    expected_size = (PROBE_WIDTH * 3 + 1) * PROBE_HEIGHT
    decompressor = zlib.decompressobj()
    raw = decompressor.decompress(bytes(compressed), expected_size + 1)
    row_size = PROBE_WIDTH * 3 + 1
    return (
        len(raw) == expected_size
        and decompressor.eof
        and not decompressor.unused_data
        and all(raw[row * row_size] == 0 for row in range(PROBE_HEIGHT))
    )


def verify_probe(directory, answer, now=None):
    """Return whether the supplied answer matches a valid, unexpired local probe."""
    try:
        challenge_dir = _artifact_directory(directory)
        metadata_path = challenge_dir / "probe.json"
        image_path = challenge_dir / "probe.png"
        if metadata_path.is_symlink() or image_path.is_symlink():
            return False
        if not metadata_path.is_file() or not image_path.is_file():
            return False
        if metadata_path.stat().st_size > 4096 or image_path.stat().st_size > PROBE_PNG_MAX_BYTES:
            return False
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        image_data = image_path.read_bytes()
        if (
            not isinstance(metadata, dict)
            or type(metadata.get("format")) is not int
            or metadata.get("format") != 1
        ):
            return False
        if metadata.get("image") != "probe.png" or not _validate_probe_png(image_data):
            return False
        image_hash = metadata.get("image_hash")
        if not isinstance(image_hash, str) or not hmac.compare_digest(
            image_hash, hashlib.sha256(image_data).hexdigest()
        ):
            return False

        salt = metadata.get("salt")
        digest = metadata.get("hash")
        created_at = metadata.get("created_at")
        expires_at = metadata.get("expires_at")
        if (
            not isinstance(salt, str)
            or not re.fullmatch(r"[0-9a-f]{64}", salt)
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or type(created_at) is not int
            or type(expires_at) is not int
        ):
            return False
        current_time = int(time.time() if now is None else now)
        if (
            created_at > current_time + 30
            or expires_at <= current_time
            or expires_at <= created_at
            or expires_at - created_at > PROBE_TTL_SECONDS
        ):
            return False
        if not isinstance(answer, str) or not re.fullmatch(
            f"[{re.escape(PROBE_ALPHABET)}]{{{PROBE_CODE_LENGTH}}}", answer.upper()
        ):
            return False
        actual = hashlib.sha256(bytes.fromhex(salt) + answer.upper().encode("ascii")).hexdigest()
        return hmac.compare_digest(digest, actual)
    except (OSError, ValueError, TypeError, UnicodeError, json.JSONDecodeError, zlib.error, struct.error):
        return False


def choose_model(cli_model, environ, kilo_model=None):
    return cli_model or environ.get("BROWSER_QA_MODEL") or kilo_model


def find_recent_kilo_model(database_path, directory, now=None):
    """Return a recent, unambiguous model from the current Kilo workspace."""
    path = Path(database_path)
    if not path.is_file():
        return None

    current_time = time.time() * 1000 if now is None else now
    unit = 1000 if current_time > 100_000_000_000 else 1
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=1) as connection:
            rows = connection.execute(
                "SELECT directory, model, time_updated FROM session "
                "WHERE time_updated >= ? ORDER BY time_updated DESC",
                (current_time - SESSION_MAX_AGE_SECONDS * unit,),
            ).fetchall()
    except (sqlite3.Error, OSError):
        return None

    target_directory = os.path.normcase(os.path.realpath(directory))
    workspace_sessions = [
        row for row in rows if os.path.normcase(os.path.realpath(row[0])) == target_directory
    ]
    if len(workspace_sessions) != 1:
        return None

    try:
        model = json.loads(workspace_sessions[0][1])
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(model, dict):
        return None
    provider = model.get("providerID")
    model_id = model.get("id") or model.get("modelID")
    if not isinstance(provider, str) or not isinstance(model_id, str) or not provider or not model_id:
        return None
    return model_id if model_id.startswith(provider + "/") else f"{provider}/{model_id}"


def parse_jsonc(text):
    """Parse JSON with line comments, block comments, and trailing commas."""
    output = []
    index = 0
    in_string = False
    escaped = False

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and next_char == "*":
            end = text.find("*/", index + 2)
            if end == -1:
                raise ValueError("unterminated JSONC block comment")
            index = end + 2
            continue
        if char == ",":
            following = index + 1
            while following < len(text) and text[following].isspace():
                following += 1
            if following < len(text) and text[following] in "}]":
                index += 1
                continue

        output.append(char)
        index += 1

    return json.loads("".join(output))


def parse_kilo_config(text):
    data = parse_jsonc(text)
    configured_models = {}
    providers = data.get("provider", {}) if isinstance(data, dict) else {}
    if not isinstance(providers, dict):
        return configured_models

    for provider_id, provider in providers.items():
        if not isinstance(provider, dict):
            continue
        models = provider.get("models", {})
        if not isinstance(models, dict):
            continue
        for model_id, model in models.items():
            if isinstance(model, dict) and isinstance(model.get("modalities"), dict):
                configured_models[f"{provider_id}/{model_id}"] = model
    return configured_models


def parse_kilo_verbose(text):
    """Read the JSON model records printed by `kilo models --verbose`."""
    decoder = json.JSONDecoder()
    models = []
    index = 0
    while True:
        start = text.find("{", index)
        if start == -1:
            break
        try:
            value, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(value, dict) and isinstance(value.get("id"), str):
            models.append(value)
        index = end
    return models


def _model_keys(model_id, provider=None):
    keys = {model_id.casefold()}
    if provider and not model_id.casefold().startswith(provider.casefold() + "/"):
        keys.add(f"{provider}/{model_id}".casefold())
    return keys


def _input_modalities(metadata):
    if not isinstance(metadata, dict):
        return None
    direct_inputs = metadata.get("input")
    if isinstance(direct_inputs, list):
        return {item.casefold() for item in direct_inputs if isinstance(item, str)}
    capabilities = metadata.get("capabilities")
    if isinstance(capabilities, dict):
        inputs = capabilities.get("input")
        if isinstance(inputs, dict) and isinstance(inputs.get("image"), bool):
            return {"image"} if inputs["image"] else set()
    modalities = metadata.get("modalities")
    if isinstance(modalities, dict) and isinstance(modalities.get("input"), list):
        return {item.casefold() for item in modalities["input"] if isinstance(item, str)}
    return None


def resolve_vision(model_id, catalog, configured_models, input_modalities=None):
    if input_modalities is not None:
        modalities = {
            item.casefold() for item in input_modalities if isinstance(item, str) and item.strip()
        }
        if not modalities:
            return "unknown"
        return "yes" if "image" in modalities else "no"
    if not model_id:
        return "unknown"

    target = model_id.casefold()
    verdicts = []
    for model in catalog:
        model_name = model.get("id") or model.get("modelID")
        provider = model.get("providerID") or model.get("provider")
        if not isinstance(model_name, str):
            continue
        if target not in _model_keys(model_name, provider):
            continue
        modalities = _input_modalities(model)
        if modalities is not None:
            verdicts.append("yes" if "image" in modalities else "no")

    for configured_id, metadata in configured_models.items():
        if configured_id.casefold() != target:
            continue
        modalities = _input_modalities(metadata)
        if modalities is not None:
            verdicts.append("yes" if "image" in modalities else "no")

    if not verdicts or len(set(verdicts)) != 1:
        return "unknown"
    return verdicts[0]


def _kilo_database_path(environ):
    if environ.get("KILO_DB_PATH"):
        configured_path = Path(environ["KILO_DB_PATH"])
        if configured_path.is_file():
            return configured_path

    default_path = Path.home() / ".local" / "share" / "kilo" / "kilo.db"
    if default_path.is_file():
        return default_path

    executable = shutil.which("kilo")
    candidates = []
    if executable:
        try:
            result = subprocess.run(
                [executable, "db", "path"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            candidates.extend(
                Path(line.strip())
                for line in result.stdout.splitlines()
                if line.strip().startswith(("/", "\\")) or re.match(r"^[A-Za-z]:\\", line.strip())
            )
        except (OSError, subprocess.TimeoutExpired):
            pass

    return next((path for path in candidates if path.is_file()), None)


def _is_kilo_runtime(environ):
    return bool(
        environ.get("KILO_RUN_ID")
        or environ.get("KILO_APP_NAME") == "kilo-code"
        or environ.get("KILOCODE_FEATURE")
    )


def _configured_kilo_models(directory):
    paths = [
        Path.home() / ".config" / "kilo" / "kilo.jsonc",
        directory / "kilo.jsonc",
        directory / ".kilo" / "kilo.jsonc",
    ]
    models = {}
    for path in paths:
        try:
            models.update(parse_kilo_config(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return models


def _kilo_models(model_id, environ):
    executable = shutil.which("kilo")
    if not executable:
        tree_sitter = environ.get("KILO_TREE_SITTER_WASM_DIR")
        if tree_sitter:
            bundled = Path(tree_sitter).parent / "kilo"
            if bundled.is_file():
                executable = str(bundled)
    if not executable or "/" not in model_id:
        return []

    provider = model_id.split("/", 1)[0]
    try:
        result = subprocess.run(
            [executable, "models", provider, "--verbose"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    return parse_kilo_verbose(result.stdout)


def _input_modalities_from_env(environ):
    value = environ.get("BROWSER_QA_MODEL_INPUT_MODALITIES")
    if value is None:
        return None
    modalities = [item.casefold() for item in re.split(r"[,\s]+", value.strip()) if item]
    return modalities or None


def _parse_modalities_argument(value):
    if value is None:
        return None
    return [item.casefold() for item in re.split(r"[,\s]+", value.strip()) if item]


def _print_verdict(verdict, message=None):
    print(f"VISION={verdict}")
    if message:
        print(message, file=sys.stderr)
    return EXIT_CODES[verdict]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check whether the active model accepts image input.")
    parser.add_argument("--model", help="active model ID in provider/model format")
    parser.add_argument(
        "--input-modalities",
        help="explicit active-harness input modalities, comma-separated or quoted space-separated",
    )
    probe_group = parser.add_mutually_exclusive_group()
    probe_group.add_argument("--create-probe", metavar="DIRECTORY")
    probe_group.add_argument("--verify-probe", metavar="DIRECTORY")
    parser.add_argument("--answer", help="code read from the probe image")
    args = parser.parse_args(argv)
    environ = os.environ

    if args.create_probe and args.answer is not None:
        parser.error("--answer is only valid with --verify-probe")
    if args.verify_probe and args.answer is None:
        parser.error("--verify-probe requires --answer")
    if args.answer is not None and not args.verify_probe:
        parser.error("--answer is only valid with --verify-probe")

    if args.create_probe:
        try:
            challenge_dir, image_path, metadata_path = create_probe(args.create_probe)
        except (OSError, ValueError):
            return _print_verdict("unknown", "Could not create a probe inside .artifacts.")
        print(f"PROBE_DIRECTORY={challenge_dir}")
        print(f"PROBE_IMAGE={image_path}")
        print(f"PROBE_METADATA={metadata_path}")
        return EXIT_CODES["yes"]

    if args.verify_probe:
        if verify_probe(args.verify_probe, args.answer):
            return _print_verdict(
                "yes",
                "The supplied answer matches the image probe in this session; it does not identify a provider model.",
            )
        return _print_verdict(
            "unknown",
            "The local image probe could not be verified; this does not establish model capability.",
        )

    input_modalities = (
        _parse_modalities_argument(args.input_modalities)
        if args.input_modalities is not None
        else _input_modalities_from_env(environ)
    )
    model_id = choose_model(args.model, environ)
    directory = Path.cwd()
    if not model_id and input_modalities is None and _is_kilo_runtime(environ):
        database = _kilo_database_path(environ)
        if database:
            model_id = find_recent_kilo_model(database, directory)

    configured_models = _configured_kilo_models(directory) if model_id and input_modalities is None else {}
    catalog = _kilo_models(model_id, environ) if model_id and input_modalities is None else []
    verdict = resolve_vision(
        model_id,
        catalog,
        configured_models,
        input_modalities=input_modalities,
    )
    reasons = {
        "yes": "The active model or explicit harness metadata confirms image input.",
        "no": "The active model metadata says image input is not supported.",
        "unknown": "The active model or its image-input metadata could not be verified.",
    }
    return _print_verdict(verdict, reasons[verdict])


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print("VISION=unknown")
        print("Vision check failed; no capability was established.", file=sys.stderr)
        sys.exit(EXIT_CODES["unknown"])
