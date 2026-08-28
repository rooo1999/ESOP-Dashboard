"""
ESOP Exit Planning Dashboard
----------------------------
A client-facing Streamlit tool for MIRA Money clients holding ESOPs in a
company that is pre-IPO or newly listed. The client can log one or more
ESOP grants (different years, prices, vesting rules), track vesting,
value the holding (manually pre-listing, live via NSE ticker once
listed), estimate tax impact, and get a staggered exit plan for whatever
portion they don't want to hold long-term.

Run with:  streamlit run esop_dashboard.py
(place the accompanying .streamlit/config.toml alongside it for the
default dark theme.)
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# --------------------------------------------------------------------------
# PAGE CONFIG + THEME
# --------------------------------------------------------------------------
st.set_page_config(page_title="ESOP Exit Planning Dashboard", layout="wide")

NAVY_BG = "#050505"
CARD_BG = "#101010"
CARD_BG_2 = "#181818"
GOLD = "#D4AF37"
GOLD_SOFT = "#F0D584"
TEXT = "#F2F2F0"
MUTED = "#A3A0A0"
GREEN = "#3BAE87"
RED = "#D9573F"
SILVER = "#C7C8C6"
BRONZE = "#C08A52"
BORDER = "rgba(212,175,55,0.50)"

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, -apple-system, sans-serif", color=TEXT, size=13),
    margin=dict(t=36, l=10, r=10, b=10),
    legend=dict(orientation="h", y=1.14, bgcolor="rgba(0,0,0,0)"),
)

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background: radial-gradient(circle at 15% -10%, #141414 0%, {NAVY_BG} 55%); }}

    h1, h2, h3, h4 {{ font-family: 'Fraunces', serif; color: {TEXT}; font-weight: 600; }}
    h1 {{ letter-spacing: 0.01em; }}

    .brand-row {{ display:flex; justify-content:space-between; align-items:baseline;
                  border-bottom: 1px solid {BORDER}; padding-bottom: 14px; margin-bottom: 6px; }}
    .brand-mark {{ font-size: 0.78rem; letter-spacing: 0.22em; color: {GOLD}; font-weight: 600; }}
    .brand-client {{ font-size: 0.85rem; color: {MUTED}; letter-spacing: 0.02em; }}

    .kpi-card {{
        background: linear-gradient(160deg, {CARD_BG_2} 0%, {CARD_BG} 100%);
        border: 1px solid {BORDER};
        border-top: 2px solid {GOLD};
        border-radius: 12px;
        padding: 18px 20px;
        color: {TEXT};
        box-shadow: 0 8px 24px rgba(0,0,0,0.28);
        height: 100%;
    }}
    .kpi-label {{ font-size: 0.72rem; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.1em; }}
    .kpi-value {{ font-size: 1.65rem; font-weight: 700; margin-top: 6px; font-family: 'Fraunces', serif; }}
    .kpi-sub {{ font-size: 0.76rem; color: {MUTED}; margin-top: 6px; }}
    .kpi-accent {{ color: {GOLD_SOFT}; }}

    .section-note {{
        background: linear-gradient(120deg, rgba(212,175,55,0.10), rgba(212,175,55,0.03));
        border: 1px solid {BORDER};
        border-left: 3px solid {GOLD};
        padding: 12px 16px; border-radius: 8px; font-size: 0.84rem; color: {MUTED};
    }}

    .pill {{ display:inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem;
             letter-spacing: 0.04em; font-weight: 600; }}
    .pill-green {{ background: rgba(59,174,135,0.15); color: {GREEN}; border: 1px solid rgba(59,174,135,0.35); }}
    .pill-gold {{ background: rgba(212,175,55,0.15); color: {GOLD_SOFT}; border: 1px solid rgba(212,175,55,0.35); }}
    .pill-silver {{ background: rgba(199,200,198,0.12); color: {SILVER}; border: 1px solid rgba(199,200,198,0.30); }}
    .pill-bronze {{ background: rgba(192,138,82,0.15); color: {BRONZE}; border: 1px solid rgba(192,138,82,0.35); }}

    div[data-testid="stMetricValue"] {{ color: {TEXT}; font-family: 'Fraunces', serif; }}
    div[data-testid="stMetricLabel"] {{ color: {MUTED}; }}
    .stTabs [data-baseweb="tab"] {{ font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase; font-size: 0.8rem; color: {MUTED}; }}
    .stTabs [aria-selected="true"] {{ color: {TEXT} !important; }}
    .stTabs [data-baseweb="tab-highlight"] {{ background-color: {GOLD}; }}
    section[data-testid="stSidebar"] {{ border-right: 1px solid {BORDER}; background-color: {NAVY_BG}; }}
    hr {{ border-color: {BORDER}; }}
    .stDataFrame {{ border: 1px solid {BORDER}; border-radius: 10px; overflow: hidden; }}

    .stButton > button {{
        background: {CARD_BG}; border: 1px solid {BORDER}; color: {TEXT};
        border-radius: 8px; font-weight: 500;
    }}
    .stButton > button:hover {{ border-color: {GOLD}; color: {GOLD_SOFT}; background: {CARD_BG_2}; }}
    .stButton > button:focus:not(:active) {{ border-color: {GOLD}; color: {GOLD_SOFT}; }}

    div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="datepicker"] {{
        background-color: {CARD_BG} !important; border-color: {BORDER} !important; border-radius: 8px !important;
    }}
    .streamlit-expanderHeader {{ background-color: {CARD_BG}; border-radius: 8px; }}
    div[data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-radius: 10px; }}

    input[type="checkbox"], input[type="radio"] {{ accent-color: {GOLD}; }}
</style>
""", unsafe_allow_html=True)


