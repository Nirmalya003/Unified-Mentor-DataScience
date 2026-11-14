
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
# PAGE CONFIGURATION
st.set_page_config(
    page_title="France Top 50 Playlist Analysis",
    page_icon="🎵",
    layout="wide"
)

# LOAD DATA
@st.cache_data
def load_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    data = pd.read_csv(os.path.join(BASE_DIR, "france_top50_cleaned.csv"))

    data["date"] = pd.to_datetime(data["date"])

    if "duration_minutes" not in data.columns:
        data["duration_minutes"] = data["duration_ms"] / 60000

    if "rank_tier" not in data.columns:
        data["rank_tier"] = np.where(
            data["position"] <= 10,
            "Top 10",
            np.where(data["position"] <= 25, "Top 25", "26-50")
        )

    return data

df = load_data()

# TITLE
st.title("🎵 France Top 50 Playlist Analysis")
st.subheader(
    "Audience Sensitivity, Content Compliance & Format Preference"
)
st.caption("Atlantic Recording Corporation | Unified Mentor Project")

# SIDEBAR FILTERS
st.sidebar.header("Dashboard Filters")

min_date = df["date"].min().date()
max_date = df["date"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

rank_filter = st.sidebar.selectbox(
    "Rank Tier",
    ["All (Top 50)", "Top 10", "Top 25", "26-50"]
)

explicit_filter = st.sidebar.selectbox(
    "Explicit Content",
    ["All", "Explicit", "Clean"]
)

album_filter = st.sidebar.selectbox(
    "Album Type",
    ["All"] + sorted(df["album_type"].dropna().unique().tolist())
)

# APPLY FILTERS
filtered_df = df.copy()

if isinstance(date_range, (tuple, list)):
    if len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])

        filtered_df = filtered_df[
            (filtered_df["date"] >= start_date) &
            (filtered_df["date"] < end_date + pd.Timedelta(days=1))
        ]

if rank_filter == "Top 10":
    filtered_df = filtered_df[filtered_df["position"] <= 10]
elif rank_filter == "Top 25":
    filtered_df = filtered_df[filtered_df["position"] <= 25]
elif rank_filter == "26-50":
    filtered_df = filtered_df[filtered_df["position"] > 25]

if explicit_filter == "Explicit":
    filtered_df = filtered_df[filtered_df["is_explicit"] == True]
elif explicit_filter == "Clean":
    filtered_df = filtered_df[filtered_df["is_explicit"] == False]

if album_filter != "All":
    filtered_df = filtered_df[filtered_df["album_type"] == album_filter]

total = len(filtered_df)

# OVERVIEW
st.header("📊 Dashboard Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Total Records", f"{total:,}")

with c2:
    st.metric("Unique Dates", filtered_df["date"].nunique())

with c3:
    st.metric(
        "Average Popularity",
        f"{filtered_df['popularity'].mean():.2f}" if total else "N/A"
    )

with c4:
    st.metric(
        "Average Duration",
        f"{filtered_df['duration_minutes'].mean():.2f} min" if total else "N/A"
    )

# KPI CALCULATIONS
if total:
    explicit_count = int(filtered_df["is_explicit"].sum())
    clean_count = total - explicit_count

    explicit_share = explicit_count / total * 100
    clean_share = clean_count / total * 100

    clean_ratio = (
        clean_count / explicit_count if explicit_count else np.nan
    )

    single_count = (
        filtered_df["album_type"].str.lower() == "single"
    ).sum()

    album_count = (
        filtered_df["album_type"].str.lower() == "album"
    ).sum()

    single_album_ratio = (
        single_count / album_count if album_count else np.nan
    )

    avg_duration = filtered_df["duration_minutes"].mean()

    album_df = filtered_df[
        filtered_df["album_type"].str.lower() == "album"
    ]

    album_impact = (
        album_df[["total_tracks", "popularity"]].corr().iloc[0, 1]
        if len(album_df) > 1 else np.nan
    )

    acceptance_score = clean_share

else:
    explicit_count = clean_count = 0
    explicit_share = clean_share = np.nan
    clean_ratio = single_album_ratio = np.nan
    avg_duration = album_impact = acceptance_score = np.nan

# KPI CARDS
st.header("📌 Key Performance Indicators")

