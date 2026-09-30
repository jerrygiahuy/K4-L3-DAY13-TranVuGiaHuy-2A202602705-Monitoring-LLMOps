import json
from pathlib import Path

import pandas as pd
import streamlit as st


LOG_PATH = Path("data/logs.jsonl")

st.set_page_config(
    page_title="K4-L3B Day 13 Monitoring & LLMOps",
    layout="wide",
)

st.title("K4-L3B Day 13 Monitoring & LLMOps")
st.caption("Runtime dashboard from data/logs.jsonl")


@st.cache_data(ttl=30)
def load_logs():
    rows = []

    if not LOG_PATH.exists():
        return pd.DataFrame()

    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    return pd.json_normalize(rows)


df = load_logs()

if df.empty:
    st.error("Không có dữ liệu trong data/logs.jsonl")
    st.stop()


# ============================================================
# Helpers
# ============================================================

def numeric(series):
    return pd.to_numeric(series, errors="coerce").dropna()


response_df = (
    df[df["event"] == "response_sent"].copy()
    if "event" in df.columns
    else pd.DataFrame()
)

request_df = (
    df[df["event"] == "request_received"].copy()
    if "event" in df.columns
    else pd.DataFrame()
)

failed_df = (
    df[df["event"] == "request_failed"].copy()
    if "event" in df.columns
    else pd.DataFrame()
)


# ============================================================
# ROW 1
# ============================================================

left, right = st.columns(2)

# 1. LATENCY
with left:
    st.subheader("1. Latency")

    if not response_df.empty and "latency_ms" in response_df.columns:
        latency = numeric(response_df["latency_ms"])

        if not latency.empty:
            c1, c2, c3 = st.columns(3)

            c1.metric(
                "P50",
                f"{latency.quantile(0.50):,.0f} ms",
            )

            c2.metric(
                "P95",
                f"{latency.quantile(0.95):,.0f} ms",
            )

            c3.metric(
                "P99",
                f"{latency.quantile(0.99):,.0f} ms",
            )

    if not response_df.empty and "ttft_ms" in response_df.columns:
        ttft = numeric(response_df["ttft_ms"])

        if not ttft.empty:
            st.metric(
                "TTFT P95",
                f"{ttft.quantile(0.95):,.0f} ms",
            )
    else:
        st.info("Không có dữ liệu TTFT.")


# 2. TRAFFIC
with right:
    st.subheader("2. Traffic")

    request_count = len(request_df)

    st.metric(
        "Request Received",
        request_count,
    )

    if "event" in df.columns:
        event_counts = df["event"].value_counts()
        st.bar_chart(event_counts)


# ============================================================
# ROW 2
# ============================================================

left, right = st.columns(2)

# 3. ERRORS / RETRIEVAL
with left:
    st.subheader("3. Errors & Retrieval Success")

    completed = len(response_df) + len(failed_df)

    if completed > 0:
        error_rate = len(failed_df) / completed * 100
    else:
        error_rate = 0

    c1, c2 = st.columns(2)

    c1.metric(
        "Error Rate",
        f"{error_rate:.2f}%",
    )

    retrieval_success = None

    if "tool_success" in df.columns:
        tool_data = df["tool_success"].dropna()

        if not tool_data.empty:
            converted = tool_data.map(
                lambda x: str(x).lower() == "true"
            )

            retrieval_success = converted.mean() * 100

    if retrieval_success is not None:
        c2.metric(
            "Retrieval Success",
            f"{retrieval_success:.2f}%",
        )
    else:
        c2.metric(
            "Retrieval Success",
            "N/A",
        )

    if (
        not failed_df.empty
        and "error_type" in failed_df.columns
    ):
        errors = failed_df["error_type"].dropna().value_counts()

        if not errors.empty:
            st.bar_chart(errors)


# 4. COST
with right:
    st.subheader("4. Cost")

    total_cost = 0

    if (
        not response_df.empty
        and "cost_usd" in response_df.columns
    ):
        cost = numeric(response_df["cost_usd"])

        if not cost.empty:
            total_cost = cost.sum()

            c1, c2 = st.columns(2)

            c1.metric(
                "Total Cost",
                f"${total_cost:.6f}",
            )

            c2.metric(
                "Avg / Response",
                f"${cost.mean():.6f}",
            )

            st.line_chart(
                cost.reset_index(drop=True)
            )
    else:
        st.info("Không có dữ liệu cost_usd.")


# ============================================================
# ROW 3
# ============================================================

left, right = st.columns(2)

# 5. TOKENS
with left:
    st.subheader("5. Tokens")

    tokens_in = 0
    tokens_out = 0

    if (
        not response_df.empty
        and "tokens_in" in response_df.columns
    ):
        tokens_in = numeric(
            response_df["tokens_in"]
        ).sum()

    if (
        not response_df.empty
        and "tokens_out" in response_df.columns
    ):
        tokens_out = numeric(
            response_df["tokens_out"]
        ).sum()

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Input",
        f"{tokens_in:,.0f}",
    )

    c2.metric(
        "Output",
        f"{tokens_out:,.0f}",
    )

    c3.metric(
        "Total",
        f"{tokens_in + tokens_out:,.0f}",
    )


# 6. QUALITY
with right:
    st.subheader("6. Quality")

    if (
        not response_df.empty
        and "quality_score" in response_df.columns
    ):
        quality = numeric(
            response_df["quality_score"]
        )

        if not quality.empty:
            avg_quality = quality.mean()

            st.metric(
                "Average Quality Score",
                f"{avg_quality:.3f}",
            )

            st.progress(
                min(
                    max(float(avg_quality), 0.0),
                    1.0,
                )
            )

            st.caption(
                "Target threshold: >= 0.75"
            )
        else:
            st.metric("Average Quality Score", "N/A")
    else:
        st.metric("Average Quality Score", "N/A")


st.divider()

st.caption(
    f"Loaded {len(df)} log events · "
    "Dashboard refresh cache: 30 seconds"
)