def kpi_card(label, value, sub="", accent=False):
    cls = "kpi-value kpi-accent" if accent else "kpi-value"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="{cls}">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def inr(x, decimals=0):
    """Format a number in Indian comma style with a rupee symbol."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "Rs. 0"
    neg = x < 0
    x = abs(x)
    s = f"{x:,.{decimals}f}"
    int_part, _, dec_part = s.partition(".")
    int_part = int_part.replace(",", "")
    if len(int_part) > 3:
        last3 = int_part[-3:]
        rest = int_part[:-3]
        rest = ",".join([rest[max(i - 2, 0):i] for i in range(len(rest), 0, -2)][::-1])
        int_part = rest + "," + last3
    out = "Rs. " + int_part + (("." + dec_part) if dec_part else "")
    return ("-" + out) if neg else out


FREQ_MONTHS = {"Monthly": 1, "Quarterly": 3, "Half-yearly": 6, "Yearly": 12}
VESTING_PATTERNS = [
    "1-yr cliff + annual (4 yrs)",
    "1-yr cliff + quarterly (4 yrs)",
    "Straight-line monthly (no cliff)",
    "Custom",
]

# --------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("#### Client & Company")
    client_name = st.text_input("Client name", value="")
    company_name = st.text_input("Company", value="")

st.markdown(f"""
<div class="brand-row">
    <div>
        <div class="brand-mark">MIRA MONEY &nbsp;·&nbsp; PRIVATE WEALTH</div>
        <h1 style="margin:2px 0 0 0;">ESOP Exit Planning</h1>
    </div>
    <div class="brand-client">{(client_name or "Client") + (" &middot; " + company_name if company_name else "")}</div>
