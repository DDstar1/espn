import requests
import re
import json

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

def extract_espnfitt(url: str, output_file: str | None = None):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    html = response.text

    match = re.search(
        r"window\['__espnfitt__'\]\s*=\s*({.*?});",
        html,
        re.DOTALL
    )

    if not match:
        raise ValueError(f"__espnfitt__ not found in {url}")

    data = json.loads(match.group(1))

    # Optional file save
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        my_print(f"✅ Saved __espnfitt__ from {url} → {output_file}")

    return data
