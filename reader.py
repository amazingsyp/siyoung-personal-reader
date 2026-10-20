"""siyoung-personal-reader: personal, read-only Reddit digest (non-commercial).

- OAuth script app, scope "read" only. Never posts, comments, votes, or messages.
- Fixed subreddit list, hard caps on requests, honors X-Ratelimit-* headers.
- Stores minimal fields locally, purges after 7 days, drops deleted/removed items.
"""
import json, os, sqlite3, time
import praw

SUBREDDITS = ["iPhoneDuo", "iphone", "apple", "TeslaMotors"]
KEYWORDS = ["shipped", "order status", "preparing to ship"]
MAX_REQUESTS_PER_RUN = 150      # 2 runs/day -> <= 300 requests/day
MIN_SECONDS_BETWEEN_REQ = 6     # <= 10 requests/minute
RETENTION_DAYS = 7
USER_AGENT = "macos:siyoung-personal-reader:v0.1.0 (by /u/siyoung_reader2741)"
DB = os.path.expanduser("~/.siyoung-reader/digest.sqlite")

_count = 0
_last = 0.0

def throttle(reddit):
    global _count, _last
    if _count >= MAX_REQUESTS_PER_RUN:
        raise SystemExit("request cap reached")
    wait = MIN_SECONDS_BETWEEN_REQ - (time.time() - _last)
    if wait > 0:
        time.sleep(wait)
    limits = reddit.auth.limits or {}
    if limits.get("remaining") is not None and limits["remaining"] < 10:
        raise SystemExit("rate-limit headroom low; stopping")
    _count += 1
    _last = time.time()

def db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY, sub TEXT, title TEXT,"
                " body TEXT, score INT, created REAL, fetched REAL)")
    return con

def purge(con, reddit):
    con.execute("DELETE FROM items WHERE fetched < ?", (time.time() - RETENTION_DAYS * 86400,))
    ids = [r[0] for r in con.execute("SELECT id FROM items")]
    for i in range(0, len(ids), 100):          # /api/info, 100 ids per request
        throttle(reddit)
        for thing in reddit.info(fullnames=ids[i:i + 100]):
            body = getattr(thing, "selftext", None) or getattr(thing, "body", "")
            if body in ("[deleted]", "[removed]") or getattr(thing, "removed_by_category", None):
                con.execute("DELETE FROM items WHERE id=?", (thing.fullname,))
    con.commit()

def main():
    reddit = praw.Reddit(client_id=os.environ["REDDIT_CLIENT_ID"],
                         client_secret=os.environ["REDDIT_CLIENT_SECRET"],
                         username=os.environ["REDDIT_USERNAME"],
                         password=os.environ["REDDIT_PASSWORD"],
                         user_agent=USER_AGENT, ratelimit_seconds=60)
    reddit.read_only = True
    con = db()
    purge(con, reddit)
    for sub in SUBREDDITS:
        throttle(reddit)
        posts = list(reddit.subreddit(sub).new(limit=25))
        for kw in KEYWORDS:
            throttle(reddit)
            posts += list(reddit.subreddit(sub).search(kw, sort="new", time_filter="day", limit=10))
        for p in posts:
            con.execute("INSERT OR REPLACE INTO items VALUES (?,?,?,?,?,?,?)",
                        (p.fullname, sub, p.title, p.selftext[:2000], p.score, p.created_utc, time.time()))
    con.commit()
    rows = con.execute("SELECT sub, title, score FROM items ORDER BY created DESC LIMIT 80").fetchall()
    print(json.dumps(rows, ensure_ascii=False, indent=1))   # private digest, local only

if __name__ == "__main__":
    main()
