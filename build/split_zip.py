"""Split web/content.zip into parts small enough to publish, plus an index.

Usage (repo root; build/wasm.sh runs it):
    python3 -I build/split_zip.py web/content.zip [<max MiB per part>]

The site is published by pushing web/ to the gh-pages branch, and GitHub rejects any
file over 100 MiB, so one content.zip stops deploying once the game outgrows that.
This writes content-1.zip, content-2.zip, ... (each under the limit; default 90 MiB)
next to it and content.json listing them. web/main.js mounts every listed part over
the same folder; the parts never share a path, so the order doesn't matter.

Entries are copied in their original order with their original compression; a part
is closed before an entry would push it over the limit. content.zip itself is kept
for local tools (tools/dev/devmatch.mjs checks its date) but is not deployed.
"""
import json
import os
import sys
import zipfile


def split(src, max_bytes):
    out_dir = os.path.dirname(os.path.abspath(src))
    base = os.path.splitext(os.path.basename(src))[0]
    for f in os.listdir(out_dir):  # parts from an earlier build
        if f.startswith(base + "-") and f.endswith(".zip"):
            os.remove(os.path.join(out_dir, f))

    parts, cur, cur_size = [], None, 0
    with zipfile.ZipFile(src) as zin:
        for info in zin.infolist():
            need = info.compress_size + 200 + 2 * len(info.filename)  # headers, roughly
            if need > max_bytes:
                raise SystemExit("%s alone (%d bytes) exceeds the part limit" % (info.filename, info.compress_size))
            if cur is None or cur_size + need > max_bytes:
                if cur:
                    cur.close()
                name = "%s-%d.zip" % (base, len(parts) + 1)
                parts.append(name)
                cur, cur_size = zipfile.ZipFile(os.path.join(out_dir, name), "w"), 22
            data = zin.read(info)
            cur.writestr(info, data, compress_type=info.compress_type)
            cur_size += need
    if cur:
        cur.close()

    for name in parts:
        size = os.path.getsize(os.path.join(out_dir, name))
        if size > max_bytes:
            raise SystemExit("%s came out at %d bytes, over the limit" % (name, size))
    with open(os.path.join(out_dir, base + ".json"), "w") as f:
        json.dump({"parts": parts}, f)
        f.write("\n")
    for name in parts:
        print("    %s: %.1f MB" % (name, os.path.getsize(os.path.join(out_dir, name)) / 1e6))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    split(sys.argv[1], int(float(sys.argv[2]) * 1024 * 1024) if len(sys.argv) > 2 else 90 * 1024 * 1024)
