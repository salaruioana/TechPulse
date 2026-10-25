import html
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from hn_api import search_hn, get_item, get_user, get_comment_thread
from analysis_utils import (
    clean_html, sentiment_label, keyword_counts, monthly_trend,
    timestamp_to_date, shorten
)

st.set_page_config(
    page_title="TechPulse | Security News Explorer",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded",
)
SENTIMENT_COLORS = {
    "Positive": "#2E8B57",
    "Neutral": "#9CA3AF",
    "Negative": "#D9534F",
}

st.markdown("""
<style>
    .block-container {padding-top: 1.7rem; padding-bottom: 3rem; max-width: 1400px;}
    .hero {padding: 1.4rem 1.6rem; border-radius: 16px; background: linear-gradient(120deg,#151d2b,#26364a); color: white; margin-bottom: 1rem;}
    .hero h1 {margin:0; font-size:2.2rem;}
    .hero p {margin:.45rem 0 0 0; color:#d6deea;}
    .small-muted {color: #778195; font-size: .86rem;}
    a {text-decoration: none;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🟠 TechPulse</h1>
  <p>Explore technology discussions, inspect comment threads, and compare topic activity on Hacker News.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Explore")
    st.caption("Data is retrieved live from public Hacker News APIs.")
    st.markdown("[Algolia HN Search API](https://hn.algolia.com/api)")
    st.markdown("[Official Hacker News API](https://github.com/HackerNews/API)")
    st.divider()
    st.subheader("Quick topics")
    quick_topic = st.selectbox(
        "Choose a starting topic",
        ["serverless", "Kubernetes", "LLM", "anomaly detection", "cybersecurity", "Python", "Rust"],
    )
    st.caption("Tip: use precise terms, then compare the same query over different time ranges.")

search_tab, discussion_tab, trends_tab, about_tab = st.tabs(
    ["🔎 Search", "💬 Discussion explorer", "📈 Trend explorer", "ℹ️ About & methodology"]
)

with search_tab:
    st.subheader("Search Hacker News")
    st.write("Search stories or comments, then narrow the results by type, date, and engagement.")
    st.info(
        "Workflow: Search for a topic → identify an interesting story "
        "or comment → open its discussion in Discussion Explorer "
        "to inspect comments, sentiment estimates, and frequent terms."
    )
    with st.form("search_form"):
        col1, col2, col3 = st.columns([2.2, 1.2, 1])
        with col1:
            query = st.text_input("Search phrase", value=quick_topic, placeholder="e.g. serverless security")
        with col2:
            content_type = st.selectbox(
                "Content type",
                ["Stories", "Comments", "Ask HN", "Show HN", "Stories + comments"],
            )
        with col3:
            sort_order = st.selectbox("Sort by", ["Relevance", "Newest"])
        c1, c2, c3 = st.columns(3)
        with c1:
            start_date = st.date_input("From", value=date.today() - timedelta(days=365))
        with c2:
            end_date = st.date_input("To", value=date.today())
        with c3:
            result_limit = st.select_slider("Results to fetch", options=[10, 20, 30, 50], value=20)
        c4, c5 = st.columns(2)
        with c4:
            min_points = st.number_input("Minimum points (stories)", min_value=0, max_value=100000, value=0, step=5)
        with c5:
            min_comments = st.number_input("Minimum comments (stories)", min_value=0, max_value=100000, value=0, step=5)
        submitted = st.form_submit_button("Search", type="primary", use_container_width=True)

    if submitted:
        if start_date > end_date:
            st.error("The start date must be on or before the end date.")
        else:
            tags_map = {
                "Stories": "story",
                "Comments": "comment",
                "Ask HN": "ask_hn",
                "Show HN": "show_hn",
                "Stories + comments": "(story,comment)",
            }
            with st.spinner("Querying Hacker News…"):
                try:
                    hits, metadata = search_hn(
                        query=query.strip(),
                        tags=tags_map[content_type],
                        start_date=start_date,
                        end_date=end_date,
                        limit=int(result_limit),
                        sort_by_date=(sort_order == "Newest"),
                        min_points=int(min_points) if content_type in ["Stories", "Ask HN", "Show HN"] else 0,
                        min_comments=int(min_comments) if content_type in ["Stories", "Ask HN", "Show HN"] else 0,
                    )
                    st.session_state["search_hits"] = hits
                    st.session_state["search_metadata"] = metadata
                    st.session_state["search_query"] = query.strip()
                except Exception as exc:
                    st.error(f"Could not retrieve search results: {exc}")

    hits = st.session_state.get("search_hits", [])
    if hits:
        metadata = st.session_state.get("search_metadata", {})
        st.caption(
            f"Showing {len(hits)} returned items · API reports {metadata.get('nbHits', 'unknown')} matching hits "
            f"· Search index: {metadata.get('endpoint', 'Algolia')}"
        )
        for hit in hits:
            title = clean_html(hit.get("title") or hit.get("story_title") or "(Comment without a title)")
            body = clean_html(hit.get("comment_text") or hit.get("story_text") or "")
            author = hit.get("author") or "unknown"
            created = timestamp_to_date(hit.get("created_at_i"))
            points = hit.get("points")
            comments = hit.get("num_comments")
            object_id = hit.get("objectID", "")
            is_comment = "comment" in (hit.get("_tags") or [])
            discussion_id = (
                hit.get("story_id", object_id)
                if is_comment else object_id
            )
            link = f"https://news.ycombinator.com/item?id={object_id}"
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**[{title}]({link})**")
                    if body:
                        st.write(shorten(body, 360))
                    st.caption(f"by {author} · {created} · {'Comment' if is_comment else 'Story'}")
                with c2:
                    st.metric("Points", points if points is not None else "—")
                    st.metric("Comments", comments if comments is not None else "—")
                    st.caption(f"Item ID: {object_id}")
                    
                    if is_comment:
                        st.caption(f"Discussion ID: {discussion_id}")
                        
                    if st.button(
                        "Explore this discussion",
                        key=f"explore_{object_id}",
                        type="secondary",
                    ):
                        st.session_state["selected_discussion_id"] = str(
                            discussion_id
                        ) 
                        st.session_state["open_discussion"] = True
                        st.rerun()
                if is_comment and hit.get("story_id"):
                    st.caption(f"Parent discussion: [open story](https://news.ycombinator.com/item?id={hit['story_id']})")
        if metadata.get("nbHits", 0) > len(hits):
            st.info("The API returns paginated search results. This prototype fetches a bounded sample to keep requests quick.")
    elif "search_hits" in st.session_state:
        st.info("No results found for these filters. Try a broader query or date range.")
    else:
        st.info("Run a search to see live Hacker News results.")

with discussion_tab:
    st.subheader("Inspect a discussion")
    if st.session_state.get("open_discussion"):
        st.success(
            "Discussion selected from Search. "
            "Review the item ID below and click Load discussion."
        )
        st.session_state["open_discussion"] = False
    st.write("Enter a Hacker News item ID from a search result, or paste an ID from a Hacker News URL.")
    default_id = st.session_state.get("selected_discussion_id", "")

    if not default_id:
        existing_hits = st.session_state.get("search_hits", [])
        if existing_hits:
            first_hit = existing_hits[0]
            default_id = str(
                first_hit.get("story_id", first_hit.get("objectID", ""))
                if "comment" in first_hit.get("_tags", [])
                else first_hit.get("objectID", "")
            )
    with st.form("thread_form"):
        item_id_text = st.text_input("Hacker News item ID", value=default_id, placeholder="e.g. 8863")
        max_comments = st.slider("Maximum comments to inspect", min_value=5, max_value=60, value=25, step=5)
        include_profiles = st.checkbox("Load public profiles for comment authors", value=False)
        thread_submitted = st.form_submit_button("Load discussion", type="primary")
    if thread_submitted:
        if not item_id_text.strip().isdigit():
            st.error("Enter a numeric Hacker News item ID.")
        else:
            with st.spinner("Loading item and comment thread…"):
                try:
                    root_item = get_item(int(item_id_text.strip()))
                    comments = get_comment_thread(int(item_id_text.strip()), limit=max_comments)
                    profiles = {}
                    if include_profiles:
                        for author in dict.fromkeys(c.get("by") for c in comments if c.get("by")):
                            try:
                                profiles[author] = get_user(author)
                            except Exception:
                                profiles[author] = {}
                    st.session_state["thread_item"] = root_item
                    st.session_state["thread_comments"] = comments
                    st.session_state["thread_profiles"] = profiles
                except Exception as exc:
                    st.error(f"Could not load this discussion: {exc}")

    root_item = st.session_state.get("thread_item")
    comments = st.session_state.get("thread_comments", [])
    if root_item:
        root_title = clean_html(root_item.get("title") or "Hacker News discussion")
        root_text = clean_html(root_item.get("text") or "")
        st.markdown(f"### [{root_title}](https://news.ycombinator.com/item?id={root_item.get('id')})")
        st.caption(
            f"Author: {root_item.get('by', 'unknown')} · "
            f"Points: {root_item.get('score', '—')} · "
            f"Reported comments: {root_item.get('descendants', '—')}"
        )
        if root_text:
            st.write(root_text)
        st.markdown("#### Comment overview")
        if comments:
            comment_rows = []
            for c in comments:
                txt = clean_html(c.get("text") or "")
                comment_rows.append({
                    "author": c.get("by", "unknown"),
                    "date": timestamp_to_date(c.get("time")),
                    "text": txt,
                    "sentiment": sentiment_label(txt),
                    "score": c.get("score", 0),
                    "id": c.get("id"),
                })
            df_comments = pd.DataFrame(comment_rows)
            sentiment_counts = df_comments["sentiment"].value_counts().reindex(
                ["Positive", "Neutral", "Negative"], fill_value=0
            ).reset_index()
            sentiment_counts.columns = ["Sentiment (lexical estimate)", "Comments"]
            col1, col2 = st.columns([1, 2])
            with col1:
                fig = px.pie(
                    sentiment_counts,
                    names="Sentiment (lexical estimate)",
                    values="Comments",
                    title="Comment tone (rough estimate)",
                    hole=0.45,
                    color="Sentiment (lexical estimate)",
                    color_discrete_map=SENTIMENT_COLORS,
                )
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                terms = keyword_counts(" ".join(df_comments["text"].tolist()), limit=15)
                if terms:
                    term_df = pd.DataFrame(terms, columns=["Term", "Count"])
                    fig = px.bar(term_df.sort_values("Count"), x="Count", y="Term", orientation="h",
                                 title="Frequent terms in loaded comments")
                    st.plotly_chart(fig, use_container_width=True)
            st.markdown("#### Loaded comments")
            for _, row in df_comments.iterrows():
                with st.container(border=True):
                    st.caption(f"{row['author']} · {row['date']} · lexical label: {row['sentiment']}")
                    st.write(shorten(row["text"], 1200) or "(No text available)")
                    if include_profiles:
                        profile = st.session_state.get("thread_profiles", {}).get(row["author"], {})
                        if profile:
                            st.caption(f"Author karma: {profile.get('karma', 'unknown')} · account created: {timestamp_to_date(profile.get('created'))}")
                            about = clean_html(profile.get("about") or "")
                            if about:
                                st.caption(f"Profile: {shorten(about, 240)}")
        else:
            st.info("No accessible comments were returned for this item.")
        st.caption("The official API represents comments as a tree. This prototype samples the thread in breadth-first order and caps the number of fetched comments.")

with trends_tab:
    st.subheader("Compare topic activity over time")
    st.write("This view samples monthly search results for each topic and compares the activity visible through the Algolia index.")
    with st.form("trend_form"):
        topics_text = st.text_input(
            "Topics (comma-separated; up to 3)",
            value="serverless, Kubernetes, anomaly detection",
        )
        trend_type = st.selectbox("Count", ["Stories", "Comments", "Stories + comments"])
        months = st.slider("Months to compare", min_value=3, max_value=24, value=12)
        per_month = st.select_slider("Sample size per topic/month", options=[10, 20, 30, 50], value=20)
        trend_submitted = st.form_submit_button("Build trend chart", type="primary")
    if trend_submitted:
        topics = [x.strip() for x in topics_text.split(",") if x.strip()][:3]
        if not topics:
            st.error("Enter at least one topic.")
        else:
            type_tags = {"Stories": "story", "Comments": "comment", "Stories + comments": "(story,comment)"}
            start_month = (date.today().replace(day=1) - timedelta(days=months * 31)).replace(day=1)
            records = []
            progress = st.progress(0)
            total = len(topics) * months
            done = 0
            try:
                for topic in topics:
                    for offset in range(months - 1, -1, -1):
                        # Month boundaries are calculated without external dependencies.
                        today_first = date.today().replace(day=1)
                        month_index = today_first.year * 12 + today_first.month - 1 - offset
                        year = month_index // 12
                        month = month_index % 12 + 1
                        month_start = date(year, month, 1)
                        if month == 12:
                            month_end = date(year + 1, 1, 1) - timedelta(days=1)
                        else:
                            month_end = date(year, month + 1, 1) - timedelta(days=1)
                        hits, meta = search_hn(
                            query=topic, tags=type_tags[trend_type],
                            start_date=month_start, end_date=month_end,
                            limit=int(per_month), sort_by_date=True,
                        )
                        records.append({
                            "topic": topic,
                            "month": month_start.strftime("%Y-%m"),
                            "sample_count": len(hits),
                            "api_total": meta.get("nbHits", len(hits)),
                        })
                        done += 1
                        progress.progress(done / total)
                trend_df = pd.DataFrame(records)
                st.session_state["trend_df"] = trend_df
                st.session_state["trend_type"] = trend_type
                st.session_state["trend_topics"] = topics
            except Exception as exc:
                st.error(f"Trend collection failed: {exc}")
            finally:
                progress.empty()

    trend_df = st.session_state.get("trend_df")
    if trend_df is not None and not trend_df.empty:
        metric = "sample_count"
        chart_df = trend_df.rename(columns={"sample_count": "Returned sample", "api_total": "API-reported matches"})
        fig = px.line(
            chart_df, x="month", y="Returned sample", color="topic", markers=True,
            title=f"Monthly returned sample — {st.session_state.get('trend_type', 'Stories')}",
            hover_data={"API-reported matches": True, "month": True, "topic": True},
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Important: the line shows the number of results returned within your chosen sample cap, not the total number of posts on Hacker News.")
        with st.expander("View monthly data table"):
            st.dataframe(trend_df, use_container_width=True, hide_index=True)
        csv = trend_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download trend data as CSV", csv, "techpulse_trends.csv", "text/csv")
    else:
        st.info("Choose topics and build a trend chart to start the analysis.")

with about_tab:
    st.subheader("About this prototype")
    st.markdown("""
**TechPulse** is a small research prototype for exploring public technology discussions on Hacker News.

**Data sources**
- **Algolia HN Search API** is used for full-text search and date/type filtering.
- **Official Hacker News Firebase API** is used to retrieve an item, its comment tree, and optional public author profiles.

**Research questions**
1. How does discussion activity around selected technologies vary over time on Hacker News?
2. Is discussion activity associated with story scores or comment counts?
3. Which terms and rough sentiment signals appear in selected comment threads?

**Methodological limitations**
- Hacker News users are not representative of the whole technology industry.
- Search terms can be ambiguous; a keyword match is not proof that a post is truly about the topic.
- The trend chart uses a bounded monthly sample. The number of returned results is not the same as the total number of posts.
- The sentiment labels use a small English word lexicon, not a trained or context-aware model. Sarcasm, technical language, and negation can lead to errors.
- The official API stores comments as a tree, so retrieving a thread requires multiple requests. Deleted or inaccessible items may be missing.
- Results can change as new posts appear or the search index updates.

**Reproducibility tip:** record the search phrase, date range, content type, sample cap, and retrieval date when reporting results in the course paper.
""")
    st.markdown("**Documentation:** [Algolia HN Search API](https://hn.algolia.com/api) · [Official HN API](https://github.com/HackerNews/API)")
