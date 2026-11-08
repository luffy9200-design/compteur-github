import json, os, urllib.request, urllib.error
cle = os.environ["GH_FACTURATION"]; u = "luffy9200-design"
for c in [f"users/{u}/settings/billing/budgets", "user/settings/billing/budgets",
          f"users/{u}/settings/billing/usage/summary?product=actions",
          f"users/{u}/settings/billing/budgets?scope=user", f"organizations/{u}/settings/billing/budgets"]:
    r = urllib.request.Request("https://api.github.com/" + c, headers={"Authorization": f"Bearer {cle}",
        "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "compteur-claude"})
    try:
        d = json.load(urllib.request.urlopen(r, timeout=60)); print(c, "200", json.dumps(d)[:1500])
    except urllib.error.HTTPError as e:
        print(c, e.code, e.read()[:200])
