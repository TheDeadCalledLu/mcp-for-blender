"""Build the release artifacts for the fork.

Produces:
  dist/mcp-for-blender-addon-<ver>.zip   (Blender "Install from Disk" package)
  dist/mcp-for-blender-addon-<ver>.zip.sha256
  dist/RELEASE_NOTES.md
"""
import hashlib
import re
import zipfile
from pathlib import Path

ROOT = Path(r"d:\mrlu\code\blender\blender-mcp")
SRC = ROOT / "addon.py"
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)

text = SRC.read_text(encoding="utf-8")
ver = ".".join(re.search(r'"version":\s*\((\d+),\s*(\d+)\)', text).groups())
proto = re.search(r"ADDON_PROTOCOL_VERSION\s*=\s*(\d+)", text).group(1)

# --- zip (addon.py at the root, DEFLATE) --------------------------------
zip_path = DIST / f"mcp-for-blender-addon-{ver}.zip"
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    info = zipfile.ZipInfo("addon.py")
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    z.writestr(info, SRC.read_bytes())

# --- verify -------------------------------------------------------------
with zipfile.ZipFile(zip_path) as z:
    names = z.namelist()
    bad = z.testzip()
    raw = sum(i.file_size for i in z.infolist())
assert names == ["addon.py"], names
assert bad is None, bad

digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
sha_path = DIST / f"mcp-for-blender-addon-{ver}.zip.sha256"
sha_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8", newline="\n")

# --- release notes ------------------------------------------------------
notes = f"""# MCP for Blender — fork release {ver}

Addon version **{ver}** (protocol {proto}), based on upstream `mcp-for-blender` {ver}.

## Install

1. Download `mcp-for-blender-addon-{ver}.zip`.
2. Blender: **Edit > Preferences > Add-ons > Install from Disk…** and pick the zip.
3. Enable **Interface: MCP for Blender**.
4. The embedded MCP server starts automatically on `http://localhost:9877/mcp`.

## What this fork adds

- **Embedded MCP server (Streamable HTTP, port 9877)** — no agent-side process needed.
- **Async tasks + polling** — long renders/scripts avoid the client's ~60s request
  timeout. Start with `async=true`, poll `get_task_status`.
- **`request_id` idempotency** — a retried call is deduplicated.
- **`render_scene` tool** — renders from the camera and returns the image, so the
  model can see lighting, materials and framing even when the viewport is hidden.
- **Busy guard (fail-open)** — requests fail fast while Blender is rendering.
- **Tool annotations** — `readOnlyHint` / `destructiveHint`.
- **Endpoint self-heal** — the servers restart after a file load if they stop.

## Verification

- `addon.py` compiles cleanly.
- 25 MCP tools exposed; annotations present.
- Live-tested against Blender 5.2: `get_scene_info`, `execute_blender_code`
  (with traceback), `render_scene` (sync + async), `get_task_status`,
  `cancel_task`, `request_id` dedup, busy guard (0.01s fast-fail),
  endpoint self-heal after `read_homefile`, and upstream features
  (`get_addon_info`, `export_scene`).

## Checksums

```
{digest}  {zip_path.name}
```
"""
notes_path = DIST / "RELEASE_NOTES.md"
notes_path.write_text(notes, encoding="utf-8", newline="\n")

print("version:", ver, "protocol:", proto)
print("zip:", zip_path.name, zip_path.stat().st_size, "bytes")
print("raw:", raw, "bytes")
print("sha256:", digest)
print("notes:", notes_path.name)
