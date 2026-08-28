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
BORDER = "rgba(212,175,55,0.16)"

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

    div[data-testid="stTextInputRootElement"], div[data-testid="stTextAreaRootElement"],
    div[data-testid="stNumberInputContainer"], div[data-testid="stDateInputField"],
    div[data-testid="stSelectbox"] > div:last-child {{
        background-color: {CARD_BG} !important; border: 1px solid rgba(212,175,55,0.5) !important; border-radius: 8px !important;
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
    tax_slab_pct = st.number_input("Income-tax slab % (for perquisite tax)", min_value=0.0, max_value=100.0,
                                    value=30.0, step=1.0,
                                    help="Entered directly as the tax rate on perquisite income — no cess is added on top.")
    tax_rate = tax_slab_pct / 100

st.markdown(
    '<div class="section-note">Tax rates used below — LTCG 12.5% beyond a 1-year holding from the exercise date, '
    'STCG 20% within 1 year, Rs. 1.25L LTCG exemption per year, perquisite tax at the slab rate entered in the sidebar on exercise — '
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

tabs = st.tabs(["Vesting Schedule", "Value & Tax", "Exit Plan", "Deployment Plan", "Deployment by Tranche"])

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
    # Quantity and Vest Date are user-editable above; recompute Cumulative Vested from
    # scratch each run (sorted by date) rather than trusting the stored, disabled column —
    # otherwise it silently goes stale the moment someone edits a quantity or a date.
    edited["Vest Date"] = pd.to_datetime(edited["Vest Date"])
    edited = edited.sort_values("Vest Date").reset_index(drop=True)
    edited["Cumulative Vested"] = edited["Quantity"].cumsum()
    st.session_state.schedule_df = edited

    today = pd.Timestamp(date.today())
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

    # Clip each tranche's perquisite gain at zero individually before summing — an underwater
    # tranche (FMV at exercise below strike, e.g. after a down-round) can't generate negative
    # perquisite tax that offsets other tranches' gains; its own contribution is simply zero.
    perq_gain = float((edited.loc[exercised_mask, "Quantity"] *
                        (edited.loc[exercised_mask, "FMV at Exercise (Rs.)"] - edited.loc[exercised_mask, "Strike Price"])
                        ).clip(lower=0).sum())
    perq_tax_paid_estimate = perq_gain * tax_rate

    unexercised_vested_mask = (edited["Status"] == "Vested") & (~exercised_mask)
    perq_gain_if_now = float((edited.loc[unexercised_vested_mask, "Quantity"] *
                               (current_price - edited.loc[unexercised_vested_mask, "Strike Price"])).clip(lower=0).sum())
    perq_tax_if_now = perq_gain_if_now * tax_rate

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
        # Compare against the exact 1-year anniversary date above, not a flat 365-day count —
        # keeps this consistent with "LTCG eligible from" and correct across leap years.
        ex_df["Gain type today"] = np.where(today >= ex_df["LTCG eligible from"], "LTCG (12.5%)", "STCG (20%)")
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

        # Shares that haven't vested yet today but WILL vest by lock-in end are also part of
        # exitable_full_qty (see Tab 3 above) — they must be included here too, or the sell pool
        # runs short of exitable_full_qty and the shortfall silently gets 0% tax applied further down.
        future_vesting_mask = (edited["Vest Date"] > today) & (edited["Vest Date"] <= lockin_end)
        to_exercise_at_sale_mask = unexercised_vested_mask | future_vesting_mask

        unexercised_qty_total = int(edited.loc[to_exercise_at_sale_mask, "Quantity"].sum())
        unexercised_qty_total = int(round(unexercised_qty_total * keep_frac))
        avg_strike_unexercised = (
            float((edited.loc[to_exercise_at_sale_mask, "Quantity"] * edited.loc[to_exercise_at_sale_mask, "Strike Price"]).sum() /
                  edited.loc[to_exercise_at_sale_mask, "Quantity"].sum())
            if edited.loc[to_exercise_at_sale_mask, "Quantity"].sum() > 0 else 0.0
        )

        LTCG_EXEMPTION_PER_FY = 125000.0

        def fy_label(ts):
            """Indian financial year (Apr-Mar) label for a timestamp, e.g. '2025-26'."""
            y = ts.year if ts.month >= 4 else ts.year - 1
            return f"{y}-{str(y + 1)[-2:]}"

        plan_rows = []
        remaining_unexercised = unexercised_qty_total
        pool_idx = 0
        ltcg_exemption_left = {}  # FY label -> exemption still available

        for i in range(n_legs):
            leg_date = lockin_end + pd.DateOffset(months=int(round(i * spread_months / max(n_legs - 1, 1))))
            leg_qty = int(base_qty + (remainder if i == n_legs - 1 else 0))
            if leg_qty <= 0:
                continue
            months_out = max((leg_date - today).days / 30.44, 0)
            projected_price = current_price * ((1 + monthly_rate) ** months_out)

            still_needed = leg_qty
            ltcg_gain_leg = 0.0
            stcg_gain_leg = 0.0
            other_tax_leg = 0.0  # perquisite tax on cashless-exercised-then-sold shares
            treatments = set()

            while still_needed > 0 and pool_idx < len(exercised_pool):
                lot_qty, lot_date, lot_fmv = exercised_pool[pool_idx]
                if lot_qty <= 0:
                    pool_idx += 1
                    continue
                take = min(lot_qty, still_needed)
                exercised_pool[pool_idx][0] -= take
                still_needed -= take
                # Exact 1-year anniversary of the exercise date, consistent with the Value & Tax
                # tab's "LTCG eligible from" — not a flat 365-day count.
                long_term = leg_date >= (lot_date + pd.DateOffset(years=1))
                gain = max(take * (projected_price - lot_fmv), 0)
                if long_term:
                    ltcg_gain_leg += gain
                else:
                    stcg_gain_leg += gain
                treatments.add("LTCG" if long_term else "STCG")
                if exercised_pool[pool_idx][0] <= 0:
                    pool_idx += 1

            if still_needed > 0 and remaining_unexercised > 0:
                take = min(still_needed, remaining_unexercised)
                remaining_unexercised -= take
                still_needed -= take
                perq_gain_leg = max(take * (projected_price - avg_strike_unexercised), 0)
                other_tax_leg += perq_gain_leg * tax_rate
                treatments.add("Exercise + Sale")

            # Rs. 1.25L LTCG exemption, tracked per Indian financial year across all legs —
            # only the portion of this leg's LTCG gain beyond the year's remaining exemption is taxed.
            fy = fy_label(leg_date)
            exemption_left = ltcg_exemption_left.get(fy, LTCG_EXEMPTION_PER_FY)
            exemption_used = min(ltcg_gain_leg, exemption_left)
            ltcg_exemption_left[fy] = exemption_left - exemption_used
            taxable_ltcg = ltcg_gain_leg - exemption_used

            tax_total = taxable_ltcg * 0.125 + stcg_gain_leg * 0.20 + other_tax_leg

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
            'a tax advisor before execution — the Rs. 1.25L annual LTCG exemption is applied per financial year '
            'across these legs, but surcharge on high incomes is not modeled.</div>',
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
        st.session_state["exit_plan_df"] = plan_df.copy()
    else:
        st.info("Nothing left to plan an exit for — either no shares will be vested by lock-in end, or 100% is set to be retained above.")
        st.session_state["exit_plan_total_net"] = 0.0
        st.session_state["exit_plan_df"] = pd.DataFrame()

# --------------------------------------------------------------------------
# TAB 4 — DEPLOYMENT PLAN
# --------------------------------------------------------------------------
ASSET_COLORS = {"Equity": GOLD, "Debt": SILVER, "Commodity": BRONZE}
ASSET_PILL = {"Equity": "pill-gold", "Debt": "pill-silver", "Commodity": "pill-bronze"}
CAT_PALETTE = [GOLD, SILVER, BRONZE, GOLD_SOFT, "#8A8A8A", "#E4C98A", "#9C7A4A"]

DEPLOY_CATEGORIES = [
    {"Category": "Liquid",                      "Default %": 3,  "Return Low": 6,  "Return High": 7,  "Asset Class": "Debt",    "Liquidity": "High"},
    {"Category": "Core Equity",                  "Default %": 33, "Return Low": 12, "Return High": 14, "Asset Class": "Equity",  "Liquidity": "High"},
    {"Category": "PMS Satellite",                 "Default %": 13, "Return Low": 14, "Return High": 16, "Asset Class": "Equity",  "Liquidity": "High"},
    {"Category": "Pvt Credit / REIT / InvIT",     "Default %": 17, "Return Low": 11, "Return High": 12, "Asset Class": "Debt",    "Liquidity": "Low to moderate"},
    {"Category": "International",                 "Default %": 17, "Return Low": 12, "Return High": 14, "Asset Class": "Equity",  "Liquidity": "High"},
    {"Category": "Commodities",                    "Default %": 7,  "Return Low": 9,  "Return High": 11, "Asset Class": "Commodity", "Liquidity": "High"},
    {"Category": "Private Equity",                 "Default %": 10, "Return Low": 17, "Return High": 19, "Asset Class": "Equity",  "Liquidity": "Low"},
]

# Base timing schedule — % of each category's total corpus deployed at t1, t2, t3, t4.
# Front-loaded for liquid, spread across the early legs for equity/intl/commodities,
# mid-loaded for the PMS satellite sleeve, and back-loaded for the less liquid sleeves
# (private credit/REIT/InvIT, private equity) that typically call capital later.
BASE_TRANCHE_SCHEDULE = {
    "Liquid":                      [100, 0, 0, 0],
    "Core Equity":                 [50, 25, 25, 0],
    "PMS Satellite":               [0, 50, 50, 0],
    "Pvt Credit / REIT / InvIT":   [0, 50, 25, 25],
    "International":               [50, 25, 25, 0],
    "Commodities":                 [50, 25, 25, 0],
    "Private Equity":              [0, 0, 50, 50],
}


def stretch_schedule(base_pcts, n_out):
    """Resample a schedule of percentages onto n_out tranches, preserving the total and the
    overall shape. Treats base_pcts as a step function over [0, 1] (each entry an equal-width
    stage) and re-bins it onto n_out equal-width stages by overlapping area — so a 4-stage
    front-loaded schedule stays proportionally front-loaded whether stretched to 2 tranches
    or 8. When n_out equals len(base_pcts), this returns base_pcts unchanged."""
    n_in = len(base_pcts)
    if n_out <= 0 or n_in == 0:
        return []
    out = [0.0] * n_out
    for i in range(n_in):
        in_start, in_end = i / n_in, (i + 1) / n_in
        val = base_pcts[i]
        if val == 0:
            continue
        for j in range(n_out):
            out_start, out_end = j / n_out, (j + 1) / n_out
            overlap = max(0.0, min(in_end, out_end) - max(in_start, out_start))
            if overlap > 0:
                out[j] += val * (overlap / (in_end - in_start))
    return out


def ipf_balance(seed, row_totals, col_totals, iters=200, tol=1e-9):
    """Iterative proportional fitting (RAS / biproportional scaling).

    `seed` is a category x leg matrix built from each category's own timing
    shape (row-normalised). Taken on its own, its row sums equal each
    category's total corpus, but its column sums (money placed in a given
    exit leg, across all categories) generally do NOT equal that leg's net
    proceeds — the timing shapes were set independently per category.

    This repeatedly rescales rows to match `row_totals` (category corpus)
    and columns to match `col_totals` (leg net proceeds) in alternation.
    Column scaling is always applied last, so columns end up matching
    `col_totals` essentially exactly. Row totals match too whenever the
    timing shapes make that feasible (which they do whenever the exit
    legs are reasonably close in size — the normal case); with sharply
    uneven legs and categories that are 0% in some legs, an exact
    row+column match can become mathematically infeasible, and IPF finds
    the closest proportional fit while still hitting column totals exactly.
    A cell that is structurally zero (0% in the schedule) stays zero.
    """
    m = seed.astype(float).copy()
    row_totals = np.asarray(row_totals, dtype=float)
    col_totals = np.asarray(col_totals, dtype=float)
    for _ in range(iters):
        row_sums = m.sum(axis=1)
        rf = np.divide(row_totals, row_sums, out=np.ones_like(row_totals), where=row_sums > 1e-9)
        m = m * rf[:, None]
        col_sums = m.sum(axis=0)
        cf = np.divide(col_totals, col_sums, out=np.ones_like(col_totals), where=col_sums > 1e-9)
        m = m * cf[None, :]
        if (np.abs(m.sum(axis=1) - row_totals).max() < tol
                and np.abs(m.sum(axis=0) - col_totals).max() < tol):
            break
    return m

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
    liquidity_map = {c["Category"]: c["Liquidity"] for c in DEPLOY_CATEGORIES}
    deploy_view["Liquidity"] = deploy_view["Category"].map(liquidity_map)
    st.session_state["deploy_split_pct"] = deploy_view.set_index("Category")["% of Total"].to_dict()
    st.session_state["deploy_amounts_cr"] = deploy_view.set_index("Category")["Amount (Rs. Cr)"].to_dict()

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
        deploy_view[["Category", "Amount (Rs. Cr)", "% of Total", "Asset Class", "Liquidity", "Return Low (%)", "Return High (%)"]],
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

# --------------------------------------------------------------------------
# TAB 5 — DEPLOYMENT BY TRANCHE
# --------------------------------------------------------------------------
with tabs[4]:
    st.subheader("Where each exit tranche's money goes")
    st.caption("Each category has its own timing — some front-loaded, some staged mid-way, some called later. "
               "The schedule below is stretched proportionally from a base t1\u2013t4 pattern to however many exit "
               "legs your Exit Plan actually has, and is fully editable.")

    tranche_plan_df = st.session_state.get("exit_plan_df", pd.DataFrame())
    amounts_cr = st.session_state.get("deploy_amounts_cr", {})

    if tranche_plan_df.empty or not amounts_cr:
        st.info("Set up an exit plan (Exit Plan tab) and a deployment split (Deployment Plan tab) first — "
                "this tab combines the two.")
    else:
        categories = [c["Category"] for c in DEPLOY_CATEGORIES]
        leg_labels = list(tranche_plan_df["Leg"])
        n_out = len(leg_labels)

        schedule_reset = st.button("Reset to suggested schedule")

        shape_key = tuple(leg_labels)
        if ("tranche_schedule_df" not in st.session_state
                or st.session_state.get("tranche_schedule_shape") != shape_key
                or schedule_reset):
            sched_rows = []
            for cat in categories:
                stretched = stretch_schedule(BASE_TRANCHE_SCHEDULE.get(cat, [0] * 4), n_out)
                row = {"Category": cat}
                row.update({leg: round(v, 1) for leg, v in zip(leg_labels, stretched)})
                sched_rows.append(row)
            st.session_state.tranche_schedule_df = pd.DataFrame(sched_rows)
            st.session_state.tranche_schedule_shape = shape_key

        schedule_col_config = {"Category": st.column_config.TextColumn("Category", disabled=True)}
        for leg in leg_labels:
            schedule_col_config[leg] = st.column_config.NumberColumn(f"{leg} (%)", min_value=0.0, max_value=100.0, step=1.0)

        st.caption("% of each category's total corpus deployed at each exit leg — edit any cell.")
        schedule_edited = st.data_editor(
            st.session_state.tranche_schedule_df,
            column_config=schedule_col_config,
            disabled=["Category"],
            num_rows="fixed",
            use_container_width=True,
            hide_index=True,
            key="tranche_schedule_editor",
        )
        st.session_state.tranche_schedule_df = schedule_edited

        row_sums = schedule_edited[leg_labels].sum(axis=1)
        off_rows = schedule_edited.loc[(row_sums - 100).abs() > 0.5, "Category"].tolist()
        if off_rows:
            st.warning("These categories don't add up to 100% across the tranches: " + ", ".join(off_rows))

        # Build a seed matrix from each category's own timing shape — on its own this makes each
        # category's ROW sum to its total corpus, but says nothing about whether a given leg's
        # COLUMN sums to that leg's actual net proceeds (it generally won't — see ipf_balance()).
        # We then biproportionally rescale the seed so columns match leg net proceeds exactly,
        # while keeping row totals matching category corpus wherever the timing shapes allow it.
        cat_totals_rs = np.array([float(amounts_cr.get(cat, 0.0)) * 1e7 for cat in categories])
        leg_totals_rs = tranche_plan_df["Est. net proceeds"].to_numpy(dtype=float)

        total_corpus_rs, total_proceeds_rs = cat_totals_rs.sum(), leg_totals_rs.sum()
        total_gap = abs(total_corpus_rs - total_proceeds_rs)
        if total_gap > max(1000.0, 0.005 * max(total_corpus_rs, total_proceeds_rs, 1.0)):
            st.warning(
                f"Your Deployment Plan corpus (Rs. {total_corpus_rs/1e7:,.2f} Cr) and this Exit Plan's total net "
                f"proceeds (Rs. {total_proceeds_rs/1e7:,.2f} Cr) don't match right now — every leg below will still "
                f"deploy exactly its own net proceeds, but each category's actual total will scale up or down from "
                f"its Deployment Plan figure to make that work. Go to the Deployment Plan tab and hit \"Reset to "
                f"default split\" to resync the two."
            )

        seed = np.zeros((len(categories), n_out))
        uniform_fallback = []
        for ci, cat in enumerate(categories):
            pcts = schedule_edited.loc[schedule_edited["Category"] == cat, leg_labels].iloc[0].to_numpy(dtype=float)
            if pcts.sum() <= 1e-9 and cat_totals_rs[ci] > 0:
                # No timing set at all for a category that has money to place — spread it evenly
                # rather than silently dropping it from every leg.
                pcts = np.full(n_out, 100.0 / n_out)
                uniform_fallback.append(cat)
            seed[ci] = cat_totals_rs[ci] * pcts / 100.0

        if uniform_fallback:
            st.info("No timing set for: " + ", ".join(uniform_fallback) + " — spreading evenly across legs until you set one.")

        if leg_totals_rs.sum() > 0 and cat_totals_rs.sum() > 0:
            balanced = ipf_balance(seed, cat_totals_rs, leg_totals_rs)
        else:
            balanced = seed

        rows = []
        for li in range(n_out):
            leg = tranche_plan_df.iloc[li]
            row = {"Leg": leg["Leg"], "Suggested date": leg["Suggested date"], "Net proceeds": float(leg["Est. net proceeds"])}
            for ci, cat in enumerate(categories):
                row[cat] = float(balanced[ci, li])
            row["Deployed (check)"] = float(balanced[:, li].sum())
            rows.append(row)
        tranche_deploy_df = pd.DataFrame(rows)

        st.write("")
        st.markdown("##### Rs. deployed by category, per tranche")
        st.caption("\"Deployed (check)\" is the sum across categories for that leg — it should match \"Net proceeds\" "
                   "exactly; that's the reconciliation this table is built to guarantee.")
        col_config = {
            "Net proceeds": st.column_config.NumberColumn(format="Rs. %,.0f"),
            "Deployed (check)": st.column_config.NumberColumn(format="Rs. %,.0f"),
        }
        for cat in categories:
            col_config[cat] = st.column_config.NumberColumn(format="Rs. %,.0f")

        st.dataframe(
            tranche_deploy_df,
            column_order=["Leg", "Suggested date", "Net proceeds", "Deployed (check)"] + categories,
            column_config=col_config,
            use_container_width=True, hide_index=True,
        )

        max_leg_diff = float((tranche_deploy_df["Deployed (check)"] - tranche_deploy_df["Net proceeds"]).abs().max())

        totals = tranche_deploy_df[categories].sum()
        t1, t2 = st.columns(2)
        with t1:
            kpi_card("Total net proceeds staged", inr(tranche_deploy_df["Net proceeds"].sum()),
                      f"across {len(tranche_deploy_df)} exit legs", accent=True)
        with t2:
            kpi_card("Total deployed across categories", inr(totals.sum()),
                      f"largest per-leg gap: {inr(max_leg_diff)}" if max_leg_diff >= 1 else "matches exactly, leg by leg")

        cat_check_df = pd.DataFrame({
            "Category": categories,
            "Target corpus (Deployment Plan)": cat_totals_rs,
            "Actually staged (this schedule)": balanced.sum(axis=1),
        })
        cat_check_df["Difference"] = cat_check_df["Actually staged (this schedule)"] - cat_check_df["Target corpus (Deployment Plan)"]
        cat_drift = cat_check_df.loc[cat_check_df["Difference"].abs() > max(1000.0, 0.01 * cat_totals_rs.sum()), "Category"].tolist()
        if cat_drift:
            with st.expander("Some categories' totals shifted to make every leg reconcile — details"):
                st.caption("A category that's 0% in a leg can never receive money that leg, and every leg must still "
                           "fully deploy its net proceeds — when the two constraints can't both be met exactly "
                           "(e.g. very uneven leg sizes), the category's own total shifts slightly instead. Adjust "
                           "the timing schedule above to correct any of these.")
                st.dataframe(
                    cat_check_df,
                    column_config={
                        "Target corpus (Deployment Plan)": st.column_config.NumberColumn(format="Rs. %,.0f"),
                        "Actually staged (this schedule)": st.column_config.NumberColumn(format="Rs. %,.0f"),
                        "Difference": st.column_config.NumberColumn(format="Rs. %,.0f"),
                    },
                    use_container_width=True, hide_index=True,
                )

        st.write("")
        st.markdown("##### Category allocation per tranche")
        fig_tr = go.Figure()
        for i, cat in enumerate(categories):
            fig_tr.add_bar(x=tranche_deploy_df["Leg"], y=tranche_deploy_df[cat], name=cat,
                            marker_color=CAT_PALETTE[i % len(CAT_PALETTE)])
        fig_tr.update_layout(**PLOTLY_LAYOUT, height=400, barmode="stack",
                              yaxis=dict(title="Rs.", gridcolor="rgba(255,255,255,0.06)"),
                              xaxis=dict(showgrid=False))
        st.plotly_chart(fig_tr, use_container_width=True)

        st.markdown(
            '<div class="section-note">Each category\'s total corpus (from the Deployment Plan tab) is staged across '
            'exit legs per the schedule above — rebalanced so every leg\'s category split sums exactly to that leg\'s '
            'net proceeds, not just to the same grand total. Adjust the schedule as your view on timing changes, or '
            'hit "Reset to suggested schedule" to go back to the stretched default.</div>',
            unsafe_allow_html=True
        )