k1, k2, k3 = st.columns(3)

k1.metric(
    "Explicit Content Share",
    f"{explicit_share:.2f}%" if not np.isnan(explicit_share) else "N/A"
)

k2.metric(
    "Clean Content Dominance Ratio",
    f"{clean_ratio:.3f}" if not np.isnan(clean_ratio) else "N/A"
)

k3.metric(
    "Single vs Album Ratio",
    f"{single_album_ratio:.3f}" if not np.isnan(single_album_ratio) else "N/A"
)

k4, k5, k6 = st.columns(3)

k4.metric(
    "Average Song Duration",
    f"{avg_duration:.2f} min" if not np.isnan(avg_duration) else "N/A"
)

k5.metric(
    "Album Size Impact Index",
    f"{album_impact:.4f}" if not np.isnan(album_impact) else "N/A"
)

k6.metric(
    "Content Acceptance Score",
    f"{acceptance_score:.2f}%" if not np.isnan(acceptance_score) else "N/A"
)

st.divider()

# EXPLICIT CONTENT ANALYSIS
st.header("🔞 Explicit Content Sensitivity")

if total:
    content_data = pd.DataFrame({
        "Content": ["Explicit", "Clean"],
        "Count": [explicit_count, clean_count]
    })

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.bar(content_data["Content"], content_data["Count"])
        ax.set_title("Explicit vs Clean Tracks")
        ax.set_ylabel("Number of Records")
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        fig, ax = plt.subplots()
        ax.pie(
            content_data["Count"],
            labels=content_data["Content"],
            autopct="%1.1f%%"
        )
        ax.set_title("Content Share")
        st.pyplot(fig)
        plt.close(fig)

    rank_content = pd.crosstab(
        filtered_df["rank_tier"],
        filtered_df["is_explicit"],
        normalize="index"
    ) * 100

    rank_content = rank_content.rename(
        columns={False: "Clean", True: "Explicit"}
    )

    st.subheader("Content Share by Rank Tier")
    st.dataframe(rank_content, use_container_width=True)

# RELEASE FORMAT ANALYSIS
st.header("💿 Release Format Preference")

if total:
    format_counts = filtered_df["album_type"].value_counts()

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        format_counts.plot(kind="bar", ax=ax)
        ax.set_title("Release Format Distribution")
        ax.set_ylabel("Number of Records")
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        format_popularity = filtered_df.groupby(
            "album_type"
        )["popularity"].mean()

        fig, ax = plt.subplots()
        format_popularity.plot(kind="bar", ax=ax)
        ax.set_title("Average Popularity by Release Format")
        ax.set_ylabel("Average Popularity")
        st.pyplot(fig)
        plt.close(fig)

    st.dataframe(
        format_counts.rename("Count").to_frame(),
        use_container_width=True
    )

# SONG DURATION ANALYSIS
st.header("⏱️ Song Duration Preference")

if total:
    duration_df = filtered_df.copy()

    duration_df["duration_category"] = pd.cut(
        duration_df["duration_minutes"],
        bins=[-np.inf, 3, 4.5, np.inf],
        labels=["Short (<3 min)", "Medium (3–4.5 min)", "Long (>4.5 min)"]
    )

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.hist(duration_df["duration_minutes"], bins=20)
        ax.set_title("Song Duration Distribution")
        ax.set_xlabel("Duration (minutes)")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        duration_counts = duration_df["duration_category"].value_counts()
        fig, ax = plt.subplots()
        duration_counts.plot(kind="bar", ax=ax)
        ax.set_title("Duration Category Distribution")
        st.pyplot(fig)
        plt.close(fig)

    duration_popularity = duration_df.groupby(
        "duration_category", observed=True
    )["popularity"].mean()

    st.subheader("Average Popularity by Duration Category")
    st.dataframe(
        duration_popularity.rename("Average Popularity").to_frame(),
        use_container_width=True
    )

    fig, ax = plt.subplots()
    ax.scatter(
        duration_df["duration_minutes"],
        duration_df["popularity"],
        alpha=0.3
    )
    ax.set_title("Duration vs Popularity")
    ax.set_xlabel("Duration (minutes)")
    ax.set_ylabel("Popularity")
    st.pyplot(fig)
    plt.close(fig)

