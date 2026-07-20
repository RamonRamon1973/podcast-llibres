---
name: podcast-gestio
description: Produeix i publica un episodi diari del podcast "Gestió en 15 Minuts" (resums en català de llibres de gestió empresarial, ~15 min d'àudio, publicats a un feed RSS allotjat a GitHub i distribuïts via Apple Podcasts). Utilitza SEMPRE aquesta skill quan l'usuari digui "episodi d'avui", "publica l'episodi", "nou episodi", "resum del llibre d'avui", mencioni el podcast de llibres o demani generar/publicar un resum en àudio d'un llibre de gestió, encara que no digui la paraula "podcast".
---

# Podcast "Gestió en 15 Minuts" — Producció i publicació d'un episodi

## Context fix del projecte

- **Podcast**: "Gestió en 15 Minuts", en català. Un llibre de gestió empresarial per episodi.
- **Repositori**: `github.com/RamonRamon1973/podcast-llibres` (branca `main`)
- **Feed públic**: `https://ramonramon1973.github.io/podcast-llibres/feed.xml` (GitHub Pages, es desplega sol amb cada push)
- **Estructura**: `feed.xml`, `cover.png`, `index.html`, `README.md` (llista de llibres publicats), `episodes/epNN.mp3` + `episodes/epNN-guio.txt`
- **Estadístiques**: les URL d'àudio del feed van prefixades amb OP3.
- **Autenticació**: cal un token fine-grained de GitHub del propietari (Ramon). **Mai no està desat en aquesta skill.** Si no és al missatge de l'usuari ni a l'entorn de la tasca, demana'l abans de començar. No el mostris mai sencer en cap resposta.

## Via ràpida (RECOMANADA): l'script `veu/publica.sh`

Tota la part tècnica (veu, correcció de la erra, àudio MP3, feed, README, commit, push i verificació) ja està encapsulada a `veu/publica.sh` del repositori. El flux recomanat és:

1. Clona el repo, decideix el llibre (pas 2 de baix) i escriu el guió (pas 3) a un fitxer `guio.txt`.
2. Executa: `bash veu/publica.sh <TOKEN> <NN> "<TÍTOL>" "<AUTOR>" "<DESCRIPCIÓ>" <ruta_absoluta_guio.txt>`
3. Comprova que acaba amb "FET" i verificació HTTP 200.

L'script ja gestiona: protecció anti-duplicats (feed i README), model medium amb fallback a x-low, correcció de la erra, MP3 net (no AAC), length_scale 1.18 i masterització. Els passos manuals de sota són la referència detallada per si cal depurar o modificar alguna cosa.

**IMPORTANT sobre el format i el soroll de fons:** els episodis són MP3 (`libmp3lame`, 160k), NO AAC/m4a. A més, la veu medium genera un lleuger soroll de fons a les pauses; per això la cadena de masterització inclou un noise gate (`agate`) i fa servir `dynaudnorm` en lloc de `loudnorm` (aquest últim amplificava el soroll dels silencis fins a fer-lo audible, ~-37 dB; amb el gate baixa a ~-73 dB, inaudible). NO tornis a `loudnorm` ni treguis l'`agate`.



## Veu: Azure TTS (per defecte si hi ha clau) o Piper (reserva)

Si les variables d'entorn `AZURE_KEY` i `AZURE_REGION` estan definides, l'script genera l'àudio amb la veu neuronal catalana d'Azure (`ca-ES-JoanaNeural`), que és neta, natural i pronuncia bé les erres. Si no hi ha clau o Azure falla, torna automàticament a la veu Piper mini (allotjada al repo). No cal cap correcció d'erra ni afftdn amb Azure. La tasca de Cowork ha de passar AZURE_KEY i AZURE_REGION com a variables d'entorn abans de cridar publica.sh.

---

## Procés detallat (referència)

### 1. Preparar l'entorn

```bash
cd /home/claude
git clone https://x-access-token:TOKEN@github.com/RamonRamon1973/podcast-llibres.git repo
pip install piper-tts --break-system-packages -q
```

Comprova que `ffmpeg` existeix (`which ffmpeg`; si no, `apt-get install -y ffmpeg`).

**Veu — model medium (qualitat superior, PER DEFECTE):**
Els dos arxius de la veu ja són al mateix repositori, així que es baixen sempre des de GitHub (domini accessible):
```bash
curl -sL -o ca-medium.onnx "https://github.com/RamonRamon1973/podcast-llibres/releases/download/veu-medium/ca_ES-upc_ona-medium.onnx"
curl -sL -o ca-medium.onnx.json "https://raw.githubusercontent.com/RamonRamon1973/podcast-llibres/main/veu/ca_ES-upc_ona-medium.onnx.json"
```
*Alternativa d'emergència* si la veu medium fallés: `curl -sL -o v.tar.gz https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-ca-upc_ona-x-low.tar.gz && tar xzf v.tar.gz` (dona `ca-upc_ona-x-low.onnx`, qualitat inferior).

**Correcció OBLIGATÒRIA de la erra:** la veu medium no pronuncia bé la erra vibrant inicial de paraula (diu "Damon" en lloc de "Ramon"). Abans de generar l'àudio, passa SEMPRE el guió pel filtre `veu/fix_erra.py` (és al repositori), que dobla la erra inicial de paraula (Ramon→Rramon, resum→rresum) sense tocar les erres internes (terra, carro). Ús: `python3 veu/fix_erra.py < guio.txt > guio_tts.txt` i genera l'àudio des de `guio_tts.txt`. El guió que es desa a `episodes/epNN-guio.txt` ha de ser l'ORIGINAL sense doblar, no el corregit.

### 2. Decidir el llibre

Llegeix `repo/README.md` (secció "Llibres publicats") i `repo/feed.xml` per saber:
- l'últim número d'episodi `NN` (el nou és `NN+1`)
- quins llibres ja s'han fet (**mai no es repeteix cap llibre ni cap autor dos dies seguits**)

Criteris de tria: alterna (a) clàssics de referència del management (Drucker, Collins, Covey, Kahneman, Christensen, Grove, Porter, Sinek, Lencioni, Ries...) i (b) novetats influents dels últims 2-3 anys. Tria'l tu: no preguntis a l'usuari.

### 3. Escriure el guió

Fitxer de treball: `/home/claude/guio.txt`. Requisits:

- **En català**, to de podcast conversacional (parla a "tu"), sense encapçalaments ni llistes amb símbols: text corregut que es pugui llegir en veu alta.
- **Mínim 2.600 paraules** (comprova amb `wc -w`; amb la veu medium a length_scale 1.18, ~2.600-2.900 paraules donen 14-16 min. Per sota, l'àudio queda curt).
- Estructura: salutació i presentació del llibre i per què s'ha triat → context de l'autor → tesi central → 3-6 idees clau desenvolupades amb exemples i casos reals → si escau, una nota crítica honesta sobre les limitacions del llibre → 4-5 accions pràctiques concretes per aplicar demà → resum final d'una frase → comiat anunciant que demà hi haurà nou episodi.
- Escriu els números en lletres (la veu llegeix malament les xifres) i evita anglicismes innecessaris; els títols en anglès es diuen tal qual i es tradueixen un cop.
- Cap dada inventada: si no estàs segur d'una xifra o cas del llibre, omet-lo o explica'l de manera genèrica.

### 4. Generar i masteritzar l'àudio

Primer aplica la correcció de la erra, després genera amb el model medium:

```bash
python3 repo/veu/fix_erra.py < guio.txt > guio_tts.txt

# length_scale 1.18: la veu medium parla ràpid; aquest valor la porta a ritme de podcast
python3 -m piper --model ca-medium.onnx --length_scale 1.18 --sentence_silence 0.45 \
  --output_file ep.wav < guio_tts.txt

ffmpeg -y -i ep.wav -af "highpass=f=75,afftdn=nf=-25:nt=w,equalizer=f=3200:t=q:w=1.2:g=2.5,acompressor=threshold=-18dB:ratio=3:attack=10:release=150,dynaudnorm=f=250:g=4:p=0.9,agate=threshold=0.008:ratio=9:attack=1:release=100" \
  -c:a libmp3lame -b:a 160k repo/episodes/epNN.mp3
```

Nota: `guio.txt` és l'original (es desa com a `epNN-guio.txt`); `guio_tts.txt` és el corregit i només serveix per generar l'àudio.

Comprova la durada: `ffprobe -v error -show_entries format=duration -of csv=p=0 repo/episodes/epNN.mp3`.
**Objectiu: entre 13:30 i 16:30 minuts.** Si queda curt, amplia el guió amb una secció nova (un cas real més, una crítica, una comparació amb un altre llibre ja publicat al podcast) i regenera. Desa el guió final a `repo/episodes/epNN-guio.txt`.

### 5. Actualitzar el feed

Obté la mida exacta en bytes (`stat -c%s`) i la durada en format `MM:SS`. Insereix aquest bloc a `repo/feed.xml` **just abans del primer `<item>` existent** (l'episodi nou sempre va a dalt):

```xml
    <item>
      <title>Ep. NN — TÍTOL, d'AUTOR</title>
      <description>DESCRIPCIÓ ATRACTIVA DE 2-4 FRASES AMB LES IDEES CLAU. Acaba amb: Resum i comentari del llibre en català.</description>
      <enclosure url="https://op3.dev/e/raw.githubusercontent.com/RamonRamon1973/podcast-llibres/main/episodes/epNN.mp3" length="BYTES" type="audio/mpeg"/>
      <guid isPermaLink="false">gestio15-epNN</guid>
      <pubDate>DATA RFC-2822 D'AVUI, p.ex. Sat, 18 Jul 2026 09:00:00 +0200</pubDate>
      <itunes:duration>MM:SS</itunes:duration>
      <itunes:episode>NN</itunes:episode>
      <itunes:explicit>false</itunes:explicit>
    </item>
```

Valida sempre l'XML abans de continuar:
`python3 -c "import xml.etree.ElementTree as ET; ET.parse('repo/feed.xml')"`

### 6. Actualitzar el registre de llibres

Afegeix una línia `NN. TÍTOL — AUTOR (ANY)` a la llista de `repo/README.md`.

### 7. Publicar i verificar

```bash
cd repo && git config user.email "claude@anthropic.com" && git config user.name "Claude"
git add -A && git commit -m "Episodi NN: TÍTOL (AUTOR)" && git push origin main
```

Verificació obligatòria després del push:
- `curl -s -o /dev/null -w "%{http_code}"` de l'àudio nou a `raw.githubusercontent.com` → ha de ser 200
- estat del desplegament: `GET https://api.github.com/repos/RamonRamon1973/podcast-llibres/pages/builds/latest` amb el token → `"status": "built"` (pot trigar ~1 min; reintenta)

### 8. Informar l'usuari

Missatge breu: número i llibre publicat, durada, recordatori que refresqui l'app Podcasts, i avança quin llibre tens pensat per a demà. Sense tecnicismes.

## Gestió d'errors

- **Push rebutjat (canvis remots)**: `git pull --rebase origin main` i torna a fer push.
- **403 de l'API de GitHub**: el token no té permisos o ha estat revocat → demana a l'usuari que el revisi; no reintentis a cegues.
- **La veu medium no es descarrega**: usa la x-low de GitHub sense preguntar res.
- **Durada fora de rang després de 2 intents**: publica igualment si està entre 12 i 18 min i menciona-ho a l'usuari.
- Mai no esborris ni reescriguis episodis anteriors del feed: només afegeix.
