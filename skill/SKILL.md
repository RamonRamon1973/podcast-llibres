---
name: podcast-gestio
description: Produeix i publica un episodi diari del podcast "Gestió en 15 Minuts" / "Gestión en 15 Minutos" (anàlisi i comentari crític, en català i castellà, de llibres de gestió empresarial, ~15 min d'àudio, publicats a un feed RSS allotjat a GitHub i distribuïts via Apple Podcasts i Spotify). Utilitza SEMPRE aquesta skill quan l'usuari digui "episodi d'avui", "publica l'episodi", "nou episodi", "resum del llibre d'avui", mencioni el podcast de llibres o demani generar/publicar un resum/anàlisi en àudio d'un llibre de gestió, encara que no digui la paraula "podcast".
---

# Podcast "Gestió en 15 Minuts" — Producció i publicació d'un episodi

## Context fix del projecte

- **Podcast**: "Gestió en 15 Minuts" (català) i "Gestión en 15 Minutos" (castellà, traducció del mateix catàleg). Un llibre de gestió empresarial per episodi, en forma d'anàlisi i comentari crític original, no de resum seqüencial.
- **Repositori**: `github.com/RamonRamon1973/podcast-llibres` (branca `main`)
- **Feed públic CA**: `https://ramonramon1973.github.io/podcast-llibres/feed.xml`
- **Feed públic ES**: `https://ramonramon1973.github.io/podcast-llibres/feed-es.xml`
- (GitHub Pages es desplega sol amb cada push)
- **Estructura**: `feed.xml`/`feed-es.xml`, `cover.png`/`cover-es.png`, `index.html`/`es/index.html`, `README.md` (llibres publicats, només CA), `episodes/epNN.mp3`+`-guio.txt` i `episodes-es/epNN.mp3`+`-guio.txt`, `pendents/` i `pendents-es/` (bústia de guions pendents de veu)
- **Veu**: Azure Speech neuronal — `ca-ES-JoanaNeural` (recurs a França) i `es-ES-ElviraNeural` (recurs a Suècia), cadascun amb la seva quota gratuïta de 500.000 caràcters/mes independent
- **Estadístiques**: les URL d'àudio del feed van prefixades amb OP3.
- **Autenticació**: cal un token fine-grained de GitHub del propietari (Ramon). **Mai no està desat en aquesta skill.** Si no és al missatge de l'usuari ni a l'entorn de la tasca, demana'l abans de començar. No el mostris mai sencer en cap resposta.

## Com es publica un episodi (arquitectura real, actualitzada)

**Arquitectura del sistema (dos idiomes, català i castellà):** Cowork (aquesta skill) NOMÉS escriu el guió i el deixa "pendent" al repositori. NO genera l'àudio directament — això ho fa GitHub Actions (que sí té accés obert a Azure; l'entorn de Cowork no hi arriba).

Flux:
1. Clona el repo, decideix el llibre (secció "Decidir el llibre") i escriu el guió (secció "Escriure el guió i el disclaimer d'IA") a un fitxer `guio.txt`.
2. Si el guió conté noms propis anglesos que no siguin ja a `veu/pronunciacions.py`, crea un `pron.json` amb l'aproximació fonètica (veu la secció de pronunciació més avall).
3. Executa per al **català**:
   `bash veu/deixa_pendent.sh <TOKEN> <NN> "<TÍTOL>" "<AUTOR>" "<DESCRIPCIÓ>" "$(realpath guio.txt)" ["$(realpath pron.json)"]`
   (el número `NN` és el següent lliure: mira `README.md` i la carpeta `pendents/`)
4. Per al **castellà**, tradueix el guió (`guio_es.txt`, natural i adaptat, no literal) i executa:
   `bash veu/deixa_pendent_es.sh <TOKEN> "<TÍTULO>" "<AUTOR>" "<DESCRIPCIÓN>" "$(realpath guio_es.txt)" ["$(realpath pron_es.json)"]`
   (el número es calcula sol; NO repeteixis cap llibre que ja existeixi en castellà)