# ALBUM STRUCTURE ANALYSIS
st.header("💿 Album Structure Impact")

album_df = filtered_df[
    filtered_df["album_type"].str.lower() == "album"
].copy()

if len(album_df):
    album_df["album_size_category"] = pd.cut(
        album_df["total_tracks"],
        bins=[0, 12, 18, np.inf],
        labels=["Small (7–12)", "Medium (13–18)", "Large (19+)"]
    )

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.hist(album_df["total_tracks"], bins=15)
        ax.set_title("Album Size Distribution")
        ax.set_xlabel("Total Tracks")
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        fig, ax = plt.subplots()
        album_df["album_size_category"].value_counts().plot(
            kind="bar", ax=ax
        )
        ax.set_title("Album Size Categories")
        st.pyplot(fig)
        plt.close(fig)

    fig, ax = plt.subplots()
    ax.scatter(
        album_df["total_tracks"],
        album_df["popularity"],
        alpha=0.3
    )
    ax.set_title("Album Size vs Track Popularity")
    ax.set_xlabel("Total Tracks")
    ax.set_ylabel("Popularity")
    st.pyplot(fig)
    plt.close(fig)

    st.info(
        f"Album Size Impact Index: "
        f"{album_impact:.4f}" if not np.isnan(album_impact) else
        "Album size correlation unavailable."
    )

# RANK-TIER ANALYSIS
st.header("🏆 Rank-Tier & Content Concentration")

if total:
    rank_order = ["Top 10", "Top 25", "26-50"]

    rank_content = pd.crosstab(
        filtered_df["rank_tier"],
        filtered_df["is_explicit"],
        normalize="index"
    ) * 100

    rank_content = rank_content.rename(
        columns={False: "Clean", True: "Explicit"}
    ).reindex(rank_order).fillna(0)

    fig, ax = plt.subplots()
    rank_content.plot(kind="bar", stacked=True, ax=ax)
    ax.set_title("Explicit vs Clean by Rank Tier")
    ax.set_ylabel("Percentage (%)")
    ax.set_ylim(0, 100)
    st.pyplot(fig)
    plt.close(fig)

    rank_format = pd.crosstab(
        filtered_df["rank_tier"],
        filtered_df["album_type"],
        normalize="index"
    ) * 100

    rank_format = rank_format.reindex(rank_order).fillna(0)

    fig, ax = plt.subplots()
    rank_format.plot(kind="bar", stacked=True, ax=ax)
    ax.set_title("Release Format by Rank Tier")
    ax.set_ylabel("Percentage (%)")
    ax.set_ylim(0, 100)
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Rank-Tier Summary")
    st.dataframe(rank_content, use_container_width=True)
    st.dataframe(rank_format, use_container_width=True)

# FINAL COMPLIANCE SUMMARY
st.header("📋 Final Compliance Summary")

if total:
    st.write(f"**Explicit Content Share:** {explicit_share:.2f}%")
    st.write(f"**Clean Content Share:** {clean_share:.2f}%")
    st.write(f"**Average Popularity:** {filtered_df['popularity'].mean():.2f}")
    st.write(f"**Average Duration:** {avg_duration:.2f} minutes")

    if explicit_share >= 50:
        st.warning(
            "Explicit content represents at least half of the filtered records. "
            "Content compliance should be considered in release and pitching decisions."
        )
    else:
        st.info(
            "Clean content represents more than half of the filtered records."
        )

    st.subheader("💡 Business Insights")

    st.write(
        "• Explicit and clean tracks both have substantial representation."
    )
    st.write(
        "• Release-format representation varies across rank tiers."
    )
    st.write(
        "• Album size shows a weak relationship with track popularity."
    )
    st.write(
        "• Song duration has a very weak linear relationship with popularity."
    )
    st.caption(
        "Correlation does not establish causation. Content Acceptance Score "
        "is defined as the percentage of clean tracks."
    )

# DATA PREVIEW
st.divider()
st.header("📄 Filtered Dataset Preview")

st.write(f"Records after filters: {total:,}")

st.dataframe(
    filtered_df.head(100),
    use_container_width=True
)

st.divider()

st.caption(
    "Unified Mentor Project | France Top 50 Playlist Analysis"
)
