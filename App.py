"""
BelkaFintech | Autonomous Market & Risk Research Prototype
Run: pip install streamlit pandas numpy plotly
     streamlit run belkafintech_app.py

Research/demo prototype only. Not a production banking, investment, or insurance
risk system. Authentication below is a demo gate; deploy behind real SSO/OIDC,
HTTPS, secrets management, and an audited authorization layer.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ---------------------------------------------------------------------
# 1. PAGE / VISUAL SYSTEM
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="BelkaFintech | Autonomous Market Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #0d1117; color: #e6edf3; }
    [data-testid="stSidebar"] { background: #111827; border-right: 1px solid #263244; }
    [data-testid="stMetric"] { background: #151d2b; border: 1px solid #263244;
        padding: 14px; border-radius: 12px; }
    div[data-testid="stForm"] { border: 1px solid #263244; border-radius: 12px; padding: 12px; }
    .hero { padding: 18px 22px; border: 1px solid #263244; border-radius: 14px;
        background: linear-gradient(110deg,#151d2b,#101722); margin-bottom: 14px; }
    .muted { color: #9aa8ba; font-size: 0.88rem; }
    .stButton>button, .stDownloadButton>button { border-radius: 9px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# 2. AUTHENTICATION
# ---------------------------------------------------------------------
# Configure accounts using Streamlit secrets, never hard-code production
# passwords. Example .streamlit/secrets.toml:
# [users.admin]
# password_hash = "<sha256 hash>"
# role = "admin"
# [users.client1]
# password_hash = "<sha256 hash>"
# role = "musteri"
#
# Demo fallback is intentionally disabled unless BELKAFINTECH_DEMO_AUTH=1.
def _demo_users() -> Dict[str, dict]:
    if os.getenv("BELKAFINTECH_DEMO_AUTH", "0") != "1":
        return {}
    # Demo-only accounts. Change/remove before deployment.
    return {
        "Belkafintech": {
            "password_hash": hashlib.sha256(b"Mnvgt19892015").hexdigest(),
            "role": "admin",
        },
        **{
            f"demo_giris{i}": {
                "password_hash": hashlib.sha256(f"demo_sifre_{i}".encode()).hexdigest(),
                "role": "musteri",
            }
            for i in range(1, 101)
        },
    }


def load_users() -> Dict[str, dict]:
    users = _demo_users()
    try:
        configured = st.secrets.get("users", {})
        for username, item in configured.items():
            users[username] = {
                "password_hash": str(item["password_hash"]),
                "role": str(item.get("role", "musteri")),
            }
    except Exception:
        pass
    return users


def verify_login(username: str, password: str) -> Tuple[bool, str]:
    record = load_users().get(username)
    if not record:
        return False, ""
    candidate = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(candidate, record["password_hash"]), record["role"]


def login_screen():
    st.markdown(
        '<div class="hero"><h1>🛡️ BelkaFintech</h1>'
        '<div class="muted">Autonomous Market Engine · Research & Risk Analytics</div></div>',
        unsafe_allow_html=True,
    )
    left, center, right = st.columns([1, 1.2, 1])
    with center:
        with st.form("login_form"):
            st.subheader("Güvenli erişim")
            username = st.text_input("Kullanıcı adı")
            password = st.text_input("Şifre", type="password")
            submitted = st.form_submit_button("Panele giriş", use_container_width=True)
        if submitted:
            ok, role = verify_login(username.strip(), password)
            if ok:
                st.session_state.authenticated = True
                st.session_state.username = username.strip()
                st.session_state.role = role
                st.rerun()
            st.error("Kullanıcı adı veya şifre hatalı.")
        st.caption("Hesaplar Streamlit Secrets üzerinden tanımlanmalıdır.")
    st.stop()


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    login_screen()

# ---------------------------------------------------------------------
# 3. SIDEBAR / ALL ORIGINAL PANEL CONTROLS RETAINED
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🛡️ BELKAFINTECH")
    st.caption("Version 3.2 PRO | Research Prototype")
    st.write(f"**Kullanıcı:** {st.session_state.username}")
    st.write(f"**Rol:** {st.session_state.role}")
    if st.button("Çıkış yap", use_container_width=True):
        for key in ("authenticated", "username", "role"):
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    st.subheader("⚙️ Simülasyon parametreleri")

    currency = st.selectbox("Gösterim para birimi", ["TL", "USD", "EUR", "Belka Coin"])
    currency_symbol = {"TL": "₺", "USD": "$", "EUR": "€", "Belka Coin": "BKC"}[currency]
    st.caption("Para birimi seçimi yalnızca gösterim etiketidir; kur dönüşümü yapılmaz.")

    agent_count = st.slider("Ajan sayısı", 100, 5000, 1000, 100)
    initial_capital = st.number_input("Başlangıç sermayesi ölçeği", 100, 1_000_000, 10_000, 500)
    rounds = st.slider("Simülasyon dönemi", 10, 200, 50, 5)

    policy_rate = st.slider("Politika faizi (%)", 0.0, 50.0, 20.0, 0.5)
    deposit_rate = st.slider("Mevduat faizi (%)", 0.0, 50.0, 15.0, 0.5)
    lending_rate = st.slider("Kredi faizi (%)", 0.0, 80.0, 28.0, 0.5)

    tax_model = st.selectbox(
        "Vergi modeli",
        ["Sabit Vergi", "Artan Oranlı Vergi", "İskandinav Modeli"],
    )
    base_rd_rate = st.slider("Ar-Ge yatırım eğilimi (%)", 0.0, 30.0, 5.0, 0.5)
    fx_allocation = st.slider("Döviz varlık tahsisi (%)", 0.0, 80.0, 20.0, 1.0)
    staking_apy = st.slider("Staking yıllık getirisi (%)", 0.0, 100.0, 8.0, 0.5)
    land_supply = st.slider("Başlangıç arazi arzı", 0, 5000, 500, 25)
    monte_carlo_runs = st.slider("Monte Carlo tekrar sayısı", 1, 100, 10, 1)
    random_seed = st.number_input("Rastgelelik tohumu", 0, 2_147_483_647, 42, 1)

    st.divider()
    st.caption("Parametrelerin tamamı simülasyon motorunda kullanılır.")


# ---------------------------------------------------------------------
# 4. MODEL HELPERS
# ---------------------------------------------------------------------
@dataclass
class ModelConfig:
    agents: int
    periods: int
    capital_scale: float
    policy_rate: float
    deposit_rate: float
    lending_rate: float
    tax_model: str
    rd_rate: float
    fx_allocation: float
    staking_apy: float
    land_supply: int
    seed: int


def gini_coefficient(values: np.ndarray) -> float:
    """Gini over non-negative private net wealth; zero-wealth agents are included."""
    x = np.asarray(values, dtype=float)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    x = np.clip(x, 0.0, None)
    if x.size == 0 or np.sum(x) <= 0:
        return 0.0
    x = np.sort(x)
    n = x.size
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * x) / (n * np.sum(x))) - (n + 1) / n)


def concentration_metrics(wealth: np.ndarray) -> Tuple[float, float, float]:
    x = np.clip(np.nan_to_num(np.asarray(wealth, dtype=float)), 0, None)
    total = float(x.sum())
    if total <= 0:
        return 0.0, 0.0, gini_coefficient(x)
    shares = x / total
    hhi = float(np.sum(shares**2) * 10_000)
    top_n = max(1, int(np.ceil(len(x) * 0.05)))
    top5 = float(np.sort(x)[-top_n:].sum() / total * 100)
    return hhi, top5, gini_coefficient(x)


def tax_rate_for_income(income: np.ndarray, model: str) -> np.ndarray:
    income = np.clip(income, 0, None)
    if model == "Sabit Vergi":
        return np.full_like(income, 0.12, dtype=float)
    if model == "Artan Oranlı Vergi":
        # Marginal brackets are applied to total taxable income.
        tax = (
            np.minimum(income, 2_000) * 0.05
            + np.clip(income - 2_000, 0, 8_000) * 0.12
            + np.clip(income - 10_000, 0, None) * 0.20
        )
        return np.divide(tax, income, out=np.zeros_like(income), where=income > 0)
    # Higher flat effective rate as a stylized high-service-state scenario.
    return np.full_like(income, 0.18, dtype=float)


def safe_divide(a: float, b: float) -> float:
    return float(a / b) if abs(b) > 1e-12 else 0.0


# ---------------------------------------------------------------------
# 5. ECONOMIC SIMULATION ENGINE
# ---------------------------------------------------------------------
def run_simulation(cfg: ModelConfig, run_seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(run_seed)
    n, periods = cfg.agents, cfg.periods

    # Initial private balance sheets. All agents remain in distribution metrics,
    # including agents with zero liquid wealth.
    local_cash = rng.lognormal(mean=np.log(max(cfg.capital_scale, 1)), sigma=0.55, size=n)
    fx_cash = local_cash * (cfg.fx_allocation / max(100 - cfg.fx_allocation, 1))
    fx_cash = np.where(cfg.fx_allocation <= 0, 0.0, fx_cash)
    deposits = np.zeros(n)
    stocks = np.zeros(n)
    staking = np.zeros(n)
    land_units = np.zeros(n, dtype=int)
    debt = np.zeros(n)

    employed = rng.random(n) < 0.92
    treasury = float(local_cash.sum() * 0.05)
    exchange_rate = 1.0
    land_price = max(cfg.capital_scale * 0.25, 1.0)
    remaining_land = int(cfg.land_supply)
    productivity = 1.0
    inflation = 0.03
    trade_balance = 0.0
    previous_price_level = 1.0
    records: List[dict] = []

    for t in range(1, periods + 1):
        # Labour market: employment changes with demand and productivity.
        growth_shock = rng.normal(0, 0.012)
        productivity = max(0.5, productivity * (1 + growth_shock + cfg.rd_rate / 10000))
        hiring_probability = np.clip(0.035 + max(growth_shock, 0) * 1.5, 0.01, 0.08)
        firing_probability = np.clip(0.018 + max(-growth_shock, 0) * 1.8, 0.01, 0.10)
        hire_draw = rng.random(n)
        employed = np.where(employed, hire_draw >= firing_probability, hire_draw < hiring_probability)

        # Income and deposit/staking returns are explicit cash flows.
        wages = employed * (cfg.capital_scale * 0.025 * productivity)
        deposit_interest = deposits * (cfg.deposit_rate / 100 / 12)
        staking_return = staking * (cfg.staking_apy / 100 / 12)
        local_cash += wages + deposit_interest + staking_return

        # Credit: new borrowing creates equal cash and liability; repayment reduces both.
        credit_demand = (local_cash > cfg.capital_scale * 0.8) & (rng.random(n) < 0.025)
        loan_amount = np.where(credit_demand, np.minimum(local_cash * 0.15, cfg.capital_scale * 0.5), 0.0)
        local_cash += loan_amount
        debt += loan_amount
        monthly_loan_rate = cfg.lending_rate / 100 / 12
        interest_due = debt * monthly_loan_rate
        repayment = np.minimum(local_cash * 0.03, debt * 0.04)
        local_cash -= interest_due + repayment
        debt = np.maximum(0, debt + interest_due - repayment)

        # R&D is an actual expenditure that improves productivity over time.
        rd_spend = local_cash * (cfg.rd_rate / 100) * 0.02
        local_cash -= rd_spend

        # Foreign exchange valuation and a simple FX shock/pass-through channel.
        fx_shock = rng.normal(0, 0.008)
        if rng.random() < 0.035:
            fx_shock += rng.choice([-1, 1]) * rng.uniform(0.025, 0.07)
        exchange_rate = max(0.05, exchange_rate * (1 + fx_shock + (cfg.policy_rate - 15) / 10000))
        fx_revaluation = fx_cash * (exchange_rate - 1.0)

        # A simplified production / price-level relationship, not a forecast.
        demand_pressure = safe_divide(float(wages.sum()), float(local_cash.sum() + 1))
        supply_growth = growth_shock + cfg.rd_rate / 10000
        inflation = float(np.clip(
            0.03 + (demand_pressure - 0.025) * 0.35
            + (cfg.policy_rate - 15) / 1000
- supply_growth * 0.25 + rng.normal(0, 0.004),
            -0.02, 0.25
        ))
        price_level = previous_price_level * (1 + inflation)
        previous_price_level = price_level

        # Land market: bids are constrained by cash and actual remaining supply.
        desired_buy = (rng.random(n) < np.clip(0.012 + (cfg.deposit_rate - cfg.policy_rate) / 2000, 0.002, 0.04))
        buyer_ids = np.where(desired_buy & (local_cash >= land_price))[0]
        seller_ids = np.where((land_units > 0) & (rng.random(n) < 0.012))[0]
        buy_count = min(len(buyer_ids), remaining_land)
        executed_buys = 0
        if buy_count > 0:
            chosen_buyers = rng.choice(buyer_ids, size=buy_count, replace=False)
            # Sellers' listed units are matched first; unsold purchases come from initial supply.
            for buyer in chosen_buyers:
                if local_cash[buyer] < land_price:
                    continue
                local_cash[buyer] -= land_price
                land_units[buyer] += 1
                remaining_land = max(0, remaining_land - 1)
                executed_buys += 1
        executed_sells = 0
        if len(seller_ids) > 0:
            for seller in seller_ids:
                if land_units[seller] <= 0:
                    continue
                # A small share of listings find a buyer from the market pool.
                if rng.random() < 0.45:
                    land_units[seller] -= 1
                    local_cash[seller] += land_price * 0.98
                    remaining_land += 1
                    executed_sells += 1

        # Price responds to excess demand/supply and is bounded to avoid explosions.
        excess_demand = executed_buys - executed_sells
        market_depth = max(10, cfg.land_supply * 0.08)
        price_change = np.clip(0.025 * excess_demand / market_depth, -0.08, 0.08)
        land_price = max(1.0, land_price * (1 + price_change))

        # Progressive taxation on earned wages, transferred to public treasury.
        effective_rates = tax_rate_for_income(wages, cfg.tax_model)
        taxes = wages * effective_rates
        local_cash += 0  # explicit: taxes are deducted from wage cash below
        local_cash -= taxes
        tax_revenue = float(taxes.sum())
        treasury += tax_revenue

        # Government spending is a transfer, not newly created system wealth.
        public_spending = min(treasury, treasury * 0.025)
        if public_spending > 0:
            weights = np.maximum(wages, cfg.capital_scale * 0.002)
            weights = weights / weights.sum()
            transfers = public_spending * weights
            local_cash += transfers
            treasury -= public_spending

        # Trade balance is a modeled flow, not an arbitrary huge random shock.
        exports = max(0.0, float(wages.sum()) * (0.04 + max(growth_shock, 0)))
        imports = max(0.0, float(wages.sum()) * (0.035 + cfg.fx_allocation / 5000))
        trade_flow = exports - imports
        trade_balance += trade_flow
        exchange_rate *= max(0.98, min(1.02, 1 - trade_flow / max(float(local_cash.sum()), 1) * 0.03))

        # Private balance sheet: cash + FX + deposits + financial assets + land - debt.
        # Stocks and staking are funded by moving cash, not creating wealth.
        invest_mask = (rng.random(n) < 0.015) & (local_cash > cfg.capital_scale * 0.1)
        invest_amount = np.where(invest_mask, local_cash * 0.02, 0.0)
        local_cash -= invest_amount
        stocks += invest_amount
        stock_return = rng.normal(0.004, 0.025, n)
        stocks = np.maximum(0, stocks * (1 + stock_return))
        stake_mask = (rng.random(n) < 0.01) & (local_cash > cfg.capital_scale * 0.1)
        stake_amount = np.where(stake_mask, local_cash * 0.015, 0.0)
        local_cash -= stake_amount
        staking += stake_amount

        deposits = np.maximum(0, deposits)  # account remains available as a separate balance-sheet bucket
        fx_value = fx_cash * exchange_rate
        land_value = land_units * land_price
        gross_assets = np.maximum(0, local_cash) + fx_value + deposits + stocks + staking + land_value
        net_wealth = gross_assets - debt
        private_positive_wealth = np.clip(net_wealth, 0, None)
        hhi, top5, gini = concentration_metrics(private_positive_wealth)
        total_private_net = float(net_wealth.sum())
        total_system_wealth = total_private_net + treasury
        unemployment = float(1 - employed.mean())
        average_wage = float(wages.mean())
        credit_to_assets = safe_divide(float(debt.sum()), float(gross_assets.sum()))

        records.append({
            "Dönem": t,
            "Toplam Net Servet": total_private_net,
            "Toplam Sistem Serveti": total_system_wealth,
            "Hazine": treasury,
            "Gini": gini,
            "HHI": hhi,
            "En Zengin %5 Payı (%)": top5,
            "İşsizlik (%)": unemployment * 100,
            "Enflasyon (%)": inflation * 100,
            "Politika Faizi (%)": cfg.policy_rate,
            "Mevduat Faizi (%)": cfg.deposit_rate,
            "Kredi Faizi (%)": cfg.lending_rate,
            "Döviz Kuru": exchange_rate,
            "Arazi Fiyatı": land_price,
            "Arazi Arzı": remaining_land,
            "Arazi Alım İşlemi": executed_buys,
            "Arazi Satım İşlemi": executed_sells,
            "Vergi Geliri": tax_revenue,
            "Kamu Harcaması": public_spending,
            "Ticaret Dengesi": trade_balance,
            "Üretkenlik Endeksi": productivity,
            "Ortalama Ücret": average_wage,
            "Kredi / Brüt Varlık (%)": credit_to_assets * 100,
            "Aktif Ajan": int(n),
        })

    return pd.DataFrame(records)


def run_monte_carlo(cfg: ModelConfig, runs: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    simulations = []
    for i in range(runs):
        df = run_simulation(cfg, cfg.seed + i)
        df["Tekrar"] = i + 1
        simulations.append(df)
    combined = pd.concat(simulations, ignore_index=True)
    numeric = combined.groupby("Dönem").mean(numeric_only=True).reset_index()
    dispersion = combined.groupby("Dönem")["Toplam Net Servet"].agg(["mean", "std"]).reset_index()
    dispersion["Alt Bant"] = dispersion["mean"] - dispersion["std"].fillna(0)
    dispersion["Üst Bant"] = dispersion["mean"] + dispersion["std"].fillna(0)
    return numeric, dispersion


# ---------------------------------------------------------------------
# 6. MAIN DASHBOARD
# ---------------------------------------------------------------------
st.markdown(
    '<div class="hero"><h1>🛡️ BelkaFintech</h1>'
    '<div class="muted">Autonomous Market Engine · Agent-Based Economic Simulation · Risk Analytics</div>'
    '</div>',
    unsafe_allow_html=True,
)
st.caption(
    "Araştırma prototipi: sonuçlar model varsayımlarına bağlıdır; yatırım tavsiyesi, "
    "banka sermaye yeterliliği hesabı veya düzenleyici stres testi değildir."
)

cfg = ModelConfig(
    agents=int(agent_count),
    periods=int(rounds),
    capital_scale=float(initial_capital),
    policy_rate=float(policy_rate),
    deposit_rate=float(deposit_rate),
    lending_rate=float(lending_rate),
    tax_model=tax_model,
    rd_rate=float(base_rd_rate),
    fx_allocation=float(fx_allocation),
    staking_apy=float(staking_apy),
    land_supply=int(land_supply),
    seed=int(random_seed),
)

run_col, info_col = st.columns([1, 3])
with run_col:
    run_clicked = st.button("▶ Simülasyonu çalıştır", type="primary", use_container_width=True)
with info_col:
    st.markdown(
        '<div class="muted">Tüm panel parametreleri modele bağlanmıştır. Monte Carlo '
        'tekrarları bağımsız tohumlarla çalıştırılır.</div>',
        unsafe_allow_html=True,
    )

if run_clicked or "simulation_result" not in st.session_state:
    with st.spinner("Ekonomik ajanlar ve senaryolar çalıştırılıyor..."):
        result, mc_dispersion = run_monte_carlo(cfg, int(monte_carlo_runs))
        st.session_state.simulation_result = result
        st.session_state.mc_dispersion = mc_dispersion
        st.session_state.run_config = cfg.__dict__.copy()
        st.session_state.run_count = int(monte_carlo_runs)

df_history = st.session_state.simulation_result.copy()
mc_dispersion = st.session_state.mc_dispersion.copy()
last_row = df_history.iloc[-1]

# KPIs
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Toplam net servet", f"{currency_symbol}{last_row['Toplam Net Servet']:,.0f}")
k2.metric("Gini katsayısı", f"{last_row['Gini']:.3f}")
k3.metric("HHI endeksi", f"{last_row['HHI']:,.0f}")
k4.metric("İşsizlik", f"%{last_row['İşsizlik (%)']:.2f}")
k5.metric("Enflasyon", f"%{last_row['Enflasyon (%)']:.2f}")

# Main navigation preserves the dashboard's breadth without removing any panel.
tabs = st.tabs([
    "📊 Genel Bakış",
    "🌍 Makroekonomi",
    "🏦 Finansal Risk",
    "🏞️ Arazi & Piyasa",
    "🧪 Monte Carlo",
    "📁 Veri & Rapor",
])

with tabs[0]:
    st.subheader("Ekonomik sistem görünümü")
    a, b = st.columns(2)
    with a:
        fig = px.line(df_history, x="Dönem", y=["Toplam Net Servet", "Toplam Sistem Serveti"],
                      title="Servet gelişimi")
        st.plotly_chart(fig, use_container_width=True)
    with b:
        fig = px.line(df_history, x="Dönem", y=["Gini", "HHI"],
                      title="Servet yoğunlaşması")
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_history.tail(10), use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Makroekonomik göstergeler")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.line(df_history, x="Dönem",
                                y=["Enflasyon (%)", "İşsizlik (%)"],
                                title="Enflasyon ve işsizlik"), use_container_width=True)
    with c2:
        st.plotly_chart(px.line(df_history, x="Dönem",
                                y=["Döviz Kuru", "Ticaret Dengesi"],
                                title="Kur ve kümülatif ticaret dengesi"), use_container_width=True)
    st.plotly_chart(px.line(df_history, x="Dönem",
                            y=["Üretkenlik Endeksi", "Ortalama Ücret"],
                            title="Üretkenlik ve ücret"), use_container_width=True)

with tabs[2]:
    st.subheader("Finansal risk göstergeleri")
    r1, r2, r3 = st.columns(3)
    r1.metric("Kredi / Brüt varlık", f"%{last_row['Kredi / Brüt Varlık (%)']:.2f}")
    r2.metric("Kredi faizi", f"%{cfg.lending_rate:.2f}")
    r3.metric("Mevduat faizi", f"%{cfg.deposit_rate:.2f}")
    st.plotly_chart(px.line(df_history, x="Dönem",
                            y=["Kredi / Brüt Varlık (%)", "Hazine"],
                            title="Kredi yoğunluğu ve kamu bilançosu"), use_container_width=True)
    st.info(
        "Bu modül temel bilanço ve kredi göstergeleri sunar. PD, LGD, EAD, ECL, "
        "likidite karşılama oranı ve Basel sermaye hesapları henüz düzenleyici "
        "standartlarda modellenmemektedir."
    )

with tabs[3]:
    st.subheader("Arazi piyasası")
    p1, p2, p3 = st.columns(3)
    p1.metric("Arazi fiyatı", f"{currency_symbol}{last_row['Arazi Fiyatı']:,.2f}")
    p2.metric("Kalan arz", f"{last_row['Arazi Arzı']:,.0f}")
    p3.metric("Son dönem net işlem", f"{last_row['Arazi Alım İşlemi'] - last_row['Arazi Satım İşlemi']:.0f}")
    st.plotly_chart(px.line(df_history, x="Dönem", y="Arazi Fiyatı",
                            title="Arz-talep işlem dengesine göre arazi fiyatı"), use_container_width=True)
    st.plotly_chart(px.bar(df_history, x="Dönem",
                           y=["Arazi Alım İşlemi", "Arazi Satım İşlemi"],
                           title="Alım ve satım işlemleri"), use_container_width=True)

with tabs[4]:
    st.subheader("Monte Carlo senaryo analizi")
    st.write(f"Bağımsız tekrar sayısı: **{st.session_state.run_count}**")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=mc_dispersion["Dönem"], y=mc_dispersion["Üst Bant"],
                             mode="lines", line=dict(width=0), showlegend=False, name="Üst bant"))
    fig.add_trace(go.Scatter(x=mc_dispersion["Dönem"], y=mc_dispersion["Alt Bant"],
                             mode="lines", fill="tonexty", line=dict(width=0),
                             name="±1 standart sapma bandı"))
    fig.add_trace(go.Scatter(x=mc_dispersion["Dönem"], y=mc_dispersion["mean"],
                             mode="lines", name="Ortalama net servet"))
    fig.update_layout(title="Monte Carlo net servet dağılımı", xaxis_title="Dönem",
                      yaxis_title="Net servet")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bant, dönem bazında simülasyon tekrarlarının ortalama ± 1 standart sapmasıdır.")

with tabs[5]:
    st.subheader("Veri dışa aktarma ve raporlama")
    csv = df_history.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ CSV raporunu indir", data=csv,
                       file_name="belkafintech_simulation_report.csv",
                       mime="text/csv", use_container_width=True)
    st.download_button(
        "⬇️ Monte Carlo özetini indir",
        data=mc_dispersion.to_csv(index=False).encode("utf-8-sig"),
        file_name="belkafintech_monte_carlo_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.markdown("**Çalıştırılan parametreler**")
    st.json(st.session_state.run_config)
    st.markdown("**Dönemsel veri seti**")
    st.dataframe(df_history, use_container_width=True, hide_index=True)

st.divider()
st.caption(
    "BelkaFintech Research Prototype · Model çıktıları deneysel niteliktedir. "
    "Kurumsal kullanım öncesinde bağımsız doğrulama, veri yönetişimi, güvenlik "
    "testleri ve alan uzmanı incelemesi gerekir."
)