5. Comprova que cada script acaba amb "FET". **Aquí acaba la feina de Cowork.** El push a `pendents/` o `pendents-es/` dispara sol el workflow de GitHub Actions, que genera l'àudio amb Azure, actualitza `feed.xml`/`feed-es.xml` i `README.md`, i publica. No cal fer res més ni esperar que acabi.

**⚠️ Script `veu/publica.sh` OBSOLET**: és una relíquia de quan la veu era Piper i tot es feia en un sol pas. NO l'utilitzis. El pipeline real i vigent és `deixa_pendent.sh` / `deixa_pendent_es.sh` + GitHub Actions descrit a dalt.

**⚠️ Quota d'Azure**: cada recurs (català a França, castellà a Suècia) té 500.000 caràcters/mes gratuïts. Si el consum del mes va molt just (comprova-ho si l'usuari ho pregunta), un episodi pot fallar per quota exhaurida; en aquest cas informa l'usuari en lloc de reintentar en bucle.

---

## Pronunciació de noms i termes en anglès (IMPORTANT)

Les veus Azure (Joana en català, Elvira en castellà) NO són multilingües: llegeixen els noms propis i termes anglesos amb les regles fonètiques del seu propi idioma, cosa que sona estrany o confon l'oient (p. ex. "Kahneman" o "Silicon Valley" llegits com si fossin paraules catalanes).

**Solució ja integrada:** `veu/pronunciacions.py` conté un diccionari de termes anglesos recurrents (Google, Harvard, feedback, startup, marketing...) que es reescriuen foneticament amb ortografia catalana/castellana NOMÉS per a la síntesi de veu — mai es toca el guió que es desa com a transcripció. Aquest pas és automàtic, no cal fer-hi res.

**El que SÍ has de fer cada dia:** si el guió d'avui conté el títol del llibre en anglès, el nom de l'autor, o qualsevol altre terme anglès que no sigui ja al diccionari base, crea un petit fitxer JSON amb l'aproximació fonètica i passa'l com a paràmetre opcional als scripts:

```json
{"Thinking, Fast and Slow": "Zínquin Fast an Slou", "Daniel Kahneman": "Dàniel Càhneman"}
```

Escriu l'aproximació fent servir ortografia catalana (o castellana per a l'episodi en castellà) que, llegida amb les regles normals d'aquell idioma, soni el més semblant possible a la pronunciació anglesa real. Exemples de tècnica: dobla consonants per marcar èmfasi, evita lletres que no existeixen en la pronunciació catalana/castellana (com la "th"), i pensa en com un locutor de ràdio català/castellà "castellanitzaria" el nom en veu alta.

Desa aquest JSON com a `pron.txt` (o el nom que vulguis) i passa'l com a últim argument:

```bash
bash veu/deixa_pendent.sh <TOKEN> <NN> "<TÍTOL>" "<AUTOR>" "<DESCRIPCIÓ>" "$(realpath guio.txt)" "$(realpath pron.txt)"
bash veu/deixa_pendent_es.sh <TOKEN> "<TÍTULO>" "<AUTOR>" "<DESCRIPCIÓN>" "$(realpath guio_es.txt)" "$(realpath pron_es.txt)"
```

Aquest paràmetre és opcional: si el guió d'avui no té termes anglesos rellevants més enllà dels que ja cobreix el diccionari base, no cal passar-lo.

**Termes recurrents nous:** si detectes un terme anglès que probablement es repetirà en episodis futurs (una empresa, un concepte de negoci habitual), afegeix-lo directament a `DICCIONARI_CA` i `DICCIONARI_ES` dins de `veu/pronunciacions.py` en el mateix commit, perquè quedi cobert per sempre sense haver-ho de repetir cada dia.



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

### Escriure el guió i el disclaimer d'IA

Fitxer de treball: `/home/claude/guio.txt`. Requisits:

- **En català** (o castellà per a `guio_es.txt`), to de podcast conversacional (parla a "tu"), sense encapçalaments ni llistes amb símbols: text corregut que es pugui llegir en veu alta.
- **Mínim 2.600 paraules** (comprova amb `wc -w`; per sota, l'àudio queda curt d'uns 15 min).
- Escriu els números en lletres (la veu llegeix malament les xifres) i evita anglicismes innecessaris; els títols en anglès es diuen tal qual i es tradueixen un cop.
- Cap dada inventada: si no estàs segur d'una xifra o cas del llibre, omet-lo o explica'l de manera genèrica.

