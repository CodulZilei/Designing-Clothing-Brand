# NEPĂMÂNTEAN — brief de colecție (100 de piese, băieți și fete)

Colecția: **NEPĂMÂNTEAN** („nu de pe Pământul ăsta”). Brand provizoriu: LĂLÂU. Croieli largi (oversized, baggy) pentru băieți, plus croieli crop și ajustate pentru fete, și accesorii unisex. Lista celor 100 de piese este în `products.py` / `products.json`.

## Inspirația (descrisă în cuvinte, pentru că imaginile nu sunt în repo)

Clientul a trimis trei imagini de pe Pinterest. **Le folosim doar ca direcție de stil. Nimic nu se copiază**: nici compoziția, nici textele lor exacte, nici elementele lor grafice. Toată grafica trebuie să fie originală.

1. **Afiș CRT glitch.** Fotografiat de pe un ecran vechi CRT/LED: peste tot se vede grila de subpixeli RGB și linii orizontale de scanare. Imaginea are o ușoară bombare fisheye și vignetă. Domină cyan, cobalt/indigo și alb pe negru, cu mici accente roz-magenta și roșu-portocaliu. Paginarea e de fanzin: o coloană îngustă în stânga, cu un logo glob din sârmă (wireframe), cercuri de geometrie sacră (floarea vieții) și blocuri de text minuscul. Coloana principală are titluri uriașe, bold, extinse, cu majuscule, un ochi gigant posterizat (albul ochiului, iris negru, punct de lumină alb), paragrafe de text mărunt și dens și un al doilea iris, ca o fotografie macro.
2. **Galaxie cu sclipici.** Spațiu negru adânc, plin de brațe spirale din particule strălucitoare: auriu, alb, albastru electric și puțin roșu-portocaliu. Are stele strălucitoare cu 4 raze, o planetă întunecată cu o margine fină de lumină și, jos, un peisaj extraterestru stâncos cu un lichid auriu care reflectă. Stilul e maximalist, sclipitor, ca o copertă SF pictată cu aerograful în anii 80.
3. **Slogan 3D deformat deasupra unui vârtej.** Vid negru, un vârtej spiral indigo-violet (gaură neagră) din dâre de lumină. Sloganul e scris cu litere grele, extinse, rotunjite, periwinkle și albastru electric, ondulat ca un steag și cu extrudare 3D. Mai are o etichetă-parodie de „clasificare de film”, cu text mărunt și un glob minuscul, și planeta Pământ jos, mânjită cu dâre de pixeli. Peste tot se văd aberație cromatică, moliciunea casetelor VHS și sclipiri mici albe.

**Teme comune:** spațiu cosmic, extratereștri, ochi care privesc, geometrie sacră, simulare și realitate, semnal TV pierdut, glitch, Y2K, rave din anii 90 și misticism cibernetic. Ca registru: fanzin de conspirație, dar cu umor românesc.

## Paleta colecției

| Nume | Hex |
|---|---|
| Vid | `#07070D` |
| Indigo adânc | `#24228A` |
| Albastru electric | `#3D5AFE` |
| Periwinkle | `#6C6CFF` |
| Cyan | `#5FF3FF` |
| Lavandă | `#C9C3FF` |
| Alb crom | `#F2F4FF` |
| Auriu | `#F4B942` |
| Portocaliu semnal | `#FF4D2E` |
| Magenta glitch | `#FF3DA8` |

Se pot folosi nuanțe intermediare și degradeuri între aceste culori. Pământul de la g02 poate avea albastru-verde-maro.

## Fonturi (`fonts/`)

Unbounded Black/SemiBold (titluri extinse, ondulate), Michroma (tehnic, lat), Syne ExtraBold, Dela Gothic One, Rubik Glitch, Rubik Moonrocks (litere cu cratere), Monoton (neon retro), Major Mono Display, VT323 (pixeli CRT), Space Mono Regular/Bold, IBM Plex Mono Medium, Instrument Serif Italic (elegant), Anton, Archivo Black, Archivo Narrow Bold.
**Fără ș/ț/ă**, deci de folosit doar pentru texte fără aceste litere: Audiowide, Bagel Fat One, Orbitron Black, Zen Dots, Silkscreen, Krona One, Rubik Mono One.

## Unelte (`tools/`)

