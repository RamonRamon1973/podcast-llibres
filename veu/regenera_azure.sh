#!/usr/bin/env bash
# Regenera amb Azure TTS els episodis ja publicats (per defecte 1..8), reutilitzant
# els guions guardats a episodes/epNN-guio.txt i mantenint el feed intacte
# (mateix títol, autor, descripció, número i data; només canvia l'àudio).
#
# Ús: AZURE_KEY=xxx AZURE_REGION=francecentral ./regenera_azure.sh <TOKEN> [DES] [FINS]
set -euo pipefail

TOKEN="$1"; DES="${2:-1}"; FINS="${3:-8}"
REPO="RamonRamon1973/podcast-llibres"
WORK="/tmp/regen-work"

command -v ffmpeg >/dev/null || { apt-get update -q && apt-get install -y -q ffmpeg; }

rm -rf "$WORK" && git clone -q "https://x-access-token:${TOKEN}@github.com/${REPO}.git" "$WORK"
cd "$WORK"
git config user.email "claude@anthropic.com"
git config user.name "Claude"

for n in $(seq "$DES" "$FINS"); do
  NN=$(printf "%02d" "$n")
  GUIO="episodes/ep${NN}-guio.txt"
  if [ ! -f "$GUIO" ]; then echo "!! Falta $GUIO, salto"; continue; fi
  echo "==> Regenerant episodi $NN amb Azure"

  AZURE_KEY="$AZURE_KEY" AZURE_REGION="${AZURE_REGION:-francecentral}" \
    AZURE_VOICE="${AZURE_VOICE:-ca-ES-JoanaNeural}" \
    python3 veu/azure_tts.py "$GUIO" azure_raw.mp3

  ffmpeg -y -i azure_raw.mp3 -af "highpass=f=60,loudnorm=I=-16:TP=-2.0:LRA=11,alimiter=limit=0.95" \
    -c:a libmp3lame -b:a 160k "episodes/ep${NN}.mp3" -loglevel error

  # Actualitzar la mida (length) i la durada al feed per a aquest episodi
  SIZE=$(stat -c%s "episodes/ep${NN}.mp3")
  DUR_S=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "episodes/ep${NN}.mp3")
  DUR=$(python3 -c "d=float('$DUR_S'); print(f'{int(d//60)}:{int(d%60):02d}')")
  python3 - "$NN" "$SIZE" "$DUR" << 'PYEOF'
import sys, re
NN, SIZE, DUR = sys.argv[1:4]
feed = open('feed.xml', encoding='utf-8').read()
# Actualitza length de l'enclosure d'aquest episodi
feed = re.sub(rf'(episodes/ep{NN}\.mp3" length=")\d+', rf'\g<1>{SIZE}', feed)
# Actualitza itunes:duration dins del bloc d'aquest episodi
def repl(m):
    return re.sub(r'(<itunes:duration>)[^<]*', rf'\g<1>{DUR}', m.group(0))
feed = re.sub(rf'<item>.*?gestio15-ep{NN}.*?</item>', repl, feed, flags=re.DOTALL)
open('feed.xml','w',encoding='utf-8').write(feed)
import xml.etree.ElementTree as ET; ET.parse('feed.xml')
print(f'    feed actualitzat: ep{NN} {DUR} {SIZE}b')
PYEOF
  echo "    ep${NN} regenerat ($DUR, $SIZE bytes)"
done

echo "==> Publicant tots els canvis"
git add -A
git commit -q -m "Regenerar episodis ${DES}-${FINS} amb veu Azure"
git push -q origin main
echo "==> FET. Episodis ${DES} a ${FINS} regenerats amb Azure."
