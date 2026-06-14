# Codebook — Summer 2026 (Famille Lecointre)

_Documentation technique de l'application._
_Dernière mise à jour : 2026-06-11_

---

## 1. Architecture en une phrase

Une **SPA mono-fichier** (`index.html`, ~190 KB, HTML + CSS + JS inline, zéro framework) générée par un **template + script Python** qui injecte les données, déployée sur **Netlify** depuis **GitHub**, avec les PDFs servis par **GitHub Pages** (cross-origin volontaire).

---

## 2. Inventaire des fichiers

Repo `jal-hub/jal-summer-2026` :

| Fichier | Rôle |
|---|---|
| `index.html` | **L'app déployée** (généré). Contient tout : UI, logique, et les données (`let DATA = {...}`). |
| `netlify.toml` | Config Netlify : `publish = "."` + headers `no-cache` sur HTML/docs/avatars. |
| `robots.txt` | `Disallow: /` (anti-indexation, sécurité par obscurité). |
| `apple-touch-icon.png` | Icône PWA (écran d'accueil iOS). |
| `publish.command` | Script 1-clic : garde-fou taille + backup + refresh hashes + commit + push. |
| `refresh_doc_hashes.py` | Recalcule les MD5 des PDFs et les injecte dans `DATA.doc_hashes` (cache-busting). Appelé par `publish.command`. |
| `docs/*.pdf` | Billets/e-tickets (servis via GitHub Pages). |
| `avatars/*.png` | Photos des 5 membres (servis via Netlify). |
| `.backups/` | Backups horodatés de `index.html` (10 derniers, auto). |

Outils de build (hors repo, dans l'espace de travail / pCloud) :

| Fichier | Rôle |
|---|---|
| `template_v22.html` | **Le template source** : tout le code, avec un placeholder `__DATA_PLACEHOLDER__`. C'est ici qu'on édite le CODE. |
| `build_v22.py` | Lit le template + extrait `DATA` de l'`index.html` existant + ré-injecte → nouveau `index.html`. Détecte avatars, calcule les hashes (avatars, icon, PDFs). |

> ⚠️ **Distinction clé** : on édite le **code** dans `template_v22.html`, mais les **données** vivent dans `index.html`. Le build fusionne les deux.

---

## 3. Modèle de données (`DATA`)

Objet JSON injecté dans `index.html`. "Grille-first" : la grille jour×personne est la source, les séjours/trajets sont **recalculés en JS** à la volée.

```
DATA = {
  meta:    { title, family, dateStart, dateEnd },
  users:   [ { id, nom, ramp, initials, photo? }, ... ],   // 5 membres
  d:       [ ["06-20","Sa", actA, actAu, actS, actC, actJ], ... ],  // grille : 1 ligne/jour
  c:       { "2026-06-28|jal": "note trajet brute...", ... },        // commentaires/détails trajets
  enrichissements: { "Gonfaron": { adresse, gmapsUrl, contact, notes, docs[] }, ... },
  docs_trajets:    { "2026-06-28|jal": [ {label, url}, ... ], ... }, // PDFs liés aux trajets
  doc_hashes:      { "Flight X.pdf": "ab12cd34", "docs/Flight X.pdf": "ab12cd34", ... }  // cache-bust
}
```

**Grille `d`** : chaque ligne = `[mmdd, jourAbbr, Anatole, Auguste, Sixtine, Carole, JAL]`.
Mapping colonnes : `USER_COL_IDX = { anatole:2, auguste:3, sixtine:4, carole:5, jal:6 }`.

**Couleurs membres (`ramp`)** : jal=teal, carole=pink, anatole=blue, auguste=green, sixtine=purple.

---

## 4. Routes (paramètres URL)

| URL | Vue |
|---|---|
| `/` | Home : avatars, widget "Aujourd'hui", liens Carte/Impression, calendrier famille |
| `?user=jal` | Programme individuel (cartes séjour/trajet) |
| `?map=1` | Carte Leaflet des séjours |
| `?print=1` | Vue calendrier 3 pages (→ génère le PDF) |
| `?edit=1` | Éditeur de grille (réservé JAL) |
| `?day=2026-07-15` | Auto-déplie + scroll vers une carte précise |

Dispatch dans `render()`. Une classe est posée sur `<body>` selon la vue (`map-mode`, `print-mode`, `edit-mode`).

---

## 5. Logique métier — fonctions clés

**Calcul séjours/trajets (depuis la grille)**
- `computeStretches(userId)` — regroupe les jours consécutifs d'un même séjour.
- `computeItems(userId)` — produit la liste ordonnée séjours + trajets, + "bridges" Dubai entre événements.
- `isRoutine()` / `isTrajet()` / `isTentatif()` / `cleanTitre()` / `visualTitre()` — classification des activités.
- `parseTrajetNote(note)` — extrait d'une note brute : n° vol, compagnie, horaires, origine/destination (IATA), réf, coût.

**Émojis** (voir §6)
- `getSejourEmoji()`, `getGroupEmoji()`, `getTrajetEmoji()`, `getActivityGroup()`
- `twemojify(text)` — convertit les émojis du set en `<img>` Twemoji (SVG).

**Affichage**
- `renderHome()`, `renderProgramme()`, `renderMap()`, `renderPrint()`, `renderEdit()`
- `renderCard()`, `renderBanner()`, `renderTodayWidget()`, `getUserTodayStatus()`, `renderCalendar()`

**Documents / partage / export**
- `resolveDocUrl(rawUrl)` — résout les URLs : `docs/*` → GitHub Pages, `avatars/*` → Netlify, + `?v=hash`.
- `buildTrajetIcs()` / `addTrajetToCalendar()` — génère un `.ics` (avec rappels VALARM).
- `normalizeFr24Number(vol)` — n° de vol pour FlightRadar24 (strip leading zeros : EK089 → ek89).
- `downloadCalendarPdf()` — génère le PDF 3 pages via jsPDF + html2canvas.
- `buildShareTextForItem()` / `shareItem()` / `sharePdf()` — partage WhatsApp/AirDrop.
- `geocode()` / `fetchForecast()` / `renderWeatherBlock()` — météo Open-Meteo (cache localStorage).

**Sauvegarde**
- `saveDashboardHtml()` — écrit `index.html` via File System Access API (fallback download). Regex `let DATA = {...};` remplacée via **fonction** (pas string, pour éviter l'interprétation des `$`).
- `exportXlsx()` — export du backup Excel.

---

## 6. Système d'émojis

Émojis affichés **à la fin** des titres. Deux niveaux :

**Cas spéciaux par lieu** (`getSejourEmoji`) :
| Lieu | Émoji | Raison |
|---|---|---|
| Dublin | 🩰✨ | Finale coupe du monde de ballet (Sixtine danse) |
| Les Roches | 🛎️ | École hôtelière (Anatole) |
| Fléac | 🏰 | Château familial |
| Lyon | 🦁 | Jeu de mots Lyon → lion |
| Boulot (Dubai/Geneva) | 💼 | Travail |
| Mariage A&J | 💒 | Mariage |
| Chantier Ste-Marguerite | 🔨 | Chantier jeune |

**Par groupe géographique** (`GROUP_EMOJI`, sinon) :
| Groupe | Émoji | Couleur carte |
|---|---|---|
| atlantique (Sud-Ouest) | 🏖️ | bleu |
| med (Sud/Méditerranée) | ☀️ | orange |
| montagne | 🏔️ | vert |
| etranger | ✈️ | violet |
| evenement | 🎉 | gris |

**Trajets** : ✈️ vol, 🚆 train, 🚗 voiture (`TRAJET_EMOJI`).

**Rendu Twemoji** : `twemojify()` remplace UNIQUEMENT le set connu `APP_EMOJIS` par des `<img>` SVG depuis jsDelivr (`jdecked/twemoji@15.1.0`). Fallback : `alt` = émoji natif si le CDN échoue.
> ⚠️ Tout nouvel émoji affiché **doit** être ajouté à `APP_EMOJIS`, sinon il reste en rendu natif (incohérent).
> Le **PDF imprimé** n'utilise PAS twemojify (émojis natifs sobres, voulu).

---

## 7. Hébergement / CDN — qui sert quoi

| Ressource | Hébergeur | Pourquoi |
|---|---|---|
| App (`index.html`, avatars) | Netlify (same-origin) | Cache no-cache, déploiement rapide |
| PDFs (`docs/*`) | **GitHub Pages** (cross-origin) | iOS PWA standalone ouvre les liens cross-origin dans Safari natif (viewer PDF complet avec retour). Same-origin bloquerait sans bouton retour. |
| Libs (xlsx, jsPDF, html2canvas, Twemoji, Leaflet) | jsDelivr | CDN fiable |
| Météo | Open-Meteo | Gratuit, sans clé |
| Carte | OpenStreetMap (via Leaflet) | Gratuit |

**Cache-busting PDFs** : `?v=<MD5>` ajouté par `resolveDocUrl`. Les hashes sont rafraîchis par `refresh_doc_hashes.py` à chaque publish → un PDF modifié = nouvelle URL = pas de cache périmé.

---

## 8. Build & déploiement

```
template_v22.html  (CODE)  ─┐
                            ├─►  build_v22.py  ─►  index.html  ─►  publish.command  ─►  GitHub  ─►  Netlify + GitHub Pages
index.html (DATA existant) ─┘
```

`publish.command` (séquence) :
1. Garde-fou : refuse si `index.html` < 1000 octets.
2. Backup horodaté dans `.backups/` (garde les 10 derniers).
3. `refresh_doc_hashes.py` : recalcule les hashes PDF.
4. `git add` + `commit` + `push` des chemins publiables.
5. Netlify (~30-60 s) + GitHub Pages (~1-2 min) se redéploient.

> Pour modifier le CODE : éditer `template_v22.html`, puis `build_v22.py` (nécessite l'`index.html` existant comme source de données), puis copier vers le repo, puis `publish.command`.

---

## 9. Gotchas & leçons apprises (important)

- **iOS Safari PWA standalone** : n'imprime pas fiablement via `window.print()` (orientation ignorée, pages blanches). → PDF généré côté client (jsPDF + html2canvas).
- **PDFs sur iOS PWA** : un lien **same-origin** s'ouvre sans bouton retour (dead-end). Un lien **cross-origin** (GitHub Pages) ouvre Safari natif. → docs servis par GitHub Pages.
- **jsDelivr cache CDN** : ignore les query strings `?v=`, propagation post-purge non fiable. → ne PAS l'utiliser pour des fichiers qui changent (PDFs). OK pour les libs versionnées.
- **statically.io** : ne sert pas le contenu de ce repo (testé, abandonné).
- **`String.replace(re, str)` + `$`** : si la chaîne de remplacement contient `$&`/`$1`, ils sont interprétés. → toujours passer une **fonction** au lieu d'une string (cas `saveDashboardHtml`).
- **Collision de `const`** : dans un fichier mono, redéclarer un nom existant (ex. `DOW_LONG_FR`) plante TOUT le JS → écran blanc. **Toujours valider** : `node -e "new Function(code)"` avant de pousser.
- **Émoji hors `APP_EMOJIS`** : reste en rendu natif (pas twemojifié) = incohérence visuelle.
- **Dark mode supprimé** : mode clair forcé (`color-scheme: light`), dégradé estival sur toute l'app.

---

## 10. Conventions

- Mode clair uniquement. Dégradé ciel→sable global. Cartes en verre dépoli.
- `YEAR_DEFAULT = 2026` codé en dur (8 endroits) — à factoriser via `DATA.meta` pour réutiliser en 2027.
- Dates au format ISO `YYYY-MM-DD` (comparaison lexicographique sûre).
- Échappement HTML systématique via `esc()` ; `twemojify()` échappe avant d'insérer.
- Helper DOM maison `el(tag, props, ...kids)` partout (pas de framework).

---

_Voir `GOVERNANCE.md` pour la gouvernance (accès, déploiement, données, risques)._
