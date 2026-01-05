import os
import requests
from datetime import datetime
from icalendar import Calendar, Event

def sync():
    # 从 GitHub 环境变量中读取你的 Token 和 ID
    token1 = os.environ.get("TOKEN_1")
    ids1 = os.environ.get("IDS_1", "").split(",")
    token2 = os.environ.get("TOKEN_2")
    ids2 = os.environ.get("IDS_2", "").split(",")
    
    cal = Calendar()
    cal.add('X-WR-CALNAME', 'Notion云端同步')
    total = 0

    configs = [
        {"name": "空间1", "token": token1, "ids": ids1},
        {"name": "空间2", "token": token2, "ids": ids2}
    ]

    for acc in configs:
        if not acc["token"]: continue
        headers = {
            "Authorization": f"Bearer {acc['token'].strip()}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        for db_id in [i.strip().replace("-", "") for i in acc["ids"] if i.strip()]:
            url = f"https://api.notion.com/v1/databases/{db_id}/query"
            res = requests.post(url, headers=headers)
            if res.status_code == 200:
                pages = res.json().get("results", [])
                for page in pages:
                    props = page.get("properties", {})
                    title = "无题"
                    for p in props.values():
                        if p.get("type") == "title" and p.get("title"):
                            title = "".join([t.get("plain_text", "") for t in p["title"]])
                            break
                    for p in props.values():
                        if p.get("type") == "date" and p.get("date") and p["date"]:
                            d = p["date"]
                            ev = Event()
                            ev.add('summary', title)
                            ev.add('dtstart', datetime.fromisoformat(d["start"].replace('Z', '+00:00')))
                            ev.add('dtend', datetime.fromisoformat((d.get("end") or d["start"]).replace('Z', '+00:00')))
                            cal.add_component(ev)
                            total += 1
    
    with open("calendar.ics", "wb") as f:
        f.write(cal.to_ical())
    print(f"✅ 同步完成，共发现 {total} 个日程")

if __name__ == "__main__":
    sync()
