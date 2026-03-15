import requests

API_KEY = "IST.eyJraWQiOiJQb3pIX2FDMiIsImFsZyI6IlJTMjU2In0.eyJkYXRhIjoie1wiaWRcIjpcIjZlMzg2OTI2LTliZTUtNDhkZi1iN2MzLTdkMjVkMzcyOGRlNlwiLFwiaWRlbnRpdHlcIjp7XCJ0eXBlXCI6XCJhcHBsaWNhdGlvblwiLFwiaWRcIjpcImJjNzA1ZTMzLWY5MGQtNGY3MS1iODE0LTA4OGRmZjQyZmQ4N1wifSxcInRlbmFudFwiOntcInR5cGVcIjpcImFjY291bnRcIixcImlkXCI6XCJlOGYzNGUyZS0xYjczLTQwYzktYTJkMS1kMDVmMjNiNzM4YjNcIn19IiwiaWF0IjoxNzcxMzM3NDQ0fQ.aMJeqjxr6HtrEOmGWMx17qRS8VbN4iLFEuufT1rZ24nykEQFQFjWAEN9zE11JKRbRwqEYf_CTekYfXZObaNjgE_jxEp1-Lf1LAS56mq2IBkbKE7-M-o-r6cbwNtGqeYcOOHLeuEjDokvsnbSry6fctQbfhvaC_F4e3peTCB4lo9GyzDhuAe4d0FRHv8hQPkFlEARV-m0_0IbXP-C1h1_zGWRdzCoBVT0Iqd-1-KvwSvVAtwcBZjyxYibEcNA0vwLPORtBjT-2wfoqQ1J8jr41nlszegbgGq5r7FlpTIh1dnzU0RgiF0LwRGisDQTqAMEW60cRupOH6d_DB8bJF5j4A"
SITE_ID = "d0fa869a-cbdb-4975-8a29-d01f7a7c1245"
HEADERS = {"Authorization": API_KEY, "wix-site-id": SITE_ID, "Content-Type": "application/json"}

r = requests.post("https://www.wixapis.com/wix-data/v2/items/query", headers=HEADERS, json={
    "dataCollectionId": "Import1",
    "query": {"paging": {"limit": 100}}
})
print("Status:", r.status_code)
if r.ok:
    data = r.json()
    items = data.get("dataItems", [])
    total = data.get("pagingMetadata", {}).get("total", "unknown")
    print(f"Total items returned: {len(items)}")
    print(f"Total count (metadata): {total}")
    print()
    for i, item in enumerate(items):
        d = item.get("data", {})
        name = d.get("childName", "N/A")
        cid = d.get("childId", "N/A")
        _id = d.get("_id", "N/A")
        print(f"  {i+1}. {name:20s} | childId: {cid:6s} | _id: {_id}")
else:
    print(r.text[:500])
