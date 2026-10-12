# Impact Utilaje — brief pentru refacerea logo-ului

Client: **Impact Utilaje**, firmă românească din zona de utilaje de construcții (logo-ul actual arată un încărcător frontal / wheel loader și o roată dințată). Serviciile exacte (închiriere, vânzare, service, lucrări) nu sunt confirmate: nu folosi în logo afirmații despre servicii. Sloganuri doar ca propuneri separate.

Logo-ul actual: `source/logo-original.jpg` (1207×545, JPEG).

## Ce păstrăm (capitalul de brand existent)

- Negru + galben-chihlimbar. Galbenul măsurat în original: aproximativ `#F1A207`.
- Litere grotesk foarte groase, majuscule. Originalul folosește un font foarte apropiat de **Archivo Black** (`fonts/ArchivoBlack-Regular.ttf`).
- Roata dințată galbenă.
- Încărcătorul frontal (wheel loader), negru, orientat spre dreapta cu cupa în față.
- Bara galbenă cu dungi de avertizare (hazard stripes) negru/galben.

## Ce e greșit în original

1. Încărcătorul e un clip-art detaliat cu linii subțiri (profil de anvelope, trepte, oglinzi). La dimensiuni mici devine o pată, nu se poate broda sau tăia în autocolant și probabil nu e desen propriu.
2. Roata dințată și utilajul se bat cap în cap: utilajul acoperă jumătate din roată, iar dinții roții lovesc literele T și E.
3. Spațierea literelor e strânsă și inegală, iar cele două rânduri nu au relație clară de lățime.
4. Bara galbenă e lungă și grea comparativ cu restul.
5. Există doar ca JPEG cu ramă în degradeu. Nu există versiune vectorială, monocromă sau doar simbol (pentru avatar sau favicon).

## Paleta (folosește doar aceste culori)

| Nume | Hex | Rol |
|---|---|---|
| Galben Impact | `#F2A20A` | culoarea de brand, roata, bara, accente |
| Negru Utilaj | `#111111` | text, utilaj, fundaluri închise |
| Gri Oțel | `#4A4F55` | text secundar, linii, aplicații |
| Gri Beton | `#E6E4DF` | fundaluri deschise în aplicații |
| Alb | `#FFFFFF` | versiunea pe fundal închis |

## Fonturi disponibile (`fonts/`, toate au diacritice românești)

Archivo Black (`ArchivoBlack-Regular.ttf`), Archivo Black Italic (`Archivo-BlackItalic.ttf`), Archivo Medium, Saira Condensed Black / ExtraBold, Saira Stencil One, Big Shoulders Display Black, Barlow Condensed ExtraBold / ExtraBold Italic / SemiBold, Barlow Regular / SemiBold / ExtraBold, Teko Bold, Anton, Montserrat Black, IBM Plex Mono SemiBold.

## Unelte (`tools/`)

- `python3 tools/text2path.py FONT TEXT --size N --x X --y Y [--tracking T] [--anchor middle] [--json]` transformă textul în contur vectorial (cu kerning). `--json` dă și lățimea și bbox-ul, ca să poți alinia exact.
- `python3 tools/gear.py --cx --cy --r-outer --r-root --teeth [--hole] [--rotate] [--json]` generează o roată dințată curată.
- `NODE_PATH=/opt/node22/lib/node_modules node tools/render.js OUT_DIR file.svg ... [--sizes 1200,256,64,32] [--bg "#111111"]` randează SVG-uri în PNG. Deschide PNG-urile cu Read și uită-te la ele.
- Pentru layout-uri complexe scrie un script Python care generează SVG-ul (folosind funcțiile din `tools/` prin import cu `sys.path.insert(0, 'tools')`). Salvează scriptul lângă SVG-uri ca să poată fi rulat din nou.

## Reguli pentru fișierele de logo

- SVG valid, cu `xmlns` și `viewBox`, fără `width`/`height` fixe sau cu ele egale cu viewBox.
- **Fără elemente `<text>`**: tot textul convertit în contur cu `text2path.py`.
- Fără imagini raster, fără fonturi externe, fără filtre, fără degradeuri în logo (culori plate, ca să se poată tăia în autocolant, broda sau serigrafia).
- Doar culorile din paletă.
- Spațiu liber în jurul logo-ului în viewBox: cam 4% din lățime pe fiecare parte.
- Fiecare variantă livrează: `color` (pe fundal deschis), `mono-black` (o singură culoare, negru), `reverse` (pentru fundal închis: alb + galben, fundalul NU e inclus în fișier) și, dacă are sens, `icon` (doar simbolul, pătrat).
- Verifică la 32 px că simbolul încă se recunoaște.
- Numele și textele în română cu diacritice corecte (Ș, Ț cu virgulă dedesubt).
