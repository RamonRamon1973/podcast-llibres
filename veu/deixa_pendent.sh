#!/usr/bin/env bash
# deixa_pendent.sh — El fa servir Cowork (núvol, només GitHub).
# Desa un guió com a pendent perquè el PC el converteixi a àudio amb Azure.
# Ús: ./deixa_pendent.sh <TOKEN> <NN> "<TÍTOL>" "<AUTOR>" "<DESCRIPCIÓ>" <guio.txt>
set -euo pipefail

TOKEN="$1"; NN="$2"; TITOL="$3"; AUTOR="$4"; DESC="$5"; GUIO="$(realpath "$6")"
REPO="RamonRamon1973/podcast-llibres"
WORK="/tmp/pendent-work"

rm -rf "$WORK" && git clone -q "https://x-access-token:${TOKEN}@github.com/${REPO}.git" "$WORK"
cd "$WORK"

# Protecció anti-duplicats: ja publicat o ja pendent?
if grep -q "gestio15-ep${NN}" feed.xml; then
  echo "!! L'episodi ${NN} ja està publicat al feed. Aturo."; exit 1
fi
if [ -f "pendents/ep${NN}.json" ]; then
  echo "!! Ja hi ha un pendent per a l'episodi ${NN}. Aturo."; exit 1
fi

# Escriure el JSON del pendent (Python per escapar bé el text)
python3 - "$NN" "$TITOL" "$AUTOR" "$DESC" "$GUIO" << 'PYEOF'
import sys, json
NN, TITOL, AUTOR, DESC, GUIO = sys.argv[1:6]
guio = open(GUIO, encoding="utf-8").read()
d = {"nn": int(NN), "titol": TITOL, "autor": AUTOR, "descripcio": DESC, "guio": guio}
open(f"pendents/ep{NN.zfill(2)}.json","w",encoding="utf-8").write(
    json.dumps(d, ensure_ascii=False, indent=2))
print(f"    Pendent ep{NN.zfill(2)} desat ({len(guio)} caràcters)")
PYEOF

git config user.email "claude@anthropic.com"
git config user.name "Claude"
git add -A
git commit -q -m "Guió pendent ep${NN}: ${TITOL} (${AUTOR})"
git push -q origin main
echo "==> FET. Guió de l'episodi ${NN} deixat com a pendent. El PC el convertirà amb Azure."
