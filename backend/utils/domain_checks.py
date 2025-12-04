import tldextract
import random

def quick_domain_checks(url):
    info = tldextract.extract(url)
    domain = f"{info.domain}.{info.suffix}"
    age_days = random.randint(1, 1000)  # Dummy placeholder
    return {"domain": domain, "age_days": age_days}
