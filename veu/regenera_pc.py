#!/usr/bin/env python3
"""
regenera_pc.py — Regenera amb Azure els episodis indicats, al PC.
Reutilitza els guions guardats a episodes/epNN-guio.txt i actualitza el feed
(àudio, mida i durada) sense tocar títol/autor/descripció/data.
Per als episodis 1-5, a més, canvia l'enclosure de .m4a a .mp3 al feed si cal.

Ús:  py veu\\regenera_pc.py 1 2 3 4 5 6 7 8 9
     (llista de números d'episodi a regenerar, separats per espais)

Variables d'entorn: AZURE_KEY, AZURE_REGION, AZURE_VOICE (opc.), FFMPEG_DIR (opc.)
"""
import os, sys, re, subprocess, tempfile, urllib.request, urllib.error, html

REPO_DIR = os.environ.get("REPO_DIR", os.path.join(os.path.dirname(__file__), ".."))
KEY = os.environ.get("AZURE_KEY", "").strip()
REGION = os.environ.get("AZURE_REGION", "francecentral").strip()
VOICE = os.environ.get("AZURE_VOICE", "ca-ES-JoanaNeural").strip()
FFDIR = os.environ.get("FFMPEG_DIR", "").strip()
FFMPEG = os.path.join(FFDIR, "ffmpeg") if FFDIR else "ffmpeg"
FFPROBE = os.path.join(FFDIR, "ffprobe") if FFDIR else "ffprobe"

def log(m): print(f"[regen] {m}", flush=True)
def die(m): print(f"[regen] ERROR: {m}", file=sys.stderr, flush=True); sys.exit(1)
if not KEY: die("Falta AZURE_KEY")
os.chdir(REPO_DIR)

nums = [int(x) for x in sys.argv[1:]]
if not nums: die("Indica quins episodis regenerar, p.ex: py veu\\regenera_pc.py 1 2 3")

def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)

def azure_tts(text, out_mp3):
    frases = re.split(r'(?<=[.!?])\s+', text)
    blocs, cur = [], ""
    for f in frases:
        if len(cur)+len(f)+1 > 2500 and cur: blocs.append(cur.strip()); cur = f
        else: cur += " " + f
    if cur.strip(): blocs.append(cur.strip())
    endpoint = f"https://{REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    tmp = tempfile.mkdtemp(); parts = []
    log(f"{len(text)} caràcters en {len(blocs)} blocs")
    for i, b in enumerate(blocs):
        ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ca-ES">'
                f'<voice name="{VOICE}"><prosody rate="-4%">{html.escape(b)}</prosody></voice></speak>')
        req = urllib.request.Request(endpoint, data=ssml.encode("utf-8"),
            headers={"Ocp-Apim-Subscription-Key": KEY, "Content-Type": "application/ssml+xml",
                     "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3", "User-Agent": "podcast"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r: audio = r.read()
        except urllib.error.HTTPError as e: die(f"Azure HTTP {e.code}: {e.read().decode(errors='replace')[:200]}")
        except Exception as e: die(f"Azure xarxa: {e}")
        if len(audio) < 500: die(f"bloc {i} massa curt")
        p = os.path.join(tmp, f"p{i:03d}.mp3"); open(p,"wb").write(audio); parts.append(p)
        log(f"  bloc {i+1}/{len(blocs)} OK")
    lst = os.path.join(tmp,"l.txt"); open(lst,"w").write("".join(f"file '{p}'\n" for p in parts))
    raw = os.path.join(tmp,"raw.mp3")
    if run([FFMPEG,"-y","-f","concat","-safe","0","-i",lst,"-c","copy",raw]).returncode: die("concat")
    if run([FFMPEG,"-y","-i",raw,"-af",
            "highpass=f=60,loudnorm=I=-16:TP=-2.0:LRA=11,alimiter=limit=0.95",
            "-c:a","libmp3lame","-b:a","160k",out_mp3]).returncode: die("masterització")

run(["git","config","user.email","podcast@local"])
run(["git","config","user.name","Podcast PC"])

for n in nums:
    NN = str(n).zfill(2)
    guio_path = f"episodes/ep{NN}-guio.txt"
    if not os.path.exists(guio_path): log(f"!! Falta {guio_path}, salto"); continue
    log(f"== Regenerant ep{NN} ==")
    text = open(guio_path, encoding="utf-8").read()
    azure_tts(text, f"episodes/ep{NN}.mp3")
    # esborra el m4a antic si existeix
    old = f"episodes/ep{NN}.m4a"
    if os.path.exists(old): os.remove(old)
    size = os.path.getsize(f"episodes/ep{NN}.mp3")
    durs = run([FFPROBE,"-v","error","-show_entries","format=duration","-of","csv=p=0",f"episodes/ep{NN}.mp3"]).stdout.strip()
    sec = float(durs); dur = f"{int(sec//60)}:{int(sec%60):02d}"
    feed = open("feed.xml", encoding="utf-8").read()
    # Assegura que l'enclosure d'aquest episodi és .mp3 (converteix .m4a->.mp3 i type)
    feed = re.sub(rf'(episodes/ep{NN})\.m4a', rf'\1.mp3', feed)
    # Actualitza el type d'aquest episodi a audio/mpeg
    def fix_item(m):
        block = m.group(0)
        block = re.sub(r'type="audio/[^"]*"', 'type="audio/mpeg"', block)
        block = re.sub(rf'(episodes/ep{NN}\.mp3" length=")\d+', rf'\g<1>{size}', block)
        block = re.sub(r'(<itunes:duration>)[^<]*', rf'\g<1>{dur}', block)
        return block
    feed = re.sub(rf'<item>.*?gestio15-ep{NN}.*?</item>', fix_item, feed, flags=re.DOTALL)
    open("feed.xml","w",encoding="utf-8").write(feed)
    import xml.etree.ElementTree as ET; ET.parse("feed.xml")
    log(f"ep{NN} regenerat: {dur}, {size} bytes")

log("Publicant a GitHub...")
run(["git","add","-A"])
run(["git","commit","-q","-m",f"Regenerar episodis {nums} amb veu Azure"])
if run(["git","push","origin","main"]).returncode: die("push")
log("FET. Tot publicat.")
