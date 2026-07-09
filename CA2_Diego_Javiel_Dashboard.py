import streamlit as st
import pandas as pd
import plotly.express as px

# st.set_page_config must be the first Streamlit call
st.set_page_config(
    page_title="L7 Data Visualization and Communication CA2", layout="wide")

# Caching for preventing the CSV from being reloaded on every user interaction


@st.cache_data
def load_data():
    df = pd.read_csv("fremont_cleaned.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    return df


MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]


# Making the chart's bg color and papercolor follow Streamlit's active light/dark theme
def themed(fig):
    is_dark = st.context.theme.get("type") == "dark"
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white" if is_dark else "#1a1a1a",
    )
    return fig


df = load_data()

# Year dropdown with All toggle
years = sorted(df["Year"].unique().tolist())
year_options = ["All"] + [str(y) for y in years]

if "year_selection" not in st.session_state:
    st.session_state.year_selection = ["All"]
if "year_prev" not in st.session_state:
    st.session_state.year_prev = ["All"]


def on_year_change():
    current = list(st.session_state.year_selection or [])
    prev = list(st.session_state.year_prev)
    if "All" in current and len(current) > 1:
        if "All" in prev:
            # "All" was on, user selected a year: remove "All"
            st.session_state.year_selection = [
                y for y in current if y != "All"]
        else:
            # User selected "All": clear individual years
            st.session_state.year_selection = ["All"]
    st.session_state.year_prev = list(st.session_state.year_selection or [])


st.sidebar.multiselect(
    "Year",
    options=year_options,
    key="year_selection",
    on_change=on_year_change,
    placeholder="Select year(s)"
)

selected_year_vals = st.session_state.year_selection or []
if "All" in selected_year_vals or not selected_year_vals:
    selected_years = years
else:
    selected_years = [int(y) for y in selected_year_vals]

st.sidebar.markdown("---")

# Month pills with All toggle
if "month_selection" not in st.session_state:
    st.session_state.month_selection = ["All"]
if "month_prev" not in st.session_state:
    st.session_state.month_prev = ["All"]


def on_month_change():
    current = list(st.session_state.month_selection or [])
    prev = list(st.session_state.month_prev)
    if "All" in current and len(current) > 1:
        if "All" in prev:
            # "All" was already on — user just selected a month: remove "All"
            st.session_state.month_selection = [
                m for m in current if m != "All"]
        else:
            # User just selected "All": clear individual months
            st.session_state.month_selection = ["All"]
    st.session_state.month_prev = list(st.session_state.month_selection or [])


st.sidebar.pills(
    "Month",
    options=["All"] + MONTH_NAMES,
    selection_mode="multi",
    key="month_selection",
    on_change=on_month_change
)

selected_month_pills = st.session_state.month_selection or []
if "All" in selected_month_pills or not selected_month_pills:
    selected_month_names = MONTH_NAMES
else:
    selected_month_names = list(selected_month_pills)

st.sidebar.markdown("---")

# Direction pills — single selection
direction = st.sidebar.pills(
    "Direction",
    options=["Total", "West", "East"],
    selection_mode="single",
    default="Total"
)

# Applying filters
selected_month_nums = [i + 1 for i, m in enumerate(MONTH_NAMES)
                       if m in selected_month_names]

filtered = df[
    df["Year"].isin(selected_years) &
    df["Month"].isin(selected_month_nums)
]


# Title & paragraph
st.title("L7 Data Visualization and Communication CA2")
st.markdown(
    "**Diego Javiel** (sba25068) \n\n"
    "Interactive dashboard showing cycling patterns from **2012 to 2024**. \n\n"
    "Use the sidebar to filter by year, month or direction. \n\n"
    "**Dataset:** Fremont Bridge Bicycle Counter"
)
st.markdown("---")

# KPI metrics row
col1, col2, col3, col4 = st.columns(4)

total_cyclists = int(filtered[direction].sum())
daily_avg = int(
    filtered.groupby(filtered["Date"].dt.date)[direction].sum().mean()
) if not filtered.empty else 0

peak_hour_val = filtered.groupby("Hour")[direction].mean()
peak_hour = int(peak_hour_val.idxmax()) if not filtered.empty else 0

busiest_month_num = filtered.groupby("Month")[direction].sum()
busiest_month = (
    MONTH_NAMES[int(busiest_month_num.idxmax()) - 1]
    if not filtered.empty else "N/A"
)

