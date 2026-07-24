#!/usr/bin/env python3
"""
processa_pendents.py — S'executa al PC (Windows) amb accés a Azure.
Comprova la carpeta pendents/ del repo, i per cada guió pendent:
  1. genera l'àudio amb Azure TTS (veu catalana neuronal)
  2. masteritza amb ffmpeg
  3. actualitza feed.xml i README.md
  4. mou el guió de pendents/ a episodes/epNN-guio.txt
  5. fa commit i push
Cada guió pendent és un fitxer JSON: pendents/epNN.json amb els camps
  {nn, titol, autor, descripcio, guio}

Variables d'entorn necessàries:
  GH_TOKEN       token de GitHub
  AZURE_KEY      clau d'Azure Speech
  AZURE_REGION   regió (p.ex. francecentral)
  AZURE_VOICE    (opcional) veu, per defecte ca-ES-JoanaNeural
"""
import os, sys, re, json, subprocess, tempfile, urllib.request, urllib.error, html, glob, datetime

REPO_DIR = os.environ.get("REPO_DIR", os.path.join(os.path.dirname(__file__), ".."))
KEY = os.environ.get("AZURE_KEY", "").strip()
REGION = os.environ.get("AZURE_REGION", "francecentral").strip()
VOICE = os.environ.get("AZURE_VOICE", "ca-ES-JoanaNeural").strip()

# ffmpeg i ffprobe: si FFMPEG_DIR està definit, usa'ls des d'allà; si no, del PATH
FFDIR = os.environ.get("FFMPEG_DIR", "").strip()
FFMPEG = os.path.join(FFDIR, "ffmpeg") if FFDIR else "ffmpeg"
FFPROBE = os.path.join(FFDIR, "ffprobe") if FFDIR else "ffprobe"

def log(m): print(f"[podcast] {m}", flush=True)
def die(m, c=1): print(f"[podcast] ERROR: {m}", file=sys.stderr, flush=True); sys.exit(c)

if not KEY: die("Falta AZURE_KEY")
os.chdir(REPO_DIR)

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return r

# ---- Azure TTS ----
def azure_tts(text, out_mp3):
    def trosseja(t, maxlen=2500):
        frases = re.split(r'(?<=[.!?])\s+', t)
        blocs, actual = [], ""
        for f in frases:
            if len(actual) + len(f) + 1 > maxlen and actual:
                blocs.append(actual.strip()); actual = f
            else:
                actual += " " + f
        if actual.strip(): blocs.append(actual.strip())
        return blocs
    endpoint = f"https://{REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    tmp = tempfile.mkdtemp(); parts = []
    blocs = trosseja(text)
    log(f"{len(text)} caràcters en {len(blocs)} blocs, veu {VOICE}")
    for i, bloc in enumerate(blocs):
        ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ca-ES">'
                f'<voice name="{VOICE}"><prosody rate="-4%">{html.escape(bloc)}</prosody></voice></speak>')
        req = urllib.request.Request(endpoint, data=ssml.encode("utf-8"),
            headers={"Ocp-Apim-Subscription-Key": KEY, "Content-Type": "application/ssml+xml",
                     "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3",
                     "User-Agent": "podcast-gestio"})
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                audio = resp.read()
        except urllib.error.HTTPError as e:
            die(f"Azure HTTP {e.code} bloc {i}: {e.read().decode(errors='replace')[:200]}")
        except Exception as e:
            die(f"Azure xarxa bloc {i}: {e}")
        if len(audio) < 500: die(f"Bloc {i} massa curt: possible error de clau")
        p = os.path.join(tmp, f"p{i:03d}.mp3"); open(p, "wb").write(audio); parts.append(p)
        log(f"  bloc {i+1}/{len(blocs)} OK")
    lst = os.path.join(tmp, "l.txt")
    with open(lst, "w") as f:
        for p in parts: f.write(f"file '{p}'\n")
    raw = os.path.join(tmp, "raw.mp3")
    r = run([FFMPEG,"-y","-f","concat","-safe","0","-i",lst,"-c","copy",raw])
    if r.returncode: die(f"concat: {r.stderr[:200]}")
    # Masterització: highpass + loudnorm amb marge + limitador (evita distorsió a volum alt)
    r = run([FFMPEG,"-y","-i",raw,"-af",
             "highpass=f=60,loudnorm=I=-16:TP=-2.0:LRA=11,alimiter=limit=0.95",
             "-c:a","libmp3lame","-b:a","160k",out_mp3])
    if r.returncode: die(f"masterització: {r.stderr[:200]}")

# ---- Processa cada guió pendent ----
pendents = sorted(glob.glob("pendents/ep*.json"))
if not pendents:
    log("No hi ha guions pendents. Res a fer."); sys.exit(0)

run(["git","config","user.email","podcast@local"])
run(["git","config","user.name","Podcast PC"])

for pf in pendents:
    d = json.load(open(pf, encoding="utf-8"))
    NN = str(d["nn"]).zfill(2)
    if f"gestio15-ep{NN}" in open("feed.xml", encoding="utf-8").read():
        log(f"ep{NN} ja existeix al feed, salto i esborro el pendent")
        os.remove(pf); continue
    log(f"== Processant ep{NN}: {d['titol']} ({d['autor']}) ==")
    open(f"episodes/ep{NN}-guio.txt","w",encoding="utf-8").write(d["guio"])
    azure_tts(d["guio"], f"episodes/ep{NN}.mp3")
    size = os.path.getsize(f"episodes/ep{NN}.mp3")
    durs = run([FFPROBE,"-v","error","-show_entries","format=duration","-of","csv=p=0",f"episodes/ep{NN}.mp3"]).stdout.strip()
    sec = float(durs); dur = f"{int(sec//60)}:{int(sec%60):02d}"
    pub = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    # Inserir al feed abans del primer <item>
    feed = open("feed.xml", encoding="utf-8").read()
    item = (f'    <item>\n'
            f'      <title>Ep. {int(NN)} — {d["titol"]}, de {d["autor"]}</title>\n'
            f'      <description>{d["descripcio"]}</description>\n'
            f'      <enclosure url="https://op3.dev/e/raw.githubusercontent.com/RamonRamon1973/podcast-llibres/main/episodes/ep{NN}.mp3" length="{size}" type="audio/mpeg"/>\n'
            f'      <guid isPermaLink="false">gestio15-ep{NN}</guid>\n'
            f'      <pubDate>{pub}</pubDate>\n'
            f'      <itunes:duration>{dur}</itunes:duration>\n'
            f'      <itunes:episode>{int(NN)}</itunes:episode>\n'
            f'      <itunes:explicit>false</itunes:explicit>\n'
            f'    </item>\n\n')
    feed = feed.replace("    <item>", item + "    <item>", 1)
    open("feed.xml","w",encoding="utf-8").write(feed)
    import xml.etree.ElementTree as ET; ET.parse("feed.xml")
    # README
    linia = f'{int(NN)}. {d["titol"]} — {d["autor"]}'
    rm = open("README.md", encoding="utf-8").read()
    if linia not in rm: open("README.md","a",encoding="utf-8").write(linia+"\n")
    os.remove(pf)
    log(f"ep{NN} llest: {dur}, {size} bytes")

if os.environ.get("SKIP_GIT", "").strip():
    log("FET. Àudio generat (el commit/push el fa el workflow).")
else:
    log("Publicant a GitHub...")
    run(["git","add","-A"])
    run(["git","commit","-q","-m","Episodis processats amb Azure des del PC"])
    pr = run(["git","push","origin","main"])
    if pr.returncode: die(f"push: {pr.stderr[:200]}")
    log("FET. Tot publicat.")
