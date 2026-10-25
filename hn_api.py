from datetime import datetime, time, timedelta, timezone
import requests
import streamlit as st

ALGOLIA_BASE = "https://hn.algolia.com/api/v1"
FIREBASE_BASE = "https://hacker-news.firebaseio.com/v0"
TIMEOUT = 15
HEADERS = {"User-Agent": "TechPulse-course-project/1.0"}

def _request_json(url, params=None):
    response = requests.get(url, params=params, timeout=TIMEOUT, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def _unix_start(d):
    return int(datetime.combine(d, time.min, tzinfo=timezone.utc).timestamp())

def _unix_end(d):
    return int(datetime.combine(d + timedelta(days=1), time.min, tzinfo=timezone.utc).timestamp()) - 1

@st.cache_data(ttl=300, show_spinner=False)
def search_hn(query="", tags="story", start_date=None, end_date=None, limit=20,
              sort_by_date=False, min_points=0, min_comments=0):
    """Search Algolia's public HN index. Returns (hits, response metadata)."""
    endpoint_name = "search_by_date" if sort_by_date or min_points or min_comments else "search"
    params = {
        "query": query or "",
        "tags": tags,
        "hitsPerPage": min(max(int(limit), 1), 50),
        "page": 0,
    }
    filters = []
    if start_date:
        filters.append(f"created_at_i>={_unix_start(start_date)}")
    if end_date:
        filters.append(f"created_at_i<={_unix_end(end_date)}")
    if min_points:
        filters.append(f"points>={int(min_points)}")
    if min_comments:
        filters.append(f"num_comments>={int(min_comments)}")
    if filters:
        params["numericFilters"] = ",".join(filters)
    data = _request_json(f"{ALGOLIA_BASE}/{endpoint_name}", params=params)
    metadata = {
        "nbHits": data.get("nbHits", 0),
        "nbPages": data.get("nbPages", 0),
        "page": data.get("page", 0),
        "endpoint": endpoint_name,
        "processingTimeMS": data.get("processingTimeMS"),
    }
    return data.get("hits", []), metadata

@st.cache_data(ttl=600, show_spinner=False)
def get_item(item_id):
    item = _request_json(f"{FIREBASE_BASE}/item/{int(item_id)}.json")
    if not item:
        raise ValueError("The item was not found or is no longer available.")
    return item

@st.cache_data(ttl=3600, show_spinner=False)
def get_user(username):
    profile = _request_json(f"{FIREBASE_BASE}/user/{username}.json")
    return profile or {}

def get_comment_thread(item_id, limit=25):
    """Fetch comments breadth-first, with a hard cap to avoid excessive requests."""
    root = get_item(item_id)
    queue = [(kid, 1) for kid in root.get("kids", [])]
    comments = []
    seen = set()
    max_depth = 4
    while queue and len(comments) < limit:
        comment_id, depth = queue.pop(0)
        if comment_id in seen:
            continue
        seen.add(comment_id)
        try:
            item = get_item(comment_id)
        except (requests.RequestException, ValueError):
            continue
        if not item or item.get("deleted") or item.get("dead"):
            continue
        if item.get("type") == "comment":
            comments.append(item)
            if depth < max_depth:
                queue.extend((kid, depth + 1) for kid in item.get("kids", []))
    return comments
