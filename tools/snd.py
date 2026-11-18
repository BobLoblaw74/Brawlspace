"""Read and write MUGEN/Ikemen .snd sound files (ElecbyteSnd v4: WAV entries keyed by
group,index).

Usage (repo root):
    python3 -I tools/snd.py list <file.snd>
    python3 -I tools/snd.py build <base.snd> <out.snd> [<group>_<index>.wav ...]
    python3 -I tools/snd.py prep <any audio file> <out.wav>

`build` copies base.snd and adds each WAV under the group,index in its file name,
replacing an entry with that key if base.snd has one. Fighters use it through
tools/fighters/assemble.py (WAVs in tools/fighters/<id>/sounds/).

`prep` turns a recording (m4a, mp3, wav, ...; converted with macOS's afconvert) into a
game-ready WAV: mono 16-bit 44.1 kHz, leading/trailing silence trimmed, peak normalised
to KFM's sound level, with a short fade-out.
"""
import io
import os
import re
import struct
import subprocess
import sys
import tempfile
import wave

SIG = b"ElecbyteSnd\x00"
HEADER = 512  # signature, version, count, first offset, then a comment, zero-padded
SUB = 16      # next offset, length, group, index


def read(path):
    """-> (header bytes, [(group, index, wav bytes), ...]) in file order."""
    with open(path, "rb") as f:
        d = f.read()
    if d[:12] != SIG:
        raise SystemExit("%s: not an ElecbyteSnd file" % path)
    n, off = struct.unpack_from("<II", d, 16)
    entries = []
    for _ in range(n):
        nxt, ln, g, i = struct.unpack_from("<IIii", d, off)
        entries.append((g, i, d[off + SUB:off + SUB + ln]))
        off = nxt
    return d[:HEADER], entries


def write(path, header, entries):
    out = bytearray(header[:HEADER].ljust(HEADER, b"\0"))
    struct.pack_into("<II", out, 16, len(entries), HEADER if entries else 0)
    for g, i, wav in entries:
        nxt = len(out) + SUB + len(wav)  # the last one points at the end of the file, as KFM's do
        out += struct.pack("<IIii", nxt, len(wav), g, i) + wav
    with open(path, "wb") as f:
        f.write(out)


def key_of(wav_path):
    m = re.match(r"^(-?\d+)_(\d+)\.wav$", os.path.basename(wav_path), re.I)
    if not m:
        raise SystemExit("%s: name it <group>_<index>.wav" % wav_path)
    return int(m.group(1)), int(m.group(2))


def build(base, out, wavs):
    header, entries = read(base)
    for path in wavs:
        g, i = key_of(path)
        with open(path, "rb") as f:
            data = f.read()
        wave.open(io.BytesIO(data)).close()  # must be a readable WAV
        entries = [e for e in entries if (e[0], e[1]) != (g, i)] + [(g, i, data)]
    write(out, header, entries)


PEAK = 22000      # KFM's sounds peak around 19-24k of 32767
SILENT = 600      # samples quieter than this count as silence when trimming
LEAD_MS, TAIL_MS, FADE_MS = 10, 40, 30


def prep(src, out):
    with tempfile.TemporaryDirectory() as tmp:
        raw = os.path.join(tmp, "raw.wav")
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@44100", "-c", "1", src, raw], check=True)
        with wave.open(raw) as w:
            sr = w.getframerate()
            x = list(struct.unpack("<%dh" % w.getnframes(), w.readframes(w.getnframes())))
    loud = [k for k, v in enumerate(x) if abs(v) > SILENT]
    if not loud:
        raise SystemExit("%s: silent" % src)
    a = max(0, loud[0] - sr * LEAD_MS // 1000)
    b = min(len(x), loud[-1] + sr * TAIL_MS // 1000)
    x = x[a:b]
    gain = PEAK / max(abs(v) for v in x)
    fade = sr * FADE_MS // 1000
    y = []
    for k, v in enumerate(x):
        f = min(1.0, (len(x) - k) / fade)
        y.append(max(-32768, min(32767, int(round(v * gain * f)))))
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(struct.pack("<%dh" % len(y), *y))
    print("%s: %.2fs (trimmed %.2fs from the start), gain x%.2f" % (out, len(y) / sr, a / sr, gain))


def main(argv):
    if len(argv) >= 2 and argv[0] == "list":
        for g, i, wav in read(argv[1])[1]:
            w = wave.open(io.BytesIO(wav))
            print("%5d,%-3d %dch %5dHz %2dbit %.2fs" % (g, i, w.getnchannels(), w.getframerate(),
                                                      w.getsampwidth() * 8, w.getnframes() / w.getframerate()))
    elif len(argv) >= 3 and argv[0] == "build":
        build(argv[1], argv[2], argv[3:])
    elif len(argv) == 3 and argv[0] == "prep":
        prep(argv[1], argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
