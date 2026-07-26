#!/usr/bin/env python3
"""
regenera_tot.py — Regenera l'àudio de TOTS els episodis ja publicats
(català i/o castellà) aplicant el diccionari de pronunciacions actualitzat.

Reaprofita els guions ja desats (episodes/epNN-guio.txt i
episodes-es/epNN-guio.txt), NO toca títol/autor/descripció/data al feed,
només substitueix l'mp3 i actualitza mida+durada.

Pensat per córrer dins de GitHub Actions (accés obert a Azure).

Variables d'entorn: AZURE_KEY, AZURE_REGION, AZURE_KEY_ES, AZURE_REGION_ES
Variable opcional IDIOMES=ca,es (per defecte tots dos)
"""
import os, sys, re, glob, subprocess, tempfile, urllib.request, urllib.error, html
import pronunciacions

KEY = os.environ.get("AZURE_KEY", "").strip()
REGION = os.environ.get("AZURE_REGION", "francecentral").strip()
IDIOMES = [x.strip() for x in os.environ.get("IDIOMES", "ca,es").split(",") if x.strip()]

CONFIGS = {
    "ca": {"epis": "episodes", "feed": "feed.xml", "voice": "ca-ES-JoanaNeural",
           "lang": "ca-ES", "guid": "gestio15-ep", "key": None, "region": None},
    "es": {"epis": "episodes-es", "feed": "feed-es.xml", "voice": "es-ES-ElviraNeural",
           "lang": "es-ES", "guid": "gestion15es-ep",
           "key": os.environ.get("AZURE_KEY_ES", "").strip() or None,
           "region": os.environ.get("AZURE_REGION_ES", "").strip() or None},
}

def log(m): print(f"[regen] {m}", flush=True)
def die(m): print(f"[regen] ERROR: {m}", file=sys.stderr, flush=True); sys.exit(1)
if not KEY: die("Falta AZURE_KEY")

def run(cmd, **kw): return subprocess.run(cmd, capture_output=True, text=True, **kw)

def azure_tts(text, out_mp3, voice, lang, key, region):
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
    endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    tmp = tempfile.mkdtemp(); parts = []
    blocs = trosseja(text)
    log(f"  {len(text)} caràcters en {len(blocs)} blocs, veu {voice}")
    for i, bloc in enumerate(blocs):
        ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">'
                f'<voice name="{voice}"><prosody rate="-4%">{html.escape(bloc)}</prosody></voice></speak>')
        req = urllib.request.Request(endpoint, data=ssml.encode("utf-8"),
            headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/ssml+xml",
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
    lst = os.path.join(tmp, "l.txt")
    with open(lst, "w") as f:
        for p in parts: f.write(f"file '{p}'\n")
    raw = os.path.join(tmp, "raw.mp3")
    r = run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c","copy",raw])
    if r.returncode: die(f"concat: {r.stderr[:200]}")
    r = run(["ffmpeg","-y","-i",raw,"-af",
             "highpass=f=60,loudnorm=I=-16:TP=-2.0:LRA=11,alimiter=limit=0.95",
             "-c:a","libmp3lame","-b:a","160k",out_mp3])
    if r.returncode: die(f"masterització: {r.stderr[:200]}")

def actualitza_feed(feed_path, guid, NN, size, dur):
    """Només actualitza length i itunes:duration d'aquest episodi, sense tocar res més."""
    feed = open(feed_path, encoding="utf-8").read()
    bloc_pattern = re.compile(rf'<item>.*?{re.escape(guid)}{NN}.*?</item>', re.DOTALL)
    m = bloc_pattern.search(feed)
    if not m:
        log(f"    !! No trobo el bloc {guid}{NN} al feed, salto l'actualització del feed")
        return
    bloc = m.group(0)
    bloc2 = re.sub(r'length="\d+"', f'length="{size}"', bloc)
    bloc2 = re.sub(r'(<itunes:duration>)[^<]*', rf'\g<1>{dur}', bloc2)
    feed = feed[:m.start()] + bloc2 + feed[m.end():]
    open(feed_path, "w", encoding="utf-8").write(feed)
    import xml.etree.ElementTree as ET
    ET.parse(feed_path)

run(["git","config","user.name","GitHub Actions"])
run(["git","config","user.email","actions@github.com"])

total = 0
for idi in IDIOMES:
    cfg = CONFIGS.get(idi)
    if not cfg:
        log(f"Idioma desconegut: {idi}, salto"); continue
    key = cfg["key"] or KEY
    region = cfg["region"] or REGION
    guions = sorted(glob.glob(f"{cfg['epis']}/ep*-guio.txt"))
    log(f"== Idioma {idi}: {len(guions)} episodis a regenerar ==")
    for gp in guions:
        NN = os.path.basename(gp).split("-")[0].replace("ep", "")
        titol_log = f"ep{NN}"
        log(f"-- Regenerant {idi} {titol_log} --")
        text_original = open(gp, encoding="utf-8").read()
        text_tts = pronunciacions.aplica(text_original, lang=cfg["lang"])
        out_mp3 = f"{cfg['epis']}/ep{NN}.mp3"
        azure_tts(text_tts, out_mp3, cfg["voice"], cfg["lang"], key, region)
        size = os.path.getsize(out_mp3)
        durs = run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",out_mp3]).stdout.strip()
        sec = float(durs); dur = f"{int(sec//60)}:{int(sec%60):02d}"
        actualitza_feed(cfg["feed"], cfg["guid"], NN, size, dur)
        log(f"   {titol_log} regenerat: {dur}, {size} bytes")
        total += 1

log(f"Regenerats {total} episodis en total ({', '.join(IDIOMES)}).")
log("FET.")
