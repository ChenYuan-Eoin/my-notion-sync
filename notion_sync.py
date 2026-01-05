import os
import requests
from datetime import datetime, timedelta
from icalendar import Calendar, Event

def parse_notion_date(date_str):
    """处理 Notion 的日期格式：可能是 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS"""
    if not date_str:
        return None
    try:
        # 如果包含时间
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # 如果只是日期，返回 date 对象
            return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return None

def sync():
    token1 = os.environ.get("TOKEN_1")
    ids1 = os.environ.get("IDS_1", "").split(",")
    token2 = os.environ.get("TOKEN_2")
    ids2 = os.environ.get("IDS_2", "").split(",")
    
    cal = Calendar()
    cal.add('prodid', '-//Notion Gantt Sync//')
    cal.add('version', '2.0')
    cal.add('X-WR-CALNAME', 'Notion生产力聚合')
    total = 0

    configs = [
        {"name": "虚胖而已", "token": token1, "ids": ids1},
        {"name": "虚胖校长", "token": token2, "ids": ids2}
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
                    
                    # 1. 提取标题
                    title = "无题"
                    for p in props.values():
                        if p.get("type") == "title" and p.get("title"):
                            title = "".join([t.get("plain_text", "") for t in p["title"]])
                            break
                    
                    # 2. 提取日期（优先寻找有开始和结束时间的 Date 属性）
                    for p_name, p_val in props.items():
                        if p_val.get("type") == "date" and p_val.get("date"):
                            d = p_val["date"]
                            start_val = parse_notion_date(d.get("start"))
                            if not start_val: continue
                            
                            ev = Event()
                            ev.add('summary', title)
                            ev.add('dtstart', start_val)
                            
                            # 处理甘特图结束日期（核心修复：全天日程结束日 +1 天）
                            end_iso = d.get("end")
                            if end_iso:
                                end_val = parse_notion_date(end_iso)
                                # 如果是全天日程（date类型），ICS协议要求结束日是次日 00:00 才能包含当天
                                if isinstance(end_val, datetime):
                                    ev.add('dtend', end_val)
                                else:
                                    ev.add('dtend', end_val + timedelta(days=1))
                            else:
                                # 单日日程处理
                                if isinstance(start_val, datetime):
                                    ev.add('dtend', start_val + timedelta(hours=1))
                                else:
                                    ev.add('dtend', start_val + timedelta(days=1))
                            
                            cal.add_component(ev)
                            total += 1
    
    with open("calendar.ics", "wb") as f:
        f.write(cal.to_ical())
    print(f"✅ 同步完成，共发现 {total} 个日程。甘特图跨度已修正。")

if __name__ == "__main__":
    sync()
