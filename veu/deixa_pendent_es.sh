#!/usr/bin/env bash
# deixa_pendent_es.sh — El fa servir Cowork per al podcast en CASTELLÀ.
# Desa un guió com a pendent perquè GitHub Actions el converteixi amb la veu Elvira.
# El número d'episodi es calcula SOL (episodis ja publicats al feed-es + pendents).
# Ús: ./deixa_pendent_es.sh <TOKEN> "<TÍTULO>" "<AUTOR>" "<DESCRIPCIÓN>" <guio_es.txt> [pron.json]
# pron.json (opcional): {"Nombre Inglés": "aproximación fonética castellana", ...}
set -euo pipefail

TOKEN="$1"; TITOL="$2"; AUTOR="$3"; DESC="$4"; GUIO="$(realpath "$5")"
PRON="${6:-}"; [ -n "$PRON" ] && PRON="$(realpath "$PRON")"
REPO="RamonRamon1973/podcast-llibres"
WORK="/tmp/pendent-es-work"

rm -rf "$WORK" && git clone -q "https://x-access-token:${TOKEN}@github.com/${REPO}.git" "$WORK"
cd "$WORK"

# Número següent = publicats al feed-es + pendents existents + 1
PUB=$(grep -c "gestion15es-ep" feed-es.xml || true)
PEND=$(ls pendents-es/ep*.json 2>/dev/null | wc -l || true)
NN=$(printf "%02d" $((PUB + PEND + 1)))

# Anti-duplicats pel títol (mateix llibre ja publicat o pendent en castellà?)
if grep -qF "$TITOL" feed-es.xml || grep -qsF "$TITOL" pendents-es/ep*.json 2>/dev/null; then
  echo "!! El llibre \"$TITOL\" ja existeix al podcast castellà. Aturo."; exit 1
fi

python3 - "$NN" "$TITOL" "$AUTOR" "$DESC" "$GUIO" "$PRON" << 'PYEOF'
import sys, json
NN, TITOL, AUTOR, DESC, GUIO, PRON = sys.argv[1:7]
guio = open(GUIO, encoding="utf-8").read()
d = {"nn": int(NN), "titol": TITOL, "autor": AUTOR, "descripcio": DESC, "guio": guio}
if PRON:
    d["pron"] = json.load(open(PRON, encoding="utf-8"))
open(f"pendents-es/ep{NN}.json","w",encoding="utf-8").write(
    json.dumps(d, ensure_ascii=False, indent=2))
print(f"    Pendent castellà ep{NN} desat ({len(guio)} caràcters" +
      (f", {len(d.get('pron', {}))} pronunciacions extra" if PRON else "") + ")")
PYEOF

git config user.email "claude@anthropic.com"
git config user.name "Claude"
git add -A
git commit -q -m "Guión pendiente ES ep${NN}: ${TITOL} (${AUTOR})"
# Bypass del proxy local de git de l'entorn Cowork/CCR (veu deixa_pendent.sh per al detall).
env -u https_proxy -u HTTPS_PROXY -u http_proxy -u HTTP_PROXY git push -q origin main
echo "==> FET. Guió castellà de l'episodi ${NN} deixat com a pendent."