</div>
""", unsafe_allow_html=True)
st.write("")

# --------------------------------------------------------------------------
# SIDEBAR — MULTIPLE ESOP GRANTS
# --------------------------------------------------------------------------
def default_grant(gid):
    return {
        "id": gid, "label": f"Grant {gid}",
        "quantity": 10000, "strike_price": 50.0,
        "grant_date": date.today() - relativedelta(years=1),
        "vesting_type": VESTING_PATTERNS[0],
        "cliff_months": 12, "total_years": 4,
        "frequency": "Quarterly",
    }


if "grants" not in st.session_state:
    st.session_state.grants = [default_grant(1)]
    st.session_state.next_grant_id = 2

with st.sidebar:
    st.markdown("#### ESOP Grants")
    st.caption("Add a row for every grant year — each can have its own price, date and vesting rules.")

    remove_id = None
    for g in st.session_state.grants:
        gid = g["id"]
        with st.expander(g["label"], expanded=(gid == st.session_state.grants[0]["id"])):
            g["label"] = st.text_input("Label", value=g["label"], key=f"label_{gid}")
            g["quantity"] = st.number_input("Shares granted", min_value=0, value=g["quantity"], step=100, key=f"qty_{gid}")
            g["strike_price"] = st.number_input("Strike price (Rs./share)", min_value=0.0, value=g["strike_price"], step=1.0, key=f"strike_{gid}")
            g["grant_date"] = st.date_input("Grant date", value=g["grant_date"], key=f"gdate_{gid}")
            g["vesting_type"] = st.selectbox("Vesting pattern", VESTING_PATTERNS,
                                              index=VESTING_PATTERNS.index(g["vesting_type"]), key=f"vtype_{gid}")
            if g["vesting_type"] != "Straight-line monthly (no cliff)":
                g["cliff_months"] = st.number_input("Cliff (months)", min_value=0, value=g["cliff_months"], step=1, key=f"cliff_{gid}")
            else:
                g["cliff_months"] = 0
            g["total_years"] = st.number_input("Total vesting period (years)", min_value=1, value=g["total_years"], step=1, key=f"years_{gid}")
            if g["vesting_type"] == "Custom":
                g["frequency"] = st.selectbox("Vesting frequency", list(FREQ_MONTHS.keys()),
                                               index=list(FREQ_MONTHS.keys()).index(g["frequency"]), key=f"freq_{gid}")
            if len(st.session_state.grants) > 1:
                if st.button("Remove this grant", key=f"remove_{gid}"):
                    remove_id = gid

    if remove_id is not None:
        st.session_state.grants = [g for g in st.session_state.grants if g["id"] != remove_id]
        st.rerun()

    if st.button("+ Add another grant", use_container_width=True):
        new_id = st.session_state.next_grant_id
        st.session_state.grants.append(default_grant(new_id))
        st.session_state.next_grant_id += 1
        st.rerun()

    st.markdown("#### IPO / Listing Status")
    is_listed = st.radio("Has the company listed on a stock exchange?", ["Not yet listed (Pre-IPO)", "Listed"])

    if is_listed == "Listed":
        ticker = st.text_input("NSE ticker symbol (e.g. TATAMOTORS.NS)", value="")
        listing_date = st.date_input("Listing date", value=date.today())
        manual_price_override = st.checkbox("Enter price manually instead of fetching live", value=not YFINANCE_AVAILABLE)
        lock_in_months = st.number_input("ESOP-specific lock-in after listing (months)", min_value=0, value=6, step=1,
                                          help="Separate from any promoter lock-in — this is the period your company's ESOP policy requires before you can sell.")
    else:
        ticker = ""
        listing_date = None
        manual_price_override = True
        expected_ipo_date = st.date_input("Expected IPO date (approximate)", value=date.today() + relativedelta(months=6))
        lock_in_months = st.number_input("Expected ESOP lock-in after listing (months)", min_value=0, value=6, step=1)

    st.markdown("#### Price Assumption")
    if manual_price_override or is_listed == "Not yet listed (Pre-IPO)":
        default_strike = st.session_state.grants[0]["strike_price"] if st.session_state.grants else 50.0
        manual_price = st.number_input(
            "Illustrative fair value per share (Rs.)",
            min_value=0.0, value=max(default_strike * 3, 100.0), step=1.0,
            help="Use last funding round valuation / grey-market premium / expected IPO band midpoint. Purely illustrative pre-listing."
        )
    else:
        manual_price = None

    growth_assumption = st.slider("Assumed annual price growth for future exit legs (%)", -20, 40, 0,
                                   help="Optional — set to 0 to value all future exits at today's price.")

    st.markdown("#### Tax Inputs")
    tax_slab = st.selectbox("Income-tax slab (for perquisite tax)", ["30%", "20%", "10%", "5%", "0% / Nil"])
    slab_map = {"30%": 0.30, "20%": 0.20, "10%": 0.10, "5%": 0.05, "0% / Nil": 0.0}
    cess = 0.04

st.markdown(
    '<div class="section-note">Tax rates used below — LTCG 12.5% beyond a 1-year holding from the exercise date, '
    'STCG 20% within 1 year, Rs. 1.25L LTCG exemption per year, perquisite tax at slab + 4% cess on exercise — '
    'reflect rules as of FY2024-25. Please verify current rates before advising a client; this is a planning aid, '
    'not tax or investment advice.</div>',
    unsafe_allow_html=True
)
st.write("")

# --------------------------------------------------------------------------
# BUILD COMBINED VESTING SCHEDULE ACROSS ALL GRANTS
# --------------------------------------------------------------------------
def generate_schedule_for_grant(g):
    total, grant_dt = g["quantity"], g["grant_date"]
    cliff_m, years, pattern = g["cliff_months"], g["total_years"], g["vesting_type"]
    rows = []
    if pattern == "1-yr cliff + annual (4 yrs)":
        n = years
        per = total // n
        rem = total - per * n
        for i in range(n):
            vd = grant_dt + relativedelta(months=cliff_m) + relativedelta(years=i)
            rows.append((f"Year {i+1}", vd, int(per + (rem if i == n - 1 else 0))))
    elif pattern == "1-yr cliff + quarterly (4 yrs)":
        n = years * 4
        per = total // n
        rem = total - per * n
        for i in range(n):
            vd = grant_dt + relativedelta(months=cliff_m) + relativedelta(months=3 * i)
            rows.append((f"Q{i+1}", vd, int(per + (rem if i == n - 1 else 0))))
    elif pattern == "Straight-line monthly (no cliff)":
        n = years * 12
        per = total // n
        rem = total - per * n
        for i in range(n):
            vd = grant_dt + relativedelta(months=i + 1)
            rows.append((f"M{i+1}", vd, int(per + (rem if i == n - 1 else 0))))
    else:  # Custom — cliff + chosen frequency
        period_m = FREQ_MONTHS[g["frequency"]]
        span_m = years * 12 - cliff_m
        n = max(1, round(span_m / period_m))
        per = total // n
        rem = total - per * n
        for i in range(n):
            vd = grant_dt + relativedelta(months=cliff_m) + relativedelta(months=period_m * i)
            rows.append((f"{g['frequency'][:1]}{i+1}", vd, int(per + (rem if i == n - 1 else 0))))

    df = pd.DataFrame(rows, columns=["Tranche", "Vest Date", "Quantity"])
    df["Grant"] = g["label"]
    df["Strike Price"] = g["strike_price"]
    return df


grant_signature = tuple(
    (g["label"], g["quantity"], g["strike_price"], g["grant_date"], g["vesting_type"],
     g["cliff_months"], g["total_years"], g.get("frequency"))
    for g in st.session_state.grants
)

if st.session_state.get("grant_signature") != grant_signature:
    pieces = [generate_schedule_for_grant(g) for g in st.session_state.grants]
    combined = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(
        columns=["Tranche", "Vest Date", "Quantity", "Grant", "Strike Price"])
    combined["Vest Date"] = pd.to_datetime(combined["Vest Date"])
    combined = combined.sort_values("Vest Date").reset_index(drop=True)
    combined["Cumulative Vested"] = combined["Quantity"].cumsum()
    combined["Exercised?"] = False
    combined["Exercise Date"] = pd.NaT
    combined["FMV at Exercise (Rs.)"] = 0.0
    st.session_state.schedule_df = combined
    st.session_state.grant_signature = grant_signature

total_shares = int(sum(g["quantity"] for g in st.session_state.grants))

tabs = st.tabs(["Vesting Schedule", "Value & Tax", "Exit Plan", "Deployment Plan"])

# --------------------------------------------------------------------------
# TAB 1 — VESTING SCHEDULE
# --------------------------------------------------------------------------
with tabs[0]:
    st.subheader("Vesting schedule")
    st.caption("Tick 'Exercised?' and fill exercise details for tranches already exercised — this drives tax and holding-period calculations on the other tabs.")

    edited = st.data_editor(
        st.session_state.schedule_df,
        column_order=["Grant", "Tranche", "Vest Date", "Quantity", "Strike Price",
                      "Cumulative Vested", "Exercised?", "Exercise Date", "FMV at Exercise (Rs.)"],
        column_config={
            "Vest Date": st.column_config.DateColumn("Vest Date"),
            "Exercise Date": st.column_config.DateColumn("Exercise Date"),
            "Strike Price": st.column_config.NumberColumn("Strike Price", format="Rs. %.2f"),
            "FMV at Exercise (Rs.)": st.column_config.NumberColumn("FMV at Exercise", format="Rs. %.2f", min_value=0.0, step=1.0),
            "Quantity": st.column_config.NumberColumn("Quantity", min_value=0, step=1),
            "Cumulative Vested": st.column_config.NumberColumn("Cumulative Vested"),
        },
        disabled=["Grant", "Tranche", "Cumulative Vested"],
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key="schedule_editor",
    )
    st.session_state.schedule_df = edited

    today = pd.Timestamp(date.today())
    edited["Vest Date"] = pd.to_datetime(edited["Vest Date"])
    edited["Status"] = np.where(edited["Vest Date"] <= today, "Vested", "Upcoming")

    vested_qty = int(edited.loc[edited["Status"] == "Vested", "Quantity"].sum())
    upcoming_qty = int(total_shares - vested_qty)
    next_row = edited.loc[edited["Status"] == "Upcoming"].sort_values("Vest Date").head(1)

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Vested so far", f"{vested_qty:,} shares", f"{vested_qty/total_shares*100:.1f}% of grant" if total_shares else "")
    with c2:
        kpi_card("Still vesting", f"{upcoming_qty:,} shares", f"{upcoming_qty/total_shares*100:.1f}% of grant" if total_shares else "")
    with c3:
        if not next_row.empty:
            nd = next_row.iloc[0]["Vest Date"].date()
            kpi_card("Next vesting", nd.strftime("%d %b %Y"), f"{int(next_row.iloc[0]['Quantity']):,} shares in {(nd - date.today()).days} days", accent=True)
        else:
            kpi_card("Next vesting", "—", "All tranches vested")

    grants_list = sorted(edited["Grant"].unique())
    palette = [GOLD, SILVER, BRONZE, GOLD_SOFT, "#8A8A8A", "#E4C98A"]
    fig = go.Figure()
    for i, gname in enumerate(grants_list):
        sub = edited[edited["Grant"] == gname]
        fig.add_bar(x=sub["Tranche"] + " (" + gname + ")", y=sub["Quantity"],
                    marker_color=palette[i % len(palette)], name=gname,
                    opacity=0.92)
    fig.add_trace(go.Scatter(x=edited["Tranche"] + " (" + edited["Grant"] + ")", y=edited["Cumulative Vested"],
                              mode="lines", name="Cumulative vested",
                              line=dict(color=GOLD_SOFT, width=2.5, dash="dot"), yaxis="y2"))
    fig.update_layout(**PLOTLY_LAYOUT, height=400,
                       yaxis=dict(title="Shares per tranche", gridcolor="rgba(255,255,255,0.06)"),
                       yaxis2=dict(title="Cumulative", overlaying="y", side="right", showgrid=False),
                       xaxis=dict(showgrid=False))
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------
# LIVE / MANUAL PRICE
# --------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def fetch_live_price(sym):
    t = yf.Ticker(sym)
    hist = t.history(period="1d", interval="1m")
    if hist.empty:
        hist = t.history(period="5d")
    if hist.empty:
        return None, None
    last_price = float(hist["Close"].dropna().iloc[-1])
    last_ts = hist.index[-1].to_pydatetime()
    return last_price, last_ts


current_price, price_source, price_ts = None, "", None
if is_listed == "Listed" and not manual_price_override and ticker and YFINANCE_AVAILABLE:
    try:
        current_price, price_ts = fetch_live_price(ticker)
        price_source = f"Live · NSE · {ticker}"
    except Exception:
        current_price = None
    if current_price is None:
        st.warning("Couldn't fetch a live price for that ticker — check the symbol, or switch to manual entry in the sidebar.")
        current_price = manual_price or 0.0
        price_source = "Manual (fallback)"
elif is_listed == "Listed" and manual_price_override:
    current_price = manual_price or 0.0
    price_source = "Manual entry"
else:
    current_price = manual_price or 0.0
    price_source = "Illustrative (pre-IPO, unlisted)"

# --------------------------------------------------------------------------
# TAB 2 — VALUE & TAX
# --------------------------------------------------------------------------
with tabs[1]:
    top_l, top_r = st.columns([3, 1])
    with top_l:
        st.subheader("Current value" + (f" — {company_name}" if company_name else ""))
    with top_r:
        st.caption(f"{price_source}" + (f" · updated {price_ts.strftime('%d %b, %H:%M:%S')}" if price_ts else ""))
        if is_listed == "Listed" and not manual_price_override and st.button("Refresh price"):
            st.cache_data.clear()
            st.rerun()

    exercised_mask = edited["Exercised?"] == True
    exercised_qty = int(edited.loc[exercised_mask, "Quantity"].sum())
    not_exercised_vested_qty = vested_qty - exercised_qty

    vested_current_value = vested_qty * current_price
    vested_exercise_cost = float((edited.loc[edited["Status"] == "Vested", "Quantity"] *
                                   edited.loc[edited["Status"] == "Vested", "Strike Price"]).sum())

    perq_gain = float((edited.loc[exercised_mask, "Quantity"] *
                        (edited.loc[exercised_mask, "FMV at Exercise (Rs.)"] - edited.loc[exercised_mask, "Strike Price"])).sum())
    perq_tax_paid_estimate = max(perq_gain, 0) * (slab_map[tax_slab] + cess)

    unexercised_vested_mask = (edited["Status"] == "Vested") & (~exercised_mask)
    perq_gain_if_now = float((edited.loc[unexercised_vested_mask, "Quantity"] *
                               (current_price - edited.loc[unexercised_vested_mask, "Strike Price"])).clip(lower=0).sum())
    perq_tax_if_now = perq_gain_if_now * (slab_map[tax_slab] + cess)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Vested shares", f"{vested_qty:,}", f"of {total_shares:,} granted across {len(st.session_state.grants)} grant(s)")
    with c2:
        kpi_card("Current price / share", inr(current_price, 2), price_source, accent=True)
    with c3:
        kpi_card("Value of vested shares", inr(vested_current_value), "at current price, pre-tax")
    with c4:
        kpi_card("Exercise cost (vested)", inr(vested_exercise_cost), "across applicable strike prices")

    st.write("")
    st.markdown("##### Exercise status")
    e1, e2, e3 = st.columns(3)
    with e1:
        kpi_card("Already exercised", f"{exercised_qty:,} shares", inr(exercise_cost := float((edited.loc[exercised_mask, 'Quantity'] * edited.loc[exercised_mask, 'Strike Price']).sum())) + " paid")
    with e2:
        kpi_card("Vested, not yet exercised", f"{not_exercised_vested_qty:,} shares", inr(float((edited.loc[unexercised_vested_mask, 'Quantity'] * edited.loc[unexercised_vested_mask, 'Strike Price']).sum())) + " to exercise")
    with e3:
        kpi_card("Perquisite tax if exercised today", inr(perq_tax_if_now), f"on notional gain of {inr(perq_gain_if_now)}")

    st.markdown(
        '<div class="section-note">Perquisite tax is triggered on <i>exercise</i> (not vesting), on the spread '
        'between FMV at exercise and the strike price — taxed as salary income at the applicable slab rate. '
        'Capital gains then apply on the spread between sale price and FMV-at-exercise, based on the holding '
        'period from the exercise date (not the vesting or grant date).</div>',
        unsafe_allow_html=True
    )

    if total_shares:
        st.write("")
        st.markdown("##### Holding breakdown")
        donut = go.Figure(data=[go.Pie(
            labels=["Exercised", "Vested, unexercised", "Unvested"],
            values=[exercised_qty, not_exercised_vested_qty, upcoming_qty],
            hole=0.62,
            marker=dict(colors=[GOLD, GOLD_SOFT, "#3A3A3A"], line=dict(color=NAVY_BG, width=2)),
            textinfo="label+percent", textfont=dict(color=TEXT, size=12),
        )])
        donut.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False,
                             annotations=[dict(text=f"{total_shares:,}<br>total", x=0.5, y=0.5,
                                                font=dict(size=16, color=TEXT, family="Fraunces, serif"), showarrow=False)])
        st.plotly_chart(donut, use_container_width=True)

    if exercised_qty > 0:
        st.write("")
        st.markdown("##### Holding period on exercised tranches (for capital gains)")
        ex_df = edited.loc[exercised_mask, ["Grant", "Tranche", "Quantity", "Exercise Date", "FMV at Exercise (Rs.)"]].copy()
        ex_df["Exercise Date"] = pd.to_datetime(ex_df["Exercise Date"])
        ex_df["LTCG eligible from"] = ex_df["Exercise Date"] + pd.DateOffset(years=1)
        ex_df["Holding today (days)"] = (today - ex_df["Exercise Date"]).dt.days
        ex_df["Gain type today"] = np.where(ex_df["Holding today (days)"] >= 365, "LTCG (12.5%)", "STCG (20%)")
        ex_df["Notional gain (Rs.)"] = ex_df["Quantity"] * (current_price - ex_df["FMV at Exercise (Rs.)"])
        st.dataframe(
            ex_df,
            column_config={
                "Exercise Date": st.column_config.DateColumn("Exercise Date"),
                "LTCG eligible from": st.column_config.DateColumn("LTCG eligible from"),
                "Notional gain (Rs.)": st.column_config.NumberColumn("Notional gain", format="Rs. %,.0f"),
            },
            use_container_width=True, hide_index=True,
        )

# --------------------------------------------------------------------------
# TAB 3 — EXIT PLAN
# --------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Suggested exit plan")

    if is_listed == "Listed":
        lockin_end = pd.Timestamp(listing_date) + pd.DateOffset(months=int(lock_in_months))
    else:
        lockin_end = pd.Timestamp(expected_ipo_date) + pd.DateOffset(months=int(lock_in_months))
    days_to_lockin_end = (lockin_end - today).days

    # Exitable = everything that WILL have vested by the time lock-in clears, not just what's vested today.
    exitable_full_qty = int(edited.loc[edited["Vest Date"] <= lockin_end, "Quantity"].sum())

    l1, l2, l3 = st.columns(3)
    with l1:
        kpi_card("Listing status", "Listed" if is_listed == "Listed" else "Pre-IPO",
                  ticker if (is_listed == "Listed" and ticker) else "Awaiting IPO")
    with l2:
        kpi_card("Lock-in ends", lockin_end.strftime("%d %b %Y"),
                  f"in {days_to_lockin_end} days" if days_to_lockin_end > 0 else "Lock-in over — exit is possible now",
                  accent=True)
    with l3:
        kpi_card("Exitable quantity once lock-in clears", f"{exitable_full_qty:,} shares",
                  "shares vested by the lock-in-end date, across all tranches vesting up to then")

    st.write("")
    retain_pct = st.slider("Retain long-term — % of exitable shares you want to keep beyond this plan", 0, 100, 20)
    retain_qty = int(round(exitable_full_qty * retain_pct / 100))
    plan_qty = exitable_full_qty - retain_qty

    r1, r2 = st.columns(2)
    with r1:
        kpi_card("Retained (long-term hold)", f"{retain_qty:,} shares", f"{retain_pct}% held back, outside this exit plan")
    with r2:
        kpi_card("Planned for exit", f"{plan_qty:,} shares", f"{100-retain_pct}% of exitable quantity, staged below")

    st.write("")
    cA, cB = st.columns(2)
    with cA:
        n_legs = st.slider("Spread the exit over how many tranches?", 2, 20, 6)
    with cB:
        spread_months = st.slider("Spread exits over how many months (post lock-in)?", 1, 60, 18)

    if plan_qty > 0 and n_legs > 0:
        base_qty = plan_qty // n_legs
        remainder = plan_qty - base_qty * n_legs
        monthly_rate = (1 + growth_assumption / 100) ** (1 / 12) - 1

        # Build sell pools: exercised lots (FIFO by exercise date -> favors maturing into LTCG),
        # then vested-but-unexercised shares (cashless exercise assumed at time of sale).
        ex_lots = edited.loc[exercised_mask, ["Quantity", "Exercise Date", "FMV at Exercise (Rs.)"]].copy()
        ex_lots["Exercise Date"] = pd.to_datetime(ex_lots["Exercise Date"])
        ex_lots = ex_lots.sort_values("Exercise Date").reset_index(drop=True)
        keep_frac = 1 - retain_pct / 100
        ex_lots["Quantity"] = (ex_lots["Quantity"] * keep_frac).round().astype(int)
        # pool entries: [remaining_qty, exercise_date, fmv]
        exercised_pool = [[int(r["Quantity"]), r["Exercise Date"], float(r["FMV at Exercise (Rs.)"])]
                           for _, r in ex_lots.iterrows()]

        unexercised_qty_total = int(edited.loc[unexercised_vested_mask, "Quantity"].sum())
        unexercised_qty_total = int(round(unexercised_qty_total * keep_frac))
        avg_strike_unexercised = (
            float((edited.loc[unexercised_vested_mask, "Quantity"] * edited.loc[unexercised_vested_mask, "Strike Price"]).sum() /
                  edited.loc[unexercised_vested_mask, "Quantity"].sum())
            if edited.loc[unexercised_vested_mask, "Quantity"].sum() > 0 else 0.0
        )

        plan_rows = []
        remaining_unexercised = unexercised_qty_total
        pool_idx = 0

        for i in range(n_legs):
            leg_date = lockin_end + pd.DateOffset(months=int(round(i * spread_months / max(n_legs - 1, 1))))
            leg_qty = int(base_qty + (remainder if i == n_legs - 1 else 0))
            if leg_qty <= 0:
                continue
            months_out = max((leg_date - today).days / 30.44, 0)
            projected_price = current_price * ((1 + monthly_rate) ** months_out)

            still_needed = leg_qty
            tax_total = 0.0
            treatments = set()

            while still_needed > 0 and pool_idx < len(exercised_pool):
                lot_qty, lot_date, lot_fmv = exercised_pool[pool_idx]
                if lot_qty <= 0:
                    pool_idx += 1
                    continue
                take = min(lot_qty, still_needed)
                exercised_pool[pool_idx][0] -= take
                still_needed -= take
                held_days = (leg_date - lot_date).days
                long_term = held_days >= 365
                rate = 0.125 if long_term else 0.20
                gain = max(take * (projected_price - lot_fmv), 0)
                tax_total += gain * rate
                treatments.add("LTCG" if long_term else "STCG")
                if exercised_pool[pool_idx][0] <= 0:
                    pool_idx += 1

            if still_needed > 0 and remaining_unexercised > 0:
                take = min(still_needed, remaining_unexercised)
                remaining_unexercised -= take
                still_needed -= take
                perq_gain_leg = max(take * (projected_price - avg_strike_unexercised), 0)
                tax_total += perq_gain_leg * (slab_map[tax_slab] + cess)
                treatments.add("Exercise + Sale")

            gross_value = leg_qty * projected_price
            net_value = gross_value - tax_total
            plan_rows.append({
                "Leg": f"Exit {i+1}",
                "Suggested date": leg_date.strftime("%d %b %Y"),
                "Quantity": leg_qty,
                "Est. price/share": round(projected_price, 2),
                "Gross value": round(gross_value),
                "Tax treatment": " + ".join(sorted(treatments)) if treatments else "—",
                "Est. tax": round(tax_total),
                "Est. net proceeds": round(net_value),
            })

        plan_df = pd.DataFrame(plan_rows)
        st.dataframe(
            plan_df,
            column_config={
                "Est. price/share": st.column_config.NumberColumn(format="Rs. %.2f"),
                "Gross value": st.column_config.NumberColumn(format="Rs. %,.0f"),
                "Est. tax": st.column_config.NumberColumn(format="Rs. %,.0f"),
                "Est. net proceeds": st.column_config.NumberColumn(format="Rs. %,.0f"),
                "Quantity": st.column_config.NumberColumn(format="%,d"),
            },
            use_container_width=True, hide_index=True,
        )

        st.markdown(
            '<div class="section-note">Prices beyond today use the flat annual growth assumption set in the '
            'sidebar (0% by default) — treat this as a planning scenario, not a forecast. Already-exercised lots '
            'are sold oldest-first (FIFO) to favour long-term treatment; unexercised shares assume a cashless '
            'exercise at the time of sale, so their tax is shown mainly as perquisite tax. Confirm treatment with '
            'a tax advisor before execution, especially around the Rs. 1.25L annual LTCG exemption and surcharge '
            'on high incomes.</div>',
            unsafe_allow_html=True
        )

        fig2 = go.Figure()
        fig2.add_bar(x=plan_df["Leg"], y=plan_df["Est. net proceeds"], name="Net proceeds",
                     marker_color=GOLD, opacity=0.9)
        fig2.add_bar(x=plan_df["Leg"], y=plan_df["Est. tax"], name="Tax",
                     marker_color=RED, opacity=0.75)
        fig2.update_layout(**PLOTLY_LAYOUT, height=360, barmode="stack",
                            yaxis=dict(title="Rs.", gridcolor="rgba(255,255,255,0.06)"),
                            xaxis=dict(showgrid=False))
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown(f"""
        <div class="section-note">
        In brief: lock-in clears <b>{lockin_end.strftime('%d %b %Y')}</b>. Of the {exitable_full_qty:,} shares
        that will be exitable by then, this plan retains <b>{retain_qty:,}</b> ({retain_pct}%) for the long term
        and stages the remaining <b>{plan_qty:,}</b> across <b>{n_legs}</b> exits over <b>{spread_months}</b>
        months — smoothing price risk and letting later legs season into long-term gains where possible.
        </div>
        """, unsafe_allow_html=True)

        st.session_state["exit_plan_total_net"] = float(plan_df["Est. net proceeds"].sum())
    else:
        st.info("Nothing left to plan an exit for — either no shares will be vested by lock-in end, or 100% is set to be retained above.")
        st.session_state["exit_plan_total_net"] = 0.0

# --------------------------------------------------------------------------
# TAB 4 — DEPLOYMENT PLAN
# --------------------------------------------------------------------------
ASSET_COLORS = {"Equity": GOLD, "Debt": SILVER, "Commodity": BRONZE}
ASSET_PILL = {"Equity": "pill-gold", "Debt": "pill-silver", "Commodity": "pill-bronze"}
CAT_PALETTE = [GOLD, SILVER, BRONZE, GOLD_SOFT, "#8A8A8A", "#E4C98A", "#9C7A4A"]

DEPLOY_CATEGORIES = [
    {"Category": "Liquid",                      "Default %": 3,  "Return Low": 6,  "Return High": 7,  "Asset Class": "Debt"},
    {"Category": "Core Equity",                  "Default %": 33, "Return Low": 12, "Return High": 14, "Asset Class": "Equity"},
    {"Category": "PMS Satellite",                 "Default %": 13, "Return Low": 14, "Return High": 16, "Asset Class": "Equity"},
    {"Category": "Pvt Credit / REIT / InvIT",     "Default %": 17, "Return Low": 11, "Return High": 12, "Asset Class": "Debt"},
    {"Category": "International",                 "Default %": 17, "Return Low": 12, "Return High": 14, "Asset Class": "Equity"},
    {"Category": "Commodities",                    "Default %": 7,  "Return Low": 9,  "Return High": 11, "Asset Class": "Commodity"},
    {"Category": "Private Equity",                 "Default %": 10, "Return Low": 17, "Return High": 19, "Asset Class": "Equity"},
]

with tabs[3]:
    st.subheader("Where the exited money goes")
    st.caption("Defaults to the net proceeds from the Exit Plan tab — adjust as needed, then edit each category's amount below.")

    suggested_corpus_cr = st.session_state.get("exit_plan_total_net", 0.0) / 1e7
    cin1, cin2, cin3 = st.columns([1.2, 1.3, 1])
    with cin1:
        base_corpus_cr = st.number_input("Corpus to split (Rs. Cr)", min_value=0.0,
                                          value=round(suggested_corpus_cr, 2) if suggested_corpus_cr > 0 else 30.0,
                                          step=0.5)
    with cin2:
        st.metric("Suggested corpus (from Exit Plan)", f"Rs. {suggested_corpus_cr:.2f} Cr",
                   help="Net proceeds computed on the Exit Plan tab.")
    with cin3:
        st.write("")
        st.write("")
        reset_clicked = st.button("Reset to default split")

    if "deploy_df" not in st.session_state or reset_clicked:
        rows = []
        for c in DEPLOY_CATEGORIES:
            rows.append({
                "Category": c["Category"],
                "Amount (Rs. Cr)": round(base_corpus_cr * c["Default %"] / 100, 2),
                "Asset Class": c["Asset Class"],
                "Return Low (%)": c["Return Low"],
                "Return High (%)": c["Return High"],
            })
        st.session_state.deploy_df = pd.DataFrame(rows)

    deploy_edited = st.data_editor(
        st.session_state.deploy_df,
        column_config={
            "Amount (Rs. Cr)": st.column_config.NumberColumn("Amount (Rs. Cr)", min_value=0.0, step=0.1, format="%.2f"),
            "Asset Class": st.column_config.TextColumn("Asset Class", disabled=True),
            "Return Low (%)": st.column_config.NumberColumn("Return Low (%)", disabled=True),
            "Return High (%)": st.column_config.NumberColumn("Return High (%)", disabled=True),
        },
        disabled=["Category"],
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key="deploy_editor",
    )
    st.session_state.deploy_df = deploy_edited

    total_corpus_current = float(deploy_edited["Amount (Rs. Cr)"].sum())
    deploy_view = deploy_edited.copy()
    deploy_view["% of Total"] = (deploy_view["Amount (Rs. Cr)"] / total_corpus_current * 100).round(1) if total_corpus_current > 0 else 0

    st.write("")
    t1, t2 = st.columns(2)
    with t1:
        kpi_card("Total deployed", f"Rs. {total_corpus_current:,.2f} Cr", f"across {len(deploy_view)} categories", accent=True)
    with t2:
        weights = deploy_view["Amount (Rs. Cr)"] / total_corpus_current if total_corpus_current > 0 else 0
        blended_low = float((weights * deploy_view["Return Low (%)"]).sum())
        blended_high = float((weights * deploy_view["Return High (%)"]).sum())
        kpi_card("Blended expected return", f"{blended_low:.1f}% - {blended_high:.1f}%", "weighted by amount deployed")

    st.markdown("##### Split summary")
    st.dataframe(
        deploy_view[["Category", "Amount (Rs. Cr)", "% of Total", "Asset Class", "Return Low (%)", "Return High (%)"]],
        column_config={
            "Amount (Rs. Cr)": st.column_config.NumberColumn(format="%.2f"),
            "% of Total": st.column_config.NumberColumn(format="%.1f%%"),
        },
        use_container_width=True, hide_index=True,
    )

    badges = " &nbsp; ".join(
        f'<span class="pill {ASSET_PILL[c["Asset Class"]]}">{c["Category"]} · {c["Asset Class"]}</span>'
        for c in DEPLOY_CATEGORIES
    )
    st.markdown(f'<div style="line-height:2.4;">{badges}</div>', unsafe_allow_html=True)

    st.write("")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("###### Split by category")
        pie1 = go.Figure(data=[go.Pie(
            labels=deploy_view["Category"], values=deploy_view["Amount (Rs. Cr)"], hole=0.55,
            marker=dict(colors=CAT_PALETTE[:len(deploy_view)], line=dict(color=NAVY_BG, width=2)),
            textinfo="label+percent", textfont=dict(color=TEXT, size=11),
        )])
        pie1.update_layout(**PLOTLY_LAYOUT, height=360, showlegend=False)
        st.plotly_chart(pie1, use_container_width=True)
    with p2:
        st.markdown("###### Split by asset class (Debt / Equity / Commodity)")
        asset_summary = deploy_view.groupby("Asset Class")["Amount (Rs. Cr)"].sum().reset_index()
        pie2 = go.Figure(data=[go.Pie(
            labels=asset_summary["Asset Class"], values=asset_summary["Amount (Rs. Cr)"], hole=0.55,
            marker=dict(colors=[ASSET_COLORS[a] for a in asset_summary["Asset Class"]], line=dict(color=NAVY_BG, width=2)),
            textinfo="label+percent", textfont=dict(color=TEXT, size=12),
        )])
        pie2.update_layout(**PLOTLY_LAYOUT, height=360, showlegend=False)
        st.plotly_chart(pie2, use_container_width=True)

    st.write("")
    st.markdown("##### Return profile")
    st.caption("Expected annual return band per category, coloured by asset class.")
    rp = deploy_view.sort_values("Return High (%)")
    fig_rp = go.Figure()
    for _, row in rp.iterrows():
        fig_rp.add_trace(go.Bar(
            x=[row["Return High (%)"] - row["Return Low (%)"]],
            y=[row["Category"]],
            base=[row["Return Low (%)"]],
            orientation="h",
            marker_color=ASSET_COLORS[row["Asset Class"]],
            showlegend=False,
            hovertemplate=f"{row['Category']}: {row['Return Low (%)']}%-{row['Return High (%)']}%<extra></extra>",
        ))
    fig_rp.update_layout(**PLOTLY_LAYOUT, height=340, barmode="overlay",
                          xaxis=dict(title="Expected annual return (%)", gridcolor="rgba(255,255,255,0.06)"),
                          yaxis=dict(showgrid=False))
    st.plotly_chart(fig_rp, use_container_width=True)

    # ---- Private credit / REIT / InvIT monthly income ----
    pc_row = deploy_view[deploy_view["Category"] == "Pvt Credit / REIT / InvIT"]
    if not pc_row.empty and float(pc_row.iloc[0]["Amount (Rs. Cr)"]) > 0:
        st.write("")
        st.markdown("##### Expected monthly income — Private Credit / REIT / InvIT")
        st.caption("Assumes this sleeve pays out its return monthly, net of tax at the slab rate set in the sidebar. "
                   "REIT/InvIT distributions in practice are a mix of interest, dividend and capital-return "
                   "components taxed differently — this is a simplified planning estimate, not a distribution forecast.")

        pc_amount_cr = float(pc_row.iloc[0]["Amount (Rs. Cr)"])
        pc_amount_rs = pc_amount_cr * 1e7
        low, high = float(pc_row.iloc[0]["Return Low (%)"]), float(pc_row.iloc[0]["Return High (%)"])
        mid = (low + high) / 2
        tax_rate = slab_map[tax_slab] + cess

        income_rows = []
        for label, rate in [("Low", low), ("Mid", mid), ("High", high)]:
            annual_gross = pc_amount_rs * rate / 100
            annual_tax = annual_gross * tax_rate
            annual_net = annual_gross - annual_tax
            income_rows.append({
                "Scenario": f"{label} ({rate:.1f}%)",
                "Annual gross income": round(annual_gross),
                "Estimated tax": round(annual_tax),
                "Annual net income": round(annual_net),
                "Monthly net income": round(annual_net / 12),
            })
        income_df = pd.DataFrame(income_rows)

        st.dataframe(
            income_df,
            column_config={
                "Annual gross income": st.column_config.NumberColumn(format="Rs. %,.0f"),
                "Estimated tax": st.column_config.NumberColumn(format="Rs. %,.0f"),
                "Annual net income": st.column_config.NumberColumn(format="Rs. %,.0f"),
                "Monthly net income": st.column_config.NumberColumn(format="Rs. %,.0f"),
            },
            use_container_width=True, hide_index=True,
        )

        fig_pc = go.Figure()
        fig_pc.add_bar(x=income_df["Scenario"], y=income_df["Monthly net income"],
                       marker_color=[ASSET_COLORS["Debt"]] * len(income_df), opacity=0.9)
        fig_pc.update_layout(**PLOTLY_LAYOUT, height=300,
                              yaxis=dict(title="Monthly net income (Rs.)", gridcolor="rgba(255,255,255,0.06)"),
                              xaxis=dict(showgrid=False))
        st.plotly_chart(fig_pc, use_container_width=True)
