import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NBA Analytics Dashboard",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Barlow', sans-serif;
        background-color: #0a0e1a;
        color: #e8eaf0;
    }

    .stApp { background-color: #0a0e1a; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f1525;
        border-right: 1px solid #1e2a45;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stSlider label {
        color: #7b8db0 !important;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #131d35 0%, #0f1828 100%);
        border: 1px solid #1e2d50;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #e8471a, #f5a623);
    }
    .kpi-value {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        color: #f5a623;
        line-height: 1;
        margin-bottom: 4px;
    }
    .kpi-label {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.4px;
        text-transform: uppercase;
        color: #7b8db0;
    }
    .kpi-sub {
        font-size: 12px;
        color: #4a5a7a;
        margin-top: 4px;
    }

    /* Section headers */
    .section-header {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #e8eaf0;
        border-left: 4px solid #e8471a;
        padding-left: 12px;
        margin: 24px 0 16px 0;
    }

    /* Page title */
    .main-title {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: 3px;
        text-transform: uppercase;
        background: linear-gradient(90deg, #ffffff, #f5a623);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1;
    }
    .main-subtitle {
        font-size: 13px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #4a5a7a;
        margin-top: 4px;
    }

    /* Plotly chart backgrounds */
    .js-plotly-plot { border-radius: 12px; }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    div[data-testid="metric-container"] {
        background: #131d35;
        border: 1px solid #1e2d50;
        border-radius: 10px;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    games         = pd.read_csv("games.csv", low_memory=False)
    games_details = pd.read_csv("games_details.csv", low_memory=False)
    teams         = pd.read_csv("teams.csv")
    ranking       = pd.read_csv("ranking.csv", low_memory=False)

    games["GAME_DATE_EST"] = pd.to_datetime(games["GAME_DATE_EST"])
    games["HOME_TEAM_WINS"] = pd.to_numeric(games["HOME_TEAM_WINS"], errors="coerce")

    games = games.merge(
        teams[["TEAM_ID","NICKNAME"]].rename(columns={"TEAM_ID":"HOME_TEAM_ID","NICKNAME":"HOME_TEAM_NAME"}),
        on="HOME_TEAM_ID", how="left"
    )
    games = games.merge(
        teams[["TEAM_ID","NICKNAME"]].rename(columns={"TEAM_ID":"VISITOR_TEAM_ID","NICKNAME":"AWAY_TEAM_NAME"}),
        on="VISITOR_TEAM_ID", how="left"
    )
    return games, games_details, teams, ranking

with st.spinner("Loading NBA data..."):
    games, games_details, teams, ranking = load_data()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏀 NBA Analytics")
    st.markdown("---")

    seasons = sorted(games["SEASON"].unique(), reverse=True)
    selected_seasons = st.multiselect(
        "Seasons",
        options=seasons,
        default=[2022, 2021, 2020]
    )
    if not selected_seasons:
        selected_seasons = [2022]

    all_teams = sorted(teams["NICKNAME"].dropna().unique())
    selected_teams = st.multiselect(
        "Filter by Team",
        options=all_teams,
        default=[]
    )

    top_n = st.slider("Top N Players", min_value=5, max_value=30, value=15)

    st.markdown("---")
    st.markdown(
        "<div style='font-size:11px;color:#4a5a7a;letter-spacing:1px;'>DATA SOURCE<br>"
        "<span style='color:#7b8db0'>Snowflake · NBA_ANALYTICS</span><br>"
        "20 Seasons · 900K+ Records</div>",
        unsafe_allow_html=True
    )

# ── Filter data ───────────────────────────────────────────────────────────────
filtered_games = games[games["SEASON"].isin(selected_seasons)]
if selected_teams:
    filtered_games = filtered_games[
        filtered_games["HOME_TEAM_NAME"].isin(selected_teams) |
        filtered_games["AWAY_TEAM_NAME"].isin(selected_teams)
    ]

filtered_details = games_details[
    games_details["GAME_ID"].isin(filtered_games["GAME_ID"])
]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">NBA Performance Analytics</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="main-subtitle">Seasons {min(selected_seasons)}–{max(selected_seasons)} &nbsp;·&nbsp; '
    f'{len(filtered_games):,} Games &nbsp;·&nbsp; {len(filtered_details):,} Player Records &nbsp;·&nbsp; '
    f'Powered by Snowflake</div>',
    unsafe_allow_html=True
)
st.markdown("<br>", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_games   = len(filtered_games)
home_win_rate = filtered_games["HOME_TEAM_WINS"].mean() * 100
avg_pts_game  = (filtered_games["PTS_home"].mean() + filtered_games["PTS_away"].mean()) / 2
avg_fg_pct    = filtered_details["FG_PCT"].mean() * 100

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{total_games:,}</div>
        <div class="kpi-label">Total Games</div>
        <div class="kpi-sub">{len(selected_seasons)} season(s) selected</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{home_win_rate:.1f}%</div>
        <div class="kpi-label">Home Win Rate</div>
        <div class="kpi-sub">across all selected seasons</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{avg_pts_game:.1f}</div>
        <div class="kpi-label">Avg Points / Game</div>
        <div class="kpi-sub">home & away combined</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{avg_fg_pct:.1f}%</div>
        <div class="kpi-label">Avg FG%</div>
        <div class="kpi-sub">player-level average</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Scoring Trend + Home Advantage ────────────────────────────────────
st.markdown('<div class="section-header">Scoring & Home Advantage Trends</div>', unsafe_allow_html=True)
col1, col2 = st.columns([3, 2])

with col1:
    season_avg = (
        games.groupby("SEASON")
        .agg(avg_home=("PTS_home","mean"), avg_away=("PTS_away","mean"))
        .reset_index()
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=season_avg["SEASON"], y=season_avg["avg_home"],
        mode="lines+markers", name="Home",
        line=dict(color="#f5a623", width=2.5),
        marker=dict(size=7, color="#f5a623")
    ))
    fig.add_trace(go.Scatter(
        x=season_avg["SEASON"], y=season_avg["avg_away"],
        mode="lines+markers", name="Away",
        line=dict(color="#e8471a", width=2.5, dash="dot"),
        marker=dict(size=7, color="#e8471a")
    ))
    fig.update_layout(
        title="Average Points Per Game by Season",
        paper_bgcolor="#0f1828", plot_bgcolor="#0f1828",
        font=dict(color="#7b8db0", family="Barlow"),
        legend=dict(bgcolor="#0f1828", bordercolor="#1e2d50"),
        xaxis=dict(gridcolor="#1a2540", tickcolor="#1a2540", title="Season"),
        yaxis=dict(gridcolor="#1a2540", tickcolor="#1a2540", title="Avg Points"),
        margin=dict(t=40, b=20, l=20, r=20),
        height=320
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    home_adv = (
        games.merge(teams[["TEAM_ID","NICKNAME"]], left_on="HOME_TEAM_ID", right_on="TEAM_ID")
        .groupby("NICKNAME")
        .agg(home_pts=("PTS_home","mean"), away_pts=("PTS_away","mean"))
        .assign(advantage=lambda x: x["home_pts"] - x["away_pts"])
        .sort_values("advantage", ascending=False)
        .head(10)
        .reset_index()
    )
    fig2 = go.Figure(go.Bar(
        x=home_adv["advantage"],
        y=home_adv["NICKNAME"],
        orientation="h",
        marker=dict(
            color=home_adv["advantage"],
            colorscale=[[0,"#1e2d50"],[0.5,"#e8471a"],[1,"#f5a623"]],
            showscale=False
        ),
        text=home_adv["advantage"].round(1),
        textposition="outside",
        textfont=dict(color="#e8eaf0", size=11)
    ))
    fig2.update_layout(
        title="Top 10 Home Court Advantage (pts)",
        paper_bgcolor="#0f1828", plot_bgcolor="#0f1828",
        font=dict(color="#7b8db0", family="Barlow"),
        xaxis=dict(gridcolor="#1a2540", title="Point Advantage"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        margin=dict(t=40, b=20, l=20, r=40),
        height=320
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Top Scorers + FG% Distribution ────────────────────────────────────
st.markdown('<div class="section-header">Player Performance Analysis</div>', unsafe_allow_html=True)
col3, col4 = st.columns([2, 3])

with col3:
    top_scorers = (
        filtered_details[filtered_details["PTS"].notna()]
        .groupby("PLAYER_NAME")
        .agg(avg_pts=("PTS","mean"), games=("GAME_ID","nunique"))
        .query("games >= 20")
        .sort_values("avg_pts", ascending=True)
        .tail(top_n)
        .reset_index()
    )
    fig3 = go.Figure(go.Bar(
        x=top_scorers["avg_pts"],
        y=top_scorers["PLAYER_NAME"],
        orientation="h",
        marker=dict(
            color=top_scorers["avg_pts"],
            colorscale=[[0,"#1a3050"],[0.6,"#e8471a"],[1,"#f5a623"]],
            showscale=False
        ),
        text=top_scorers["avg_pts"].round(1),
        textposition="outside",
        textfont=dict(color="#e8eaf0", size=10)
    ))
    fig3.update_layout(
        title=f"Top {top_n} Scorers (Avg PPG, min 20 games)",
        paper_bgcolor="#0f1828", plot_bgcolor="#0f1828",
        font=dict(color="#7b8db0", family="Barlow"),
        xaxis=dict(gridcolor="#1a2540", title="Avg Points Per Game"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10)),
        margin=dict(t=40, b=20, l=20, r=50),
        height=420
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    # Scatter: avg pts vs avg rebounds, bubble = assists
    player_stats = (
        filtered_details[
            filtered_details["PTS"].notna() &
            filtered_details["REB"].notna() &
            filtered_details["AST"].notna()
        ]
        .groupby(["PLAYER_NAME","TEAM_ABBREVIATION"])
        .agg(avg_pts=("PTS","mean"), avg_reb=("REB","mean"),
             avg_ast=("AST","mean"), games=("GAME_ID","nunique"))
        .query("games >= 30")
        .reset_index()
    )
    fig4 = px.scatter(
        player_stats,
        x="avg_reb", y="avg_pts",
        size="avg_ast", color="avg_pts",
        hover_name="PLAYER_NAME",
        hover_data={"TEAM_ABBREVIATION": True, "games": True,
                    "avg_pts":":.1f", "avg_reb":":.1f", "avg_ast":":.1f"},
        color_continuous_scale=["#1a3050","#e8471a","#f5a623"],
        size_max=28,
        labels={"avg_reb":"Avg Rebounds","avg_pts":"Avg Points","avg_ast":"Avg Assists"}
    )
    fig4.update_layout(
        title="Points vs Rebounds (bubble size = Assists, min 30 games)",
        paper_bgcolor="#0f1828", plot_bgcolor="#0f1828",
        font=dict(color="#7b8db0", family="Barlow"),
        xaxis=dict(gridcolor="#1a2540"),
        yaxis=dict(gridcolor="#1a2540"),
        coloraxis_showscale=False,
        margin=dict(t=40, b=20, l=20, r=20),
        height=420
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: Team Win Rate + Conference Standings ───────────────────────────────
st.markdown('<div class="section-header">Team Performance & Standings</div>', unsafe_allow_html=True)
col5, col6 = st.columns(2)

with col5:
    team_wins = (
        filtered_games.groupby("HOME_TEAM_NAME")
        .agg(total=("GAME_ID","count"), wins=("HOME_TEAM_WINS","sum"))
        .assign(win_pct=lambda x: x["wins"]/x["total"]*100)
        .sort_values("win_pct", ascending=False)
        .reset_index()
        .dropna(subset=["HOME_TEAM_NAME"])
    )
    fig5 = go.Figure(go.Bar(
        x=team_wins["HOME_TEAM_NAME"],
        y=team_wins["win_pct"],
        marker=dict(
            color=team_wins["win_pct"],
            colorscale=[[0,"#1a2540"],[0.5,"#e8471a"],[1,"#f5a623"]],
            showscale=False
        )
    ))
    fig5.add_hline(y=50, line_dash="dash", line_color="#4a5a7a",
                   annotation_text="50% line", annotation_font_color="#4a5a7a")
    fig5.update_layout(
        title="Home Win % by Team",
        paper_bgcolor="#0f1828", plot_bgcolor="#0f1828",
        font=dict(color="#7b8db0", family="Barlow"),
        xaxis=dict(gridcolor="#1a2540", tickangle=-45, tickfont=dict(size=9)),
        yaxis=dict(gridcolor="#1a2540", title="Win %"),
        margin=dict(t=40, b=80, l=20, r=20),
        height=360
    )
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    latest_season_id = ranking["SEASON_ID"].max()
    latest_date      = ranking[ranking["SEASON_ID"]==latest_season_id]["STANDINGSDATE"].max()
    standings = (
        ranking[
            (ranking["SEASON_ID"]==latest_season_id) &
            (ranking["STANDINGSDATE"]==latest_date)
        ][["CONFERENCE","TEAM","W","L","W_PCT","HOME_RECORD","ROAD_RECORD"]]
        .sort_values(["CONFERENCE","W_PCT"], ascending=[True,False])
        .reset_index(drop=True)
    )
    standings["W_PCT"] = (standings["W_PCT"]*100).round(1).astype(str) + "%"

    fig6 = go.Figure(data=[go.Table(
        columnwidth=[60, 120, 40, 40, 70, 80, 80],
        header=dict(
            values=["CONF","TEAM","W","L","WIN%","HOME","ROAD"],
            fill_color="#1e2d50",
            font=dict(color="#f5a623", size=11, family="Barlow Condensed"),
            align="center", height=32
        ),
        cells=dict(
            values=[standings[c] for c in ["CONFERENCE","TEAM","W","L","W_PCT","HOME_RECORD","ROAD_RECORD"]],
            fill_color=[["#0f1828" if i%2==0 else "#131d35" for i in range(len(standings))]],
            font=dict(color="#c8d0e0", size=11, family="Barlow"),
            align=["center","left","center","center","center","center","center"],
            height=26
        )
    )])
    fig6.update_layout(
        title=f"Conference Standings — Latest ({latest_date})",
        paper_bgcolor="#0f1828",
        font=dict(color="#7b8db0", family="Barlow"),
        margin=dict(t=40, b=0, l=0, r=0),
        height=360
    )
    st.plotly_chart(fig6, use_container_width=True)

# ── Row 4: Data Quality Summary ───────────────────────────────────────────────
st.markdown('<div class="section-header">Data Quality & ETL Summary</div>', unsafe_allow_html=True)

total_records  = len(games_details)
missing_pts    = games_details["PTS"].isna().sum()
dnp_records    = (games_details["MIN"].isna() | (games_details["MIN"]=="DNP")).sum()
null_pct       = missing_pts / total_records * 100

q1, q2, q3, q4 = st.columns(4)
with q1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{total_records:,}</div>
        <div class="kpi-label">Total Player Records</div>
        <div class="kpi-sub">across games_details table</div>
    </div>""", unsafe_allow_html=True)
with q2:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{missing_pts:,}</div>
        <div class="kpi-label">Missing PTS Values</div>
        <div class="kpi-sub">{null_pct:.2f}% null rate</div>
    </div>""", unsafe_allow_html=True)
with q3:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{dnp_records:,}</div>
        <div class="kpi-label">DNP / No Minutes</div>
        <div class="kpi-sub">excluded from averages</div>
    </div>""", unsafe_allow_html=True)
with q4:
    clean_pct = 100 - null_pct
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{clean_pct:.1f}%</div>
        <div class="kpi-label">Data Completeness</div>
        <div class="kpi-sub">after ETL validation</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;font-size:11px;color:#2a3550;letter-spacing:1px;'>"
    "NBA ANALYTICS DASHBOARD &nbsp;·&nbsp; DATA SOURCED FROM SNOWFLAKE (NBA_ANALYTICS.NBA_DATA) "
    "&nbsp;·&nbsp; BUILT WITH PYTHON · STREAMLIT · PLOTLY"
    "</div>",
    unsafe_allow_html=True
)