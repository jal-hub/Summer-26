# Governance — Summer 2026 (Famille Lecointre)

_Document de gouvernance de l'application de planning familial._
_Dernière mise à jour : 2026-06-17_

---

## 1. Vue d'ensemble

**Quoi** : Application web (PWA) de planning de l'été 2026 pour la famille Lecointre — qui est où, quand, avec quels billets, météo, carte, et impression calendrier pour les grands-parents.

**Qui** : 5 membres — JAL, Carole, Anatole, Auguste, Sixtine.

**Période couverte** : 20 juin → 24 août 2026.

**URL de production** : https://lecointre-summer-2026.netlify.app — **protégée par mot de passe** (Netlify Pro, site-wide).

**Statut** : En production, utilisée par la famille. Considérée terminée (juin 2026), en phase de feedback/usage réel.

---

## 2. Propriété & responsabilités

| Rôle | Personne | Responsabilité |
|---|---|---|
| Owner / Admin | JAL | Décisions produit, données, déploiement, comptes |
| Éditeur de données | JAL (+ Carole en lecture) | Mise à jour de la grille, trajets, billets |
| Utilisateurs lecture | Famille + grands-parents | Consultation programme, calendrier, impression |

JAL est le seul à pouvoir modifier et déployer (accès GitHub + machine locale avec `publish.command`).

---

## 3. Infrastructure & hébergement

| Composant | Service | Détail |
|---|---|---|
| Code source (repo) | GitHub | `jal-hub/Summer-26` (**public**) |
| Hébergement app | Netlify | Site `lecointre-summer-2026`, déploie automatiquement depuis la branche `main` du repo GitHub |
| Hébergement PDFs (billets) | GitHub Pages | `jal-hub.github.io/Summer-26/docs/*` (cross-origin volontaire, voir Codebook) |
| Hébergement avatars | Netlify | `/avatars/*` (same-origin) |
| Librairies externes | jsDelivr CDN | xlsx, jsPDF, html2canvas, Twemoji, Leaflet |
| API météo | Open-Meteo | Gratuite, sans clé |
| Carte | OpenStreetMap | Tuiles via Leaflet, gratuit |

**Chaîne de déploiement** : machine locale → `git push` → GitHub `main` → Netlify rebuild (~30-60 s) + GitHub Pages rebuild (~1-2 min).

---

## 4. Accès & comptes

- **GitHub** : compte `jal-hub` (JAL). Le repo doit rester **public** pour que GitHub Pages serve gratuitement les PDFs.
- **Netlify** : compte JAL (**Pro**), site connecté au repo GitHub (auto-deploy sur push `main`).
- **Mot de passe d'accès** (activé juin 2026) : protection par mot de passe site-wide Netlify (Site configuration → Access & security → Visitor access → Password protection). Un seul mot de passe partagé avec la famille + grands-parents. À redonner aux nouveaux utilisateurs.
- **Authentification git locale** : token/SSH configuré sur la machine de JAL pour pousser sans mot de passe.

> ⚠️ Si le `git push` demande un mot de passe ou échoue en auth, le token GitHub (PAT) a peut-être expiré — le régénérer dans GitHub > Settings > Developer settings.

---

## 5. Workflow de mise à jour

1. Ouvrir le dashboard d'édition : `index.html` en local avec `?edit=1`, OU éditer la source.
2. Modifier la grille (séjours, trajets), les enrichissements, ajouter des PDFs dans `docs/`.
3. Sauvegarder (bouton "Terminer et sauver" → écrit `index.html`).
4. **Double-cliquer `publish.command`** : vérifie la taille (garde-fou), crée un backup horodaté, rafraîchit les hashes PDF, commit + push.
5. Attendre ~1-2 min (Netlify + GitHub Pages se redéploient).
6. Vérifier sur mobile (fermer/rouvrir l'app PWA) et desktop (Cmd+Shift+R).

> Détails techniques du build : voir `CODEBOOK.md`.

---

## 6. Sauvegardes

| Quoi | Où | Fréquence |
|---|---|---|
| Source de vérité (XLSX) | `pCloud/.../Summer Plan/Summer 2026.xlsx` | Manuelle (export depuis le dashboard) |
| Code + données (index.html) | Git history (GitHub) | À chaque push |
| Backups horodatés HTML | `~/Developer/Summer-26/.backups/` (10 derniers) | Auto à chaque `publish.command` |
| Dossier projet complet | pCloud (synchro) | Continue |

---

## 7. Données & confidentialité

**L'app est protégée par mot de passe** (Netlify Pro, site-wide) depuis juin 2026 → un visiteur sans le mot de passe ne peut pas accéder à l'app.

⚠️ **Gap résiduel** : la protection Netlify couvre l'app (index.html + avatars). Mais les **PDFs sont sur GitHub Pages** (autre domaine, non protégé) et le **repo GitHub est public**. Donc les billets restent techniquement accessibles par leur URL directe `jal-hub.github.io/Summer-26/docs/...`, et les données via le repo. Ces documents contiennent : noms complets, références de réservation, numéros Skywards.

**Décision JAL (juin 2026)** : mot de passe sur l'app = porte d'entrée fermée, suffisant pour l'usage familial. Les URLs PDF ne sont jamais affichées publiquement et `robots.txt` interdit l'indexation. Pour une confidentialité totale des billets, il faudrait repo privé + PDFs derrière auth (gros chantier, casse le viewer PDF iOS) — non retenu.

**Si confidentialité requise un jour** : il faudrait passer le repo en privé + un autre mode d'hébergement des PDFs (ce qui casserait le rendu PDF natif sur iOS PWA — voir Codebook, section CDN).

---

## 8. Risques connus & limitations

| Risque | Impact | Mitigation |
|---|---|---|
| Repo public = PDFs exposés | Données perso visibles | Accepté pour usage familial (voir §7) |
| Token GitHub expiré | Push impossible | Régénérer le PAT |
| Dépendance CDN (jsDelivr) | Émojis/libs KO si CDN down | Fallback émoji natif via `alt` ; libs essentielles seulement |
| iOS PWA capricieux (print) | Impression mobile imparfaite | PDF généré côté client (jsPDF) ; impression conseillée depuis desktop |
| Open-Meteo / OSM gratuits | Pas de SLA | Non critique (météo/carte = confort) |
| Single-file ~190KB | Difficile à maintenir à plusieurs | Documenté dans le Codebook |
| Sauvegarde éditeur vide `index.html` (bug FSA) | Perte du fichier local | Sauvegarde blindée (relecture + download de secours) ; garde-fou publish ; backups `.backups/` + Git (voir Codebook §11 Récupération) |
| Renommage repo/dossier | PDFs + sauvegarde cassés | Mettre à jour `DOCS_PAGES_BASE`, `REPO_DIR`, `build_v22.py` ; la sauvegarde se self-heal (re-sélection du fichier) |

---

## 9. Évolution & décisions

- Pas de SaaS / multi-tenant prévu (décision JAL : marché des family organizers difficile, app volontairement sur-mesure).
- Piste future éventuelle : template open-source forkable (sortir le contenu Lecointre dans un `config.js`). ~2h de refacto, non engagé.

---

_Voir `CODEBOOK.md` pour les détails techniques (architecture, modèle de données, fonctions, gotchas)._
