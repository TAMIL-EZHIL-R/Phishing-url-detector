import re
from urllib.parse import urlparse

def extract_features(url):
    features = []

    # 1. Having IP address
    features.append(1 if re.search(r'\d+\.\d+\.\d+\.\d+', url) else 0)

    # 2. URL Length
    features.append(1 if len(url) > 75 else 0)

    # 3. Shortening service
    features.append(1 if re.search(r'bit\.ly|tinyurl|goo\.gl', url) else 0)

    # 4. Having @ symbol
    features.append(1 if "@" in url else 0)

    # 5. Double slash redirect
    features.append(1 if urlparse(url).path.count("//") > 0 else 0)

    # 6. Prefix/Suffix (-)
    features.append(1 if "-" in urlparse(url).netloc else 0)

    # 7. Subdomain count
    features.append(1 if urlparse(url).netloc.count(".") > 2 else 0)

    # 8. HTTPS
    features.append(1 if url.startswith("https") else 0)

    # 9. Suspicious words
    features.append(1 if re.search(r'login|secure|update|bank|free', url.lower()) else 0)

    # 🔁 Repeat / pad to match dataset size (example: 30 features)
    while len(features) < 30:
        features.append(0)

    return features
