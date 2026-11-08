#!/usr/bin/env python3
"""Minutes GitHub Actions restantes sur TOUT le compte (page de facturation de GitHub).
Lit la clé GH_FACTURATION (droit « Plan » en lecture seule). Lecture seule."""
import datetime as dt, json, os, sys, urllib.request

COMPTE = os.environ.get("GH_COMPTE", "luffy9200-design")
QUOTA = int(os.environ.get("GH_QUOTA", "3000"))   # GitHub Pro : 3 000 minutes par mois
POIDS = {"linux": 1, "windows": 2, "macos": 10}   # minutes Windows et macOS comptent double et ×10

cle = os.environ.get("GH_FACTURATION")
if not cle:
    print("pas de clé GH_FACTURATION"); sys.exit(2)
j = dt.datetime.now(dt.timezone.utc)
req = urllib.request.Request(
    f"https://api.github.com/users/{COMPTE}/settings/billing/usage?year={j.year}&month={j.month}",
    headers={"Authorization": f"Bearer {cle}", "Accept": "application/vnd.github+json",
             "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "compteur-claude"})
try:
    donnees = json.load(urllib.request.urlopen(req, timeout=60))
except Exception as e:
    print(f"erreur {e}"); sys.exit(1)
utilise = 0.0
for l in donnees.get("usageItems", []):
    if l.get("product", "").lower() != "actions" or l.get("unitType", "").lower() != "minutes":
        continue
    if float(l.get("grossAmount", 1) or 0) == 0:   # dépôts publics : gratuits, hors quota
        continue
    sku = l.get("sku", "").lower()
    poids = next((p for k, p in POIDS.items() if k in sku), 1)
    utilise += float(l.get("quantity", 0)) * poids
print(f"Compte : {round(utilise)} min utilisées sur {QUOTA}, reste environ {QUOTA - round(utilise)}")
