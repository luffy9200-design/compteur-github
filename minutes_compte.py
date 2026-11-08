#!/usr/bin/env python3
"""Minutes GitHub Actions qui restent VRAIMENT sur tout le compte.
Reste = minutes offertes non utilisées + minutes encore payables avec le budget « Actions ».
Lit la clé GH_FACTURATION (droit « Plan » en lecture seule). Lecture seule."""
import datetime as dt, json, os, sys, urllib.error, urllib.request

COMPTE = os.environ.get("GH_COMPTE", "luffy9200-design")
QUOTA = int(os.environ.get("GH_QUOTA", "3000"))   # GitHub Pro : 3 000 minutes offertes par mois
POIDS = {"linux": 1, "windows": 2, "macos": 10}   # minutes Windows et macOS comptent double et ×10
PRIX_LINUX = 0.006                                 # $ par minute Linux, si la facture ne le donne pas

cle = os.environ.get("GH_FACTURATION")
if not cle:
    print("pas de clé GH_FACTURATION"); sys.exit(2)


def lire(chemin):
    req = urllib.request.Request(
        f"https://api.github.com/{chemin}",
        headers={"Authorization": f"Bearer {cle}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "compteur-claude"})
    return json.load(urllib.request.urlopen(req, timeout=60))


j = dt.datetime.now(dt.timezone.utc)
try:
    donnees = lire(f"users/{COMPTE}/settings/billing/usage?year={j.year}&month={j.month}")
except Exception as e:
    print(f"erreur {e}"); sys.exit(1)

utilise, paye, prix = 0.0, 0.0, None
for l in donnees.get("usageItems", []):
    if l.get("product", "").lower() != "actions":
        continue
    paye += float(l.get("netAmount", 0) or 0)        # déjà facturé au-delà des minutes offertes
    if l.get("unitType", "").lower() != "minutes":
        continue
    if float(l.get("grossAmount", 1) or 0) == 0:     # dépôts publics : gratuits, hors quota
        continue
    sku = l.get("sku", "").lower()
    poids = next((p for k, p in POIDS.items() if k in sku), 1)
    utilise += float(l.get("quantity", 0)) * poids
    if "linux" in sku and float(l.get("pricePerUnit", 0) or 0) > 0:
        prix = float(l["pricePerUnit"])
prix = prix or PRIX_LINUX
offertes = max(0, QUOTA - round(utilise))

# Budget « Actions » : dollars autorisés par Luffy au-delà des minutes offertes.
budget, source = None, ""
try:
    for b in lire(f"users/{COMPTE}/settings/billing/budgets").get("budgets", []):
        skus = b.get("budget_product_skus") or [b.get("budget_product_sku") or ""]
        if any("actions" in str(s).lower() for s in skus):
            budget = (budget or 0) + float(b.get("budget_amount", 0) or 0)
    source = "budget lu sur GitHub"
except urllib.error.HTTPError as e:
    source = f"budget illisible par l'API ({e.code})"
except Exception as e:
    source = f"budget illisible ({e})"
if budget is None and os.environ.get("GH_BUDGET_ACTIONS"):
    budget, source = float(os.environ["GH_BUDGET_ACTIONS"]), "budget noté à la main"

if budget is None:
    print(f"Compte : reste environ {offertes} min ({source} : minutes payantes non comptées)")
else:
    payables = max(0, int((budget - paye) / prix))
    print(f"Compte : reste environ {offertes + payables} min "
          f"({offertes} offertes + {payables} payables avec le budget de {budget:g} $, {source})")
