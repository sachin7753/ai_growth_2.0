import requests
import json

API_KEY = "IST.eyJraWQiOiJQb3pIX2FDMiIsImFsZyI6IlJTMjU2In0.eyJkYXRhIjoie1wiaWRcIjpcIjZlMzg2OTI2LTliZTUtNDhkZi1iN2MzLTdkMjVkMzcyOGRlNlwiLFwiaWRlbnRpdHlcIjp7XCJ0eXBlXCI6XCJhcHBsaWNhdGlvblwiLFwiaWRcIjpcImJjNzA1ZTMzLWY5MGQtNGY3MS1iODE0LTA4OGRmZjQyZmQ4N1wifSxcInRlbmFudFwiOntcInR5cGVcIjpcImFjY291bnRcIixcImlkXCI6XCJlOGYzNGUyZS0xYjczLTQwYzktYTJkMS1kMDVmMjNiNzM4YjNcIn19IiwiaWF0IjoxNzcxMzM3NDQ0fQ.aMJeqjxr6HtrEOmGWMx17qRS8VbN4iLFEuufT1rZ24nykEQFQFjWAEN9zE11JKRbRwqEYf_CTekYfXZObaNjgE_jxEp1-Lf1LAS56mq2IBkbKE7-M-o-r6cbwNtGqeYcOOHLeuEjDokvsnbSry6fctQbfhvaC_F4e3peTCB4lo9GyzDhuAe4d0FRHv8hQPkFlEARV-m0_0IbXP-C1h1_zGWRdzCoBVT0Iqd-1-KvwSvVAtwcBZjyxYibEcNA0vwLPORtBjT-2wfoqQ1J8jr41nlszegbgGq5r7FlpTIh1dnzU0RgiF0LwRGisDQTqAMEW60cRupOH6d_DB8bJF5j4A"
SITE_ID = "d0fa869a-cbdb-4975-8a29-d01f7a7c1245"
HEADERS = {"Authorization": API_KEY, "wix-site-id": SITE_ID, "Content-Type": "application/json"}

# Get all collections with their fields
r = requests.get("https://www.wixapis.com/wix-data/v2/collections", headers=HEADERS)
if r.ok:
    collections = r.json().get("collections", [])
    for c in collections:
        cid = c.get("id")
        name = c.get("displayName", "")
        fields = c.get("fields", [])
        print(f"\n{'='*60}")
        print(f"Collection: {cid} ({name})")
        print(f"{'='*60}")
        if fields:
            for f in fields:
                fkey = f.get("key", "")
                fname = f.get("displayName", "")
                ftype = f.get("type", "")
                print(f"  - {fkey:25s} | {ftype:10s} | {fname}")
        else:
            print("  (no field details returned)")

        # Get item count
        qr = requests.post("https://www.wixapis.com/wix-data/v2/items/query", headers=HEADERS, json={
            "dataCollectionId": cid,
            "query": {"paging": {"limit": 1}}
        })
        if qr.ok:
            items = qr.json().get("dataItems", [])
            total = qr.json().get("pagingMetadata", {}).get("total", len(items))
            print(f"  Items count: ~{total if total else len(items)}+")
        else:
            print(f"  (could not query items: {qr.status_code})")
else:
    print("Failed to get collections:", r.status_code, r.text[:300])
