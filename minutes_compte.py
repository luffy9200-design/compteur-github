#!/usr/bin/env python3
"""Minutes GitHub Actions de TOUT le compte, telles que GitHub les facture.
Tous les chiffres viennent de la facture GitHub du mois (API « billing usage ») :
minutes offertes utilisées, minutes payantes, dollars déjà facturés.
GitHub ne donne pas le plafond du budget d'un compte personnel à l'API (l'adresse « budgets »
n'existe que pour les organisations) : il vient de GH_BUDGET_ACTIONS (workflow minutes.yml), choisi par Luffy.
Reste = minutes offertes non utilisées + (budget − dollars déjà facturés) / prix d'une minute Linux.
Lit la clé GH_FACTURATION (droit « Plan » en lecture seule). Lecture seule."""
import datetime as dt, json, os, sys, urllib.request

COMPTE = os.environ.get("GH_COMPTE", "luffy9200-design")
QUOTA = int(os.environ.get("GH_QUOTA", "3000"))   # GitHub Pro : 3 000 minutes offertes par mois
POIDS = {"linux": 1, "windows": 2, "macos": 10}   # minutes Windows et macOS comptent double et ×10
PRIX_LINUX = 0.006                                 # $ par minute Linux, si la facture ne le donne pas
BUDGET = float(os.environ.get("GH_BUDGET_ACTIONS") or 0)   # $ autorisés au-delà des minutes offertes

cle = os.environ.get("GH_FACTURATION")
if not cle:
    print("pas de clé GH_FACTURATION"); sys.exit(2)


def lire(chemin):
    req = urllib.request.Request(
        f"https://api.github.com/{chemin}",
        headers={"Authorization": f"Bearer {cle}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "compteur-claude"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def nombre(n):
    return f"{n:,}".replace(",", " ")


def dollars(x):
    return f"{x:.2f}".replace(".", ",") + " $"


j = dt.datetime.now(dt.timezone.utc)
try:
    donnees = lire(f"users/{COMPTE}/settings/billing/usage?year={j.year}&month={j.month}")
except Exception as e:
    print(f"erreur {e}"); sys.exit(1)

utilisees, paye, prix = 0.0, 0.0, None
for l in donnees.get("usageItems", []):
    if l.get("product", "").lower() != "actions":
        continue
    paye += float(l.get("netAmount", 0) or 0)        # ce que GitHub facture au-delà des minutes offertes
    if l.get("unitType", "").lower() != "minutes":
        continue
    if float(l.get("grossAmount", 1) or 0) == 0:     # dépôts publics : gratuits, hors quota
        continue
    sku = l.get("sku", "").lower()
    poids = next((p for k, p in POIDS.items() if k in sku), 1)
    utilisees += float(l.get("quantity", 0)) * poids
    if "linux" in sku and float(l.get("pricePerUnit", 0) or 0) > 0:
        prix = float(l["pricePerUnit"])
prix = prix or PRIX_LINUX

utilisees = round(utilisees)
offertes = min(QUOTA, utilisees)
payantes = max(0, utilisees - QUOTA)
reste = QUOTA - offertes
debut = (j.replace(day=1) + dt.timedelta(days=32)).replace(day=1)

payables = max(0, int((BUDGET - paye) / prix))
total = reste + payables
mois = ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
        'septembre', 'octobre', 'novembre', 'décembre'][debut.month]
texte = f"reste environ {total} min"   # chiffre sans espace : lu aussi par l ancien mod
if reste:
    texte += f" ({nombre(reste)} offertes + {nombre(payables)} avec le budget de {BUDGET:g} $)"
else:
    texte += f" sur le budget de {BUDGET:g} $ ({dollars(paye)} déjà utilisés)"
    texte += f" · offertes {nombre(offertes)}/{nombre(QUOTA)} épuisées, de retour le 1er {mois}"
print(f"Compte : {texte}")
