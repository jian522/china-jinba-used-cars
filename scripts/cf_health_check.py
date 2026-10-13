"""低频只读健康检查；不清缓存、不改规则、不模拟高并发。Python 3.12。"""
import argparse
import datetime
import json
import pathlib
import time
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proxy", help="可选 HTTPS 代理，例如 http://127.0.0.1:7890")
    parser.add_argument("--output", type=pathlib.Path,
                        default=ROOT / ".workbuddy" / "cf_ops" / "health_latest.json")
    args = parser.parse_args()
    session = requests.Session()
    session.trust_env = False
    session.headers["User-Agent"] = "JinbaHealthCheck/1.0"
    if args.proxy:
        session.proxies["https"] = args.proxy
    probes = [("https://jinbacars.com/" + lang + "/contact/", 200) for lang in ("en", "zh", "ru", "ar")]
    probes += [("https://jinbacars.com/en/cars/", 200),
               ("https://jinbacars.com/assets/design-system.css", 200),
               ("https://jinbacars.com/assets/design-system.css", 200),
               ("https://www.jinbacars.com/assets/design-system.css", 200),
               ("https://www.jinbacars.com/assets/design-system.css", 200),
               ("https://jinbacars.com/cars.html?utm_source=healthcheck", 301),
               ("https://jinbacars.com/__jinba_health_missing__.webp", 404)]
    rows = []
    alerts = []
    for url, expected in probes:
        row = {"url": url, "utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        try:
            response = session.get(url, timeout=(5, 20), allow_redirects=False)
            row.update(status=response.status_code, expected=expected,
                       elapsed_to_headers_seconds=round(response.elapsed.total_seconds(), 3),
                       decoded_body_bytes=len(response.content),
                       headers={k.lower(): v for k, v in response.headers.items()
                                if k.lower() in {"cf-ray", "cf-cache-status", "age", "cache-control",
                                                 "location", "server", "etag", "content-encoding"}})
            if response.status_code != expected:
                alerts.append(f"{url}: expected {expected}, received {response.status_code}")
            if expected == 404 and (response.headers.get("Age") or response.headers.get("CF-Cache-Status") == "HIT"):
                alerts.append(f"{url}: error response unexpectedly cached")
            if expected == 301 and response.headers.get("Location") != "https://jinbacars.com/en/cars/?utm_source=healthcheck":
                alerts.append(f"{url}: unexpected redirect destination/query")
            if "design-system.css" in url and response.status_code == 200:
                cache = response.headers.get("Cache-Control", "")
                if "max-age=7200" not in cache or "s-maxage=86400" not in cache:
                    alerts.append(f"{url}: static TTL differs from current policy")
                if response.headers.get("CF-Cache-Status") in {"BYPASS", "DYNAMIC"}:
                    alerts.append(f"{url}: public static asset bypasses edge cache")
        except requests.RequestException as exc:
            row["error"] = type(exc).__name__
            alerts.append(f"{url}: {type(exc).__name__}")
        rows.append(row)
        time.sleep(1)
    report = {"checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Single monitoring location; not a global buyer-access or seven-day traffic measurement",
              "requests": rows, "alerts": alerts}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"requests": len(rows), "alerts": alerts, "report": str(args.output)}, ensure_ascii=False))
    return bool(alerts)


if __name__ == "__main__":
    raise SystemExit(main())