- `python3 tools/text2path.py FONT "TEXT" --size N --x X --y Y [--anchor middle] [--tracking T] [--json]` transformă textul drept în contur vectorial.
- `python3 tools/warp_text.py FONT "TEXT" --size N --x X --y Y --anchor middle --warp wave:0.2:1:0 --warp bulge:0.3 [--json]` face text deformat (arc, wave, bulge, fisheye, perspective, rise). Pentru extrudare 3D desenezi același contur de mai multe ori, cu translatare treptată și culori mai închise în spate.
- Ambele se pot importa din Python: `sys.path.insert(0, 'tools'); from warp_text import warp_text; from text2path import outline`.
- `NODE_PATH=/opt/node22/lib/node_modules node tools/render.js OUT_DIR fișier.svg [--sizes 900,300] [--bg "#111114"]` randează în PNG. Deschide PNG-ul cu Read și uită-te la el.

## Reguli tehnice pentru grafică (`graphics/` și `patterns/`)

- Fiecare grafică e generată de un **script Python** salvat în `graphics/src/<id>.py` (sau `patterns/src/`), care scrie SVG-ul. Scriptul trebuie să poată fi rulat din nou.
- Formate (`viewBox` pe elementul rădăcină `<svg xmlns="http://www.w3.org/2000/svg">`):
  - poster (print mare față/spate): `0 0 1200 1500`
  - marcaj mic (piept, gât, șapcă, fes): `0 0 600 600`, iar textul pe un rând (m06) `0 0 1200 240`
  - pattern pentru imprimeu complet: `0 0 1000 1000`, **perfect repetabil** (ce iese peste o margine reapare pe marginea opusă); fundalul face parte din pattern
- Fundal transparent la grafice: fără dreptunghi pe tot canvasul, cu excepția designurilor care sunt intenționat un „panou” (ecran CRT, mira TV, buletin, panou de plecări), unde forma panoului face parte din print.
- **Fără `<text>`.** Tot textul se transformă în contur cu uneltele de mai sus.
- **Fără `<style>` și fără `class`.** Folosește atribute. Toate `id`-urile încep cu numele fișierului (de exemplu `id="g07-dark-glow"`), ca mai multe grafice să poată sta în același SVG.
- Se pot folosi degradeuri, filtre SVG (blur pentru strălucire, `feTurbulence` pentru zgomot, `feDisplacementMap` pentru deformări), opacități și `mix-blend-mode` (screen) pentru aberația cromatică. Printul DTG sau sublimarea reproduc tonurile continue.
- Fără imagini raster externe. Fără linii mai subțiri de 2,5 unități la lățimea de 1200 (se pierd la print).
- Fiecare fișier rămâne sub ~1,5 MB și se randează în câteva secunde. Pentru particule folosește până la ~8.000 de cercuri.
- Variante de culoare: `-dark` e pentru țesături închise (negru, bleumarin, cărbune, mov închis): cerneluri luminoase, fără suprafețe mari negru-pur în afara panourilor. `-light` e pentru țesături deschise (alb, crem, lavandă, bleu, roz, gri melanj): cerneluri închise (vid, indigo) plus accente. Când se cer amândouă, cele două variante au aceeași compoziție.
- **Originalitate.** Fără logo-uri sau mărci reale (NASA, posturi TV, studiouri de film), fără reproducerea fidelă a blocului oficial de clasificare MPA, fără designul real al buletinului românesc și fără copierea pinurilor. Simbolurile publice (ochiul providenței, floarea vieții, mira de bare de culoare, hărțile de constelații) sunt în regulă.
- Textele sunt în română cu diacritice corecte (ș, ț cu virgulă dedesubt), cu excepția sloganurilor marcate în engleză.
- Semnătura de brand, opțională, în textul mărunt: `LĂLÂU · NEPĂMÂNTEAN · 2026`.

## Verificare

Randează fiecare grafică pe culoarea țesăturii pentru care e făcută: `--bg "#111114"` pentru dark, `--bg "#F5F5F2"` și `--bg "#C9C3E6"` pentru light. Pattern-urile se verifică pe o grilă de 3×3 plăci, ca să vezi îmbinările. Uită-te la ele ca un director de artă. Fă cel puțin 3 runde de corecturi pentru posterele mari și cel puțin 2 pentru marcaje și pattern-uri.