col1.metric("Total Cyclists", f"{total_cyclists:,}")
col2.metric("Daily Average", f"{daily_avg:,}")
col3.metric("Peak Hour", f"{peak_hour:02d}:00")
col4.metric("Busiest Month", busiest_month)

st.markdown("---")

# Monthly trend line chart
st.subheader("Monthly Cyclist Trend")

monthly = (
    filtered.groupby(filtered["Date"].dt.to_period("M"))[direction]
    .sum()
    .reset_index()
)
monthly["Date"] = monthly["Date"].dt.to_timestamp()

fig_trend = px.line(
    monthly, x="Date", y=direction,
    labels={direction: "Cyclists", "Date": "Month"},
    color_discrete_sequence=["#2ecc71"]
)
themed(fig_trend)

st.plotly_chart(fig_trend, use_container_width=True)


# Hour of day + Day of week side by side
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Average Cyclists by Hour of Day")
    hourly = filtered.groupby("Hour")[direction].mean().reset_index()
    fig_hour = px.bar(
        hourly, x="Hour", y=direction,
        labels={direction: "Avg Cyclists", "Hour": "Hour of Day"},
        color_discrete_sequence=["#3498db"]
    )
    themed(fig_hour)
    st.plotly_chart(fig_hour, use_container_width=True)

with col_right:
    st.subheader("Average Cyclists by Day of Week")
    daily_avg_df = (
        filtered.groupby("DayOfWeek")[direction]
        .mean()
        .reindex(DAY_ORDER)
        .reset_index()
    )
    fig_day = px.bar(
        daily_avg_df, x="DayOfWeek", y=direction,
        labels={direction: "Avg Cyclists", "DayOfWeek": "Day"},
        color_discrete_sequence=["#e74c3c"]
    )
    themed(fig_day)
    st.plotly_chart(fig_day, use_container_width=True)

# Hour x Day heatmap — commuter pattern across both dimensions at once
st.subheader("Cyclist Volume Heatmap — Hour vs Day of Week")
fig_heatmap = px.density_heatmap(
    filtered, x="Hour", y="DayOfWeek", z=direction, histfunc="avg",
    category_orders={"DayOfWeek": DAY_ORDER},
    labels={direction: "Avg Cyclists",
            "Hour": "Hour of Day", "DayOfWeek": "Day"},
    color_continuous_scale="Viridis"
)
themed(fig_heatmap)
st.plotly_chart(fig_heatmap, use_container_width=True)

# Seasonal pattern chart
st.subheader("Seasonal Pattern — Average Cyclists by Month")
seasonal = filtered.groupby("Month")[direction].mean().reset_index()
seasonal["MonthName"] = [MONTH_NAMES[m - 1] for m in seasonal["Month"]]

fig_season = px.bar(
    seasonal, x="MonthName", y=direction,
    labels={direction: "Avg Cyclists", "MonthName": "Month"},
    color_discrete_sequence=["#9b59b6"],
    category_orders={"MonthName": MONTH_NAMES}
)
themed(fig_season)
st.plotly_chart(fig_season, use_container_width=True)

# West vs East split (proportion) + trend, side by side
col_donut, col_we = st.columns(2)

with col_donut:
    st.subheader("West vs East Sidewalk — Overall Split")
    we_totals = filtered[["West", "East"]].sum()
    fig_donut = px.pie(
        names=we_totals.index, values=we_totals.values,
        hole=0.5,
        color=we_totals.index,
        color_discrete_map={"West": "#f39c12", "East": "#1abc9c"}
    )
    themed(fig_donut)
    st.plotly_chart(fig_donut, use_container_width=True)

with col_we:
    st.subheader("West vs East Sidewalk — Monthly Comparison")
    we_monthly = (
        filtered.groupby(filtered["Date"].dt.to_period("M"))[["West", "East"]]
        .sum()
        .reset_index()
    )
    we_monthly["Date"] = we_monthly["Date"].dt.to_timestamp()

    fig_we = px.line(
        we_monthly, x="Date", y=["West", "East"],
        labels={"value": "Cyclists", "Date": "Month", "variable": "Sidewalk"},
        color_discrete_sequence=["#f39c12", "#1abc9c"]
    )
    themed(fig_we)
    st.plotly_chart(fig_we, use_container_width=True)

st.markdown("---")
st.caption(
    "Data source: Seattle Open Data — Fremont Bridge Bicycle Counter (2012–2024)")
