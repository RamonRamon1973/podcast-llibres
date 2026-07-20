#!/usr/bin/env bash
# Automatitza la part TÈCNICA de publicar un episodi del podcast.
# NO escriu el guió (això ho fa Claude). Rep un guió ja escrit i s'encarrega de
# tota la resta: veu, àudio, feed, README, commit, push i verificació.
#
# Ús:
#   ./publica.sh <TOKEN> <NN> "<TÍTOL>" "<AUTOR>" "<DESCRIPCIÓ>" <guio.txt>
#
# Exemple:
#   ./publica.sh github_pat_xxx 06 "The Lean Startup" "Eric Ries" "Descripció..." guio.txt
#
# Requisits previs (els instal·la si falten): piper-tts, ffmpeg.
set -euo pipefail

TOKEN="$1"; NN="$2"; TITOL="$3"; AUTOR="$4"; DESC="$5"; GUIO="$6"
REPO="RamonRamon1973/podcast-llibres"
WORK="/tmp/podcast-work"
MASTER='highpass=f=70,equalizer=f=3200:t=q:w=1.2:g=2.5,acompressor=threshold=-18dB:ratio=3:attack=10:release=150,dynaudnorm=f=250:g=4:p=0.9'

echo "==> Preparant entorn"
command -v ffmpeg >/dev/null || { apt-get update -q && apt-get install -y -q ffmpeg; }
python3 -c "import piper" 2>/dev/null || pip install piper-tts --break-system-packages -q

rm -rf "$WORK" && git clone -q "https://x-access-token:${TOKEN}@github.com/${REPO}.git" "$WORK"
cd "$WORK"

# Protecció anti-duplicats: si l'episodi NN ja existeix al feed, atura't
if grep -q "gestio15-ep${NN}" feed.xml; then
  echo "!! L'episodi ${NN} ja existeix al feed. Aturo per no duplicar."
  exit 1
fi

echo "==> Generant l'àudio"
cp "$GUIO" "episodes/ep${NN}-guio.txt"           # guió original

if [ -n "${AZURE_KEY:-}" ]; then
  echo "    Provant Azure TTS (veu neuronal ${AZURE_VOICE:-ca-ES-JoanaNeural})"
  if AZURE_KEY="$AZURE_KEY" AZURE_REGION="${AZURE_REGION:-francecentral}" \
       AZURE_VOICE="${AZURE_VOICE:-ca-ES-JoanaNeural}" \
       python3 veu/azure_tts.py "$GUIO" azure_raw.mp3; then
    # Masterització lleugera (Azure ja surt net; només ajust de volum i to)
    # Azure ja surt net i ben anivellat: només un highpass suau i un limitador
    # per evitar pics que saturin (loudnorm amb marge, sense empènyer el volum)
    ffmpeg -y -i azure_raw.mp3 -af "highpass=f=60,loudnorm=I=-16:TP=-2.0:LRA=11,alimiter=limit=0.95" \
      -c:a libmp3lame -b:a 160k "episodes/ep${NN}.mp3" -loglevel error
    echo "    Àudio generat amb Azure ✓"
  else
    echo "!! Azure ha fallat, faig servir la veu Piper de reserva"
    AZURE_KEY=""
  fi
fi

if [ -z "${AZURE_KEY:-}" ] || [ ! -f "episodes/ep${NN}.mp3" ]; then
  echo "    Descarregant veu mini (Piper, reserva)"
  curl -sL -o ca-upc_ona-x-low.onnx "https://raw.githubusercontent.com/${REPO}/main/veu/ca-upc_ona-x-low.onnx"
  curl -sL -o ca-upc_ona-x-low.onnx.json "https://raw.githubusercontent.com/${REPO}/main/veu/ca-upc_ona-x-low.onnx.json"
  python3 -c "import piper" 2>/dev/null || pip install piper-tts --break-system-packages -q
  python3 -m piper --model ca-upc_ona-x-low.onnx --length_scale 1.05 --sentence_silence 0.45 \
    --output_file ep.wav < "$GUIO"
  ffmpeg -y -i ep.wav -af "$MASTER" -c:a libmp3lame -b:a 160k "episodes/ep${NN}.mp3" -loglevel error
fi

DUR_S=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "episodes/ep${NN}.mp3")
SIZE=$(stat -c%s "episodes/ep${NN}.mp3")
DUR=$(python3 -c "d=float('$DUR_S'); print(f'{int(d//60)}:{int(d%60):02d}')")
echo "    Durada: $DUR | Mida: $SIZE bytes"

echo "==> Actualitzant el feed"
PUBDATE=$(date -R)
python3 - "$NN" "$TITOL" "$AUTOR" "$DESC" "$SIZE" "$DUR" "$PUBDATE" << 'PYEOF'
import sys, re
NN, TITOL, AUTOR, DESC, SIZE, DUR, PUBDATE = sys.argv[1:8]
feed = open('feed.xml', encoding='utf-8').read()
item = f'''    <item>
      <title>Ep. {int(NN)} — {TITOL}, de {AUTOR}</title>
      <description>{DESC}</description>
      <enclosure url="https://op3.dev/e/raw.githubusercontent.com/RamonRamon1973/podcast-llibres/main/episodes/ep{NN}.mp3" length="{SIZE}" type="audio/mpeg"/>
      <guid isPermaLink="false">gestio15-ep{NN}</guid>
      <pubDate>{PUBDATE}</pubDate>
      <itunes:duration>{DUR}</itunes:duration>
      <itunes:episode>{int(NN)}</itunes:episode>
      <itunes:explicit>false</itunes:explicit>
    </item>

    <item>'''
# Insereix abans del primer <item> existent (només la primera ocurrència)
feed = feed.replace('    <item>', item, 1)
open('feed.xml','w',encoding='utf-8').write(feed)
import xml.etree.ElementTree as ET
ET.parse('feed.xml')  # llança excepció si l'XML és invàlid
print('    Feed vàlid i actualitzat')
PYEOF

echo "==> Actualitzant README"
LINIA="$(printf '%d. %s — %s' "$((10#$NN))" "$TITOL" "$AUTOR")"
grep -qF "$LINIA" README.md || echo "$LINIA" >> README.md

echo "==> Publicant a GitHub"
git config user.email "claude@anthropic.com"
git config user.name "Claude"
git add -A
git commit -q -m "Episodi ${NN}: ${TITOL} (${AUTOR})"
git push -q origin main

echo "==> Verificant"
sleep 5
CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://raw.githubusercontent.com/${REPO}/main/episodes/ep${NN}.mp3")
echo "    Àudio HTTP: $CODE"
echo "==> FET. Episodi ${NN} publicat: ${TITOL} (${AUTOR}) · ${DUR}"
