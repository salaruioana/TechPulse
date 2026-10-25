from collections import Counter
from datetime import datetime, timezone
import html
import re

# A deliberately small lexicon: useful for a demo, not validated sentiment analysis.
POSITIVE = {
    "good", "great", "excellent", "love", "useful", "helpful", "amazing",
    "better", "best", "benefit", "improve", "improved", "success", "easy",
    "fast", "nice", "promising", "exciting", "awesome", "secure", "efficient",
    "cool", "fun",
    # Technology and software
    "efficient", "efficiently", "reliable", "stable", "robust", "scalable",
    "secure", "optimized", "optimised", "faster", "simpler", "clean",
    "intuitive", "convenient", "powerful", "flexible", "maintainable",
    "compatible", "lightweight", "responsive", "accurate", "effective",
    "innovative", "upgrade", "upgraded", "solution", "solved", "works",
    "working", "supported", "support", "improvement", "improvements",
    "performance", "successfully", "smooth", "smoothly", "productive"
}
NEGATIVE = {
    "bad", "terrible", "hate", "worse", "worst", "problem", "problems",
    "bug", "bugs", "broken", "fail", "failure", "slow", "hard", "difficult",
    "risk", "risky", "vulnerability", "insecure", "expensive", "annoying",
    "wrong", "poor", "dangerous", "issue", "issues",
    # Technology and software
    "bug", "bugs", "risky", "risk", "vulnerability", "vulnerabilities",
    "insecure", "expensive", "costly", "overpriced", "crash", "crashes",
    "crashed", "crashing", "error", "errors", "exception", "timeout",
    "timeouts", "downtime", "outage", "outages", "incompatible",
    "incompatibility", "deprecated", "obsolete", "lag", "laggy",
    "inefficient", "unusable", "unresponsive", "unstable", "regression",
    "regressions", "exploit", "exploitable", "breach", "breached",
    "attack", "attacks", "malware", "leak", "leaks", "leaked",
    "overhead", "bottleneck", "bottlenecks", "corrupt", "corrupted",
    "fails", "failed", "failing", "failure", "limitations", "limitation"
}
STOPWORDS = set("""
a an the and or but if then than so to of in on for from with without at by as is
are was were be been being it its this that these those i we you they he she them
our your their my me us not no yes do does did can could should would will just
about into over under more most less very also there here what when where why how
which who have has had having up down out all any some much many such only own
same too via per new using use used one two get got make made like really still
than http https www com org net hn hacker news
""".split())

def clean_html(value):
    if not value:
        return ""
    value = re.sub(r"<br\s*/?>", "\n", str(value), flags=re.I)
    value = re.sub(r"</p\s*>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return html.unescape(re.sub(r"\s+", " ", value)).strip()

def sentiment_label(text):
    words = re.findall(r"[a-zA-Z']+", (text or "").lower())
    pos = sum(word in POSITIVE for word in words)
    neg = sum(word in NEGATIVE for word in words)
    if pos > neg:
        return "Positive"
    if neg > pos:
        return "Negative"
    return "Neutral"

def keyword_counts(text, limit=20):
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", (text or "").lower())
    counts = Counter(
        word.strip(".-") for word in words
        if len(word) > 2 and word not in STOPWORDS and not word.startswith("http")
    )
    return counts.most_common(limit)

def timestamp_to_date(value):
    if value is None:
        return "date unknown"
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OSError):
        return "date unknown"

def shorten(text, limit=300):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"

def monthly_trend(*args, **kwargs):
    """Reserved helper for future aggregation extensions."""
    raise NotImplementedError("Trend aggregation currently lives in the Streamlit app.")