**Disclaimer d'IA (OBLIGATORI, a la salutació inicial):** integra de manera natural, dins la primera o segona frase, que el contingut és una anàlisi original generada amb IA — mai amagat ni al final. Exemple de fórmula (adapta-la, no la repeteixis literal cada dia per no sonar robòtic):
> "Hola, i benvingut un dia més al teu podcast de gestió empresarial — un comentari i anàlisi original, escrit i narrat amb intel·ligència artificial. Avui parlem de..."
> (ES: "Hola, y bienvenido un día más a tu podcast de gestión empresarial — un comentario y análisis original, escrito y narrado con inteligencia artificial. Hoy hablamos de...")

**Estructura (IMPORTANT: és una anàlisi comentada, NO un resum seqüencial del llibre):**
1. Salutació amb el disclaimer integrat + presentació del llibre i per què s'ha triat avui
2. Context breu de l'autor
3. La tesi central, **explicada I valorada amb veu pròpia** — no només "el llibre diu X", sinó per què això importa o és discutible avui
4. 3-5 idees clau: per cadascuna, no et limitis a exposar-la — contrasta-la, qüestiona-la si toca, connecta-la amb algun episodi anterior del podcast quan tingui sentit, o dona-hi la teva lectura pròpia
5. **Secció de valoració crítica, NO opcional**: on l'autor generalitza massa, quines dades han envellit malament, quines objeccions raonables té algú que hi discrepeixi. Cada episodi n'ha de tenir una, encara que el llibre t'agradi
6. 4-5 accions pràctiques concretes per aplicar demà
7. Una frase final que sigui una valoració pròpia (no un resum del que ja s'ha dit)
8. Comiat anunciant que demà hi haurà nou episodi

El motiu d'aquest èmfasi: un podcast que és pura seqüència del contingut del llibre s'assembla legalment a un "resum", que la llei de propietat intel·lectual espanyola tracta com a obra derivada. Un podcast que analitza, valora, contrasta i connecta idees pròpies és comentari/crítica original, molt més protegit. Cada episodi ha de sonar com "algú intel·ligent parlant SOBRE el llibre", no "algú explicant el llibre per ordre".

A les descripcions del feed (`<description>` i al paràmetre `<DESCRIPCIÓ>`), acaba amb "Anàlisi i comentari crític del llibre, en català/en español" (NO "Resum i comentari"), coherent amb aquest enfocament.

### Què fa GitHub Actions (Cowork NO ho fa, és automàtic)

Un cop `deixa_pendent.sh`/`deixa_pendent_es.sh` acaben amb "FET", GitHub Actions s'encarrega sol de: generar l'àudio amb Azure (aplicant `veu/pronunciacions.py` per corregir noms anglesos), masteritzar amb `highpass + loudnorm + alimiter` (mai `dynaudnorm` sol, va causar distorsió), inserir l'`<item>` al feed corresponent, actualitzar `README.md` (només per al català), fer commit i push. Cowork no ha de tocar `feed.xml`, `episodes/*.mp3` ni fer cap `git push` d'àudio directament — si ho fas, probablement estàs seguint el pipeline obsolet.

### Informar l'usuari

Missatge breu: número i llibre deixat pendent (en cada idioma), i que GitHub Actions el publicarà en pocs minuts. Sense tecnicismes. No cal esperar activament que acabi ni consultar l'estat del workflow tret que l'usuari ho demani.

## Gestió d'errors

- **Push rebutjat (canvis remots)**: `git pull --rebase origin main` i torna a fer push.
- **403 de l'API de GitHub**: el token no té permisos o ha estat revocat → demana a l'usuari que el revisi; no reintentis a cegues.
- **La veu medium no es descarrega**: usa la x-low de GitHub sense preguntar res.
- **Durada fora de rang després de 2 intents**: publica igualment si està entre 12 i 18 min i menciona-ho a l'usuari.
- Mai no esborris ni reescriguis episodis anteriors del feed: només afegeix.
