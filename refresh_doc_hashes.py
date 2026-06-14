#!/usr/bin/env python3
"""
refresh_doc_hashes.py — Met à jour DATA.doc_hashes dans index.html

Pourquoi : quand un PDF dans docs/ est remplacé, son contenu change mais
son URL relative reste la même → le cache navigateur sert l'ancien.

Solution : ajouter ?v=<MD5-hash> aux URLs des PDFs. Comme l'URL change quand
le contenu change, le navigateur considère que c'est un nouveau fichier
et le re-télécharge.

Servir depuis Netlify (même origine) plutôt que jsdelivr CDN : pas de CDN
externe à purger, pas de propagation aléatoire, Netlify a déjà Cache-Control
no-cache sur /docs/* (config netlify.toml).

Ce script :
  1. Scanne tous les fichiers dans docs/ + calcule MD5 (8 chars)
  2. Met à jour DATA.doc_hashes dans index.html in-place
  3. Idempotent : si rien n'a changé, n'écrit pas le fichier

Appelé automatiquement par publish.command avant chaque commit.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
INDEX = REPO_DIR / "index.html"
DOCS_DIR = REPO_DIR / "docs"

def build_doc_hashes():
    """Scanne docs/ et calcule MD5 8 chars pour chaque fichier.
    Stocké avec deux clés (avec et sans préfixe "docs/") pour matcher
    quel que soit le format en DATA."""
    if not DOCS_DIR.exists():
        return {}
    out = {}
    for p in sorted(DOCS_DIR.rglob("*")):
        if p.is_file() and not p.name.startswith("."):
            rel = str(p.relative_to(DOCS_DIR)).replace("\\", "/")
            h = hashlib.md5(p.read_bytes()).hexdigest()[:8]
            out[rel] = h
            out[f"docs/{rel}"] = h
    return out

def main():
    if not INDEX.exists():
        print(f"ERR: {INDEX} introuvable", file=sys.stderr)
        sys.exit(1)

    new_hashes = build_doc_hashes()
    src = INDEX.read_text(encoding="utf-8")

    # Cherche le champ doc_hashes dans DATA et le remplace.
    # Pattern : "doc_hashes":{...} jusqu'au }; final (avec [^}] et nesting JSON)
    # Plus simple : on extrait DATA en entier, on modifie, on re-injecte.
    m = re.search(r'let DATA\s*=\s*(\{.*?\});(?=\s*\n\s*const TODAY)',
                  src, re.DOTALL)
    if not m:
        # Fallback : pattern moins strict
        m = re.search(r'let DATA\s*=\s*(\{.*?\});', src, re.DOTALL)
        if not m:
            print("ERR: pattern 'let DATA = {...};' introuvable", file=sys.stderr)
            sys.exit(1)

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"ERR: DATA JSON invalide : {e}", file=sys.stderr)
        sys.exit(1)

    old_hashes = data.get("doc_hashes", {})
    if old_hashes == new_hashes:
        print(f"✓ doc_hashes déjà à jour ({len(new_hashes)//2} PDFs)")
        return

    # Identifie les changements pour le log
    old_keys = {k: v for k, v in old_hashes.items() if not k.startswith("docs/")}
    new_keys = {k: v for k, v in new_hashes.items() if not k.startswith("docs/")}
    added   = set(new_keys) - set(old_keys)
    removed = set(old_keys) - set(new_keys)
    changed = {k for k in set(new_keys) & set(old_keys) if old_keys[k] != new_keys[k]}

    if added:   print(f"  + {len(added)} ajoutés : " + ", ".join(sorted(added)[:3]) + ("..." if len(added)>3 else ""))
    if removed: print(f"  - {len(removed)} supprimés : " + ", ".join(sorted(removed)[:3]) + ("..." if len(removed)>3 else ""))
    if changed: print(f"  ~ {len(changed)} modifiés : " + ", ".join(sorted(changed)[:3]) + ("..." if len(changed)>3 else ""))

    # Met à jour DATA et re-sérialise
    data["doc_hashes"] = new_hashes
    new_data_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    # Replace DATA dans le HTML — utilise FONCTION (pas string) pour éviter
    # l'interprétation des $ comme backrefs.
    new_src = re.sub(
        r'let DATA\s*=\s*\{.*?\};(?=\s*\n\s*const TODAY)',
        lambda _: f"let DATA = {new_data_str};",
        src,
        count=1,
        flags=re.DOTALL
    )
    if new_src == src:
        # Fallback sans le lookahead
        new_src = re.sub(
            r'let DATA\s*=\s*\{.*?\};',
            lambda _: f"let DATA = {new_data_str};",
            src,
            count=1,
            flags=re.DOTALL
        )
    if new_src == src:
        print("ERR: replacement DATA introuvable", file=sys.stderr)
        sys.exit(1)

    INDEX.write_text(new_src, encoding="utf-8")
    print(f"✓ doc_hashes mis à jour ({len(new_hashes)//2} PDFs au total)")

if __name__ == "__main__":
    main()
