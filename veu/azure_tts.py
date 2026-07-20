#!/usr/bin/env python3
"""Genera àudio amb Azure Text-to-Speech (veu catalana neuronal).
Ús: AZURE_KEY=xxx AZURE_REGION=francecentral python3 azure_tts.py guio.txt sortida.mp3
Troceja el guió en blocs (Azure limita cada petició), genera cada bloc i els concatena.
Surt amb codi 0 si tot va bé; codi != 0 si falla (perquè l'script pugui fer fallback a Piper)."""
import sys, os, re, subprocess, tempfile, urllib.request, urllib.error, html

KEY = os.environ.get("AZURE_KEY", "").strip()
REGION = os.environ.get("AZURE_REGION", "francecentral").strip()
VOICE = os.environ.get("AZURE_VOICE", "ca-ES-JoanaNeural").strip()

def die(msg, code=1):
    print(f"[azure_tts] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

if not KEY:
    die("Falta AZURE_KEY")

guio_path, out_path = sys.argv[1], sys.argv[2]
text = open(guio_path, encoding="utf-8").read().strip()

# Trocejar en blocs de ~2500 caràcters respectant els finals de frase
def trosseja(t, maxlen=2500):
    frases = re.split(r'(?<=[.!?])\s+', t)
    blocs, actual = [], ""
    for f in frases:
        if len(actual) + len(f) + 1 > maxlen and actual:
            blocs.append(actual.strip()); actual = f
        else:
            actual += " " + f
    if actual.strip():
        blocs.append(actual.strip())
    return blocs

blocs = trosseja(text)
print(f"[azure_tts] {len(text)} caràcters en {len(blocs)} blocs, veu {VOICE}")

endpoint = f"https://{REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
tmpdir = tempfile.mkdtemp()
parts = []

for i, bloc in enumerate(blocs):
    # SSML amb prosòdia lleugerament més pausada per to de podcast
    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ca-ES">'
        f'<voice name="{VOICE}"><prosody rate="-4%">{html.escape(bloc)}</prosody></voice></speak>'
    )
    req = urllib.request.Request(
        endpoint, data=ssml.encode("utf-8"),
        headers={
            "Ocp-Apim-Subscription-Key": KEY,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3",
            "User-Agent": "podcast-gestio",
        })
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            audio = resp.read()
    except urllib.error.HTTPError as e:
        die(f"HTTP {e.code} al bloc {i}: {e.read().decode(errors='replace')[:200]}")
    except Exception as e:
        die(f"Error de xarxa al bloc {i}: {e}")
    if len(audio) < 500:
        die(f"Bloc {i} massa curt ({len(audio)} bytes), possible error d'autenticació")
    p = os.path.join(tmpdir, f"part{i:03d}.mp3")
    open(p, "wb").write(audio)
    parts.append(p)
    print(f"[azure_tts]   bloc {i+1}/{len(blocs)} OK ({len(audio)} bytes)")

# Concatenar tots els blocs amb ffmpeg
llista = os.path.join(tmpdir, "list.txt")
with open(llista, "w") as f:
    for p in parts:
        f.write(f"file '{p}'\n")
r = subprocess.run(
    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", llista, "-c", "copy", out_path],
    capture_output=True)
if r.returncode != 0 or not os.path.exists(out_path):
    die(f"ffmpeg concat ha fallat: {r.stderr.decode(errors='replace')[:200]}")

print(f"[azure_tts] FET: {out_path}")
