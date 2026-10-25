# TechPulse — Hacker News Technology Discussion Explorer

TechPulse is a small interactive prototype for a Social Media course project. It explores public Hacker News content with two APIs:

- **Algolia Hacker News Search API** — full-text search, content-type filters, date filters, and search metadata.
- **Official Hacker News Firebase API** — item details, comment trees, and optional public user profiles.

## Features

1. **Search:** search stories/comments, filter by type and date, sort by relevance or newest, and filter stories by minimum points/comments.
2. **Discussion explorer:** load a Hacker News item by ID, inspect a bounded sample of its comments, view frequent terms, and see a very rough lexical sentiment estimate. Optional public author profiles include available karma and account creation date.
3. **Trend explorer:** compare a monthly sample of results for up to three topics and export the sampled data as CSV.
4. **Methodology page:** summarizes research questions and limitations.

## Run locally

Requires Python 3.10 or newer.

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv .venv

# Windows PowerShell
.venv\\Scripts\\Activate.ps1

# macOS/Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the application
streamlit run app.py
```

The browser should open automatically. If not, visit `http://localhost:8501`.

No API key is required for the public endpoints used here. An internet connection is required.

## Suggested demo

1. Search for `serverless` over the last year.
2. Open one result in the Discussion explorer using its item ID.
3. Compare `serverless`, `Kubernetes`, and `anomaly detection` in Trend explorer.
4. Download the CSV and discuss how the search sample and API limits affect interpretation.

## Research questions

- How does discussion activity around selected technologies vary over time on Hacker News?
- Is discussion activity associated with story scores or comment counts?
- Which terms and rough sentiment signals appear in selected comment threads?

## Important limitations

- Hacker News users are not representative of the entire technology industry.
- Keyword matches can be ambiguous and do not prove topical relevance.
- Trend charts display a **bounded sample returned by the API**, not a complete census of all matching posts. The chart should not be described as the exact volume of all activity.
- The sentiment labels use a small hand-built English word list. They are illustrative, not a validated NLP model; sarcasm, technical vocabulary, and negation can cause errors.
- The official API stores comments as a tree. Thread retrieval requires multiple requests and is capped by the app.
- Deleted, dead, or unavailable items may be omitted.
- Results may change as new content is published and the search index updates.

## API references

- https://hn.algolia.com/api
- https://github.com/HackerNews/API

## Suggested paper outline (Springer LNCS, around 10 pages)

1. Introduction and research questions
2. Related work and platform context
3. APIs and data model
4. Methodology and implementation
5. Results from selected topics and time windows
6. Limitations and lessons learned
7. Conclusion

When reporting results, record the retrieval date, query, date range, content type, and sample cap.
