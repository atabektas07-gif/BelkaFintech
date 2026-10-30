import streamlit as st
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
# --- SİMÜLASYON MOTORU (Senin Kodun) ---

@dataclass
class SimulationConfig:
    seed: int = 42
    num_agents: int = 20
    periods: int = 30
    initial_land_price: float = 1000.0
    total_land_stock: int = 500
    initial_land_per_owner: int = 2
    initial_treasury: float = 100000.0
    target_treasury: float = 80000.0
    alpha: float = 0.15
    max_price_change_pct: float = 0.30
    initial_cash_scale: float = 15000.0
    minimum_initial_cash: float = 5000.0
    initial_tax_rate: float = 0.05
    min_tax_rate: float = 0.01
    max_tax_rate: float = 0.20
    smoothing_factor: float = 0.25
    max_subsidy_per_period: float = 5000.0
    poverty_threshold: float = 8000.0

    def validate(self):
        if self.num_agents <= 0 or self.periods <= 0:
            raise ValueError("Ajan ve dönem sayısı pozitif olmalıdır.")
        if self.total_land_stock <= 0:
            raise ValueError("Arazi stoku pozitif olmalıdır.")
        if self.initial_land_per_owner < 0:
            raise ValueError("Başlangıç arazi tahsisi negatif olamaz.")
        if not 0 < self.initial_land_price:
            raise ValueError("Arazi fiyatı pozitif olmalıdır.")
        initial_owners = (self.num_agents + 1) // 2
        if (initial_owners * self.initial_land_per_owner) > self.total_land_stock:
            raise ValueError("Başlangıç arazi tahsisi toplam stoku aşıyor.")

class AgentRegistry:
    def __init__(self):
        self.ids = set()
    def register(self, agent_id: int):
        self.ids.add(agent_id)

@dataclass
class Portfolio:
    land_units: int = 0
    purchase_cost: float = 0.0
    assets_value: float = 0.0
    realized_pnl: float = 0.0

class EconomicAgent:
    def __init__(self, agent_id: int, cash: float, risk_tolerance: float, registry: AgentRegistry):
        registry.register(agent_id)
        self.agent_id = agent_id
        self.cash = float(cash)
        self.risk_tolerance = float(risk_tolerance)
        self.portfolio = Portfolio()

    def revalue(self, market_price: float):
        self.portfolio.assets_value = self.portfolio.land_units * market_price

    def decide(self, price: float, expected_roi: float):
        required_roi = 1.0 + (0.20 * (1.0 - self.risk_tolerance))
        if expected_roi >= required_roi:
            return "BUY"
        if expected_roi < (required_roi * 0.80) and self.portfolio.land_units > 0:
            return "SELL"
        return "HOLD"

class LandMarketEngine:
    def __init__(self, initial_price: float, total_land_stock: int, alpha: float, max_change: float):
        self.current_price = float(initial_price)
        self.total_land_stock = total_land_stock
        self.alpha = alpha
        self.max_change = max_change

    def update_price(self, demand: int, supply: int):
        if demand == 0 and supply == 0:
            new_price = self.current_price
        elif demand > 0 and supply == 0:
            new_price = self.current_price * (1 + self.max_change)
        else:
            pressure = (demand - supply) / max(1, supply)
            raw_price = self.current_price * (1 + self.alpha * pressure)
            new_price = np.clip(raw_price, self.current_price * (1 - self.max_change), self.current_price * (1 + self.max_change))
        self.current_price = round(max(1.0, float(new_price)), 4)
        return self.current_price

class DynamicTaxAndBudgetEngine:
    def __init__(self, config: SimulationConfig):
        self.treasury = float(config.initial_treasury)
        self.target = float(config.target_treasury)
        self.tax_rate = config.initial_tax_rate
        self.min_rate = config.min_tax_rate
        self.max_rate = config.max_tax_rate
        self.smoothing = config.smoothing_factor
        self.max_subsidy = config.max_subsidy_per_period

    def optimize_tax_rate(self, recent_volume: int):
        gap = (self.target - self.treasury) / max(1.0, self.target)
        target_rate = 0.05 + 0.12 * gap
        if recent_volume < 4:
            target_rate *= 0.75
        updated = self.tax_rate + self.smoothing * (target_rate - self.tax_rate)
        self.tax_rate = round(float(np.clip(updated, self.min_rate, self.max_rate)), 4)
        return self.tax_rate

    def collect_tax(self, transaction_amount: float):
        tax = transaction_amount * self.tax_rate
        self.treasury += tax
        return tax

    def distribute_subsidies(self, agents, poverty_threshold):
        distributed = 0.0
        if self.treasury > self.target * 0.40:
            for agent in sorted(agents, key=lambda a: a.cash):
                if distributed >= self.max_subsidy or agent.cash >= poverty_threshold:
                    continue
                amount = min(500.0, self.max_subsidy - distributed, self.treasury)
                if amount <= 0:
                    break
                agent.cash += amount
                self.treasury -= amount
                distributed += amount
        return distributed

def execute_atomic_trade(buyer, seller, price, market_price, tax_engine):
    if buyer is seller or seller.portfolio.land_units < 1:
        return False
    tax = price * tax_engine.tax_rate
    if buyer.cash < (price + tax):
        return False
    average_cost = seller.portfolio.purchase_cost / max(1, seller.portfolio.land_units)
    
    buyer.cash -= (price + tax)
    seller.cash += price
    buyer.portfolio.land_units += 1
    buyer.portfolio.purchase_cost += price
    seller.portfolio.land_units -= 1
    seller.portfolio.purchase_cost = max(0.0, seller.portfolio.purchase_cost - average_cost)
    seller.portfolio.realized_pnl += price - average_cost
    
    buyer.revalue(market_price)
    seller.revalue(market_price)
    tax_engine.collect_tax(price)
    return True

def calculate_gini(values):
    values = np.asarray(values, dtype=float)
    if values.size == 0: return 0.0
    values = np.maximum(values, 0.0)
    total = values.sum()
    if total <= 0: return 0.0
    values = np.sort(values)
    n = len(values)
    gini = (2 * np.sum(np.arange(1, n + 1) * values) / (n * total)) - ((n + 1) / n)
    return float(np.clip(gini, 0.0, 1.0))

# --- STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="BelkaFintech Makroekonomik Simülasyon", layout="wide")
st.title("🏛️ BelkaFintech: Dijital Arazi Mülkiyeti & Makro Simülasyon Paneli")

st.sidebar.header("⚙️ Simülasyon Parametreleri")
num_agents = st.sidebar.slider("Ajan Sayısı", 10, 100, 20)
periods = st.sidebar.slider("Dönem Sayısı", 10, 100, 30)
initial_land_price = st.sidebar.number_input("Başlangıç Arazi Fiyatı (TL)", 500.0, 5000.0, 1000.0)
total_land_stock = st.sidebar.number_input("Toplam Arazi Stoku", 100, 2000, 500)
initial_treasury = st.sidebar.number_input("Başlangıç Kamu Hazinesi (TL)", 10000.0, 500000.0, 100000.0)

if st.sidebar.button("🚀 Simülasyonu Başlat"):
    config = SimulationConfig(
        num_agents=num_agents,
        periods=periods,
        initial_land_price=initial_land_price,
        total_land_stock=total_land_stock,
        initial_treasury=initial_treasury
    )
    
    # Simülasyonu Çalıştır
    rng = np.random.default_rng(config.seed)
    registry = AgentRegistry()
    market = LandMarketEngine(config.initial_land_price, config.total_land_stock, config.alpha, config.max_price_change_pct)
    tax_engine = DynamicTaxAndBudgetEngine(config)
    
    agents = []
    for i in range(1, config.num_agents + 1):
        cash = rng.exponential(config.initial_cash_scale) + config.minimum_initial_cash
        risk = rng.uniform(0.1, 0.9)
        agents.append(EconomicAgent(i, float(cash), float(risk), registry))
        
    for idx, agent in enumerate(agents):
        if idx % 2 == 0:
            agent.portfolio.land_units = config.initial_land_per_owner
            agent.portfolio.purchase_cost = config.initial_land_per_owner * config.initial_land_price
            agent.revalue(config.initial_land_price)

    results = {"period": [], "price": [], "treasury": [], "gini": [], "volume": []}
    prev_vol = 5

    for period in range(1, config.periods + 1):
        price = market.current_price
        for agent in agents: agent.revalue(price)
        
        tax_rate = tax_engine.optimize_tax_rate(prev_vol)
        buyers, sellers = [], []
        for agent in agents:
            roi = 1.25 if agent.risk_tolerance > 0.5 else 1.05
            action = agent.decide(price, roi)
            if action == "BUY": buyers.append(agent)
            elif action == "SELL": sellers.append(agent)
            
        desired_demand = len(buyers)
        desired_supply = sum(a.portfolio.land_units for a in sellers)
        
        seller_queue = []
        for s in sellers: seller_queue.extend([s] * s.portfolio.land_units)
        
        executed = 0
        for b in buyers:
            if not seller_queue: break
            if execute_atomic_trade(b, seller_queue.pop(0), price, price, tax_engine):
                executed += 1
                
        tax_engine.distribute_subsidies(agents, config.poverty_threshold)
        new_price = market.update_price(desired_demand, desired_supply)
        for agent in agents: agent.revalue(new_price)
        
        priv_wealth = np.array([a.cash + a.portfolio.assets_value for a in agents])
        gini = calculate_gini(priv_wealth)
        
        results["period"].append(period)
        results["price"].append(new_price)
        results["treasury"].append(tax_engine.treasury)
        results["gini"].append(gini)
        results["volume"].append(executed)
        prev_vol = executed

    df = pd.DataFrame({
        "Dönem": results["period"],
        "Arazi Fiyatı (TL)": results["price"],
        "Kamu Hazinesi (TL)": results["treasury"],
        "Gini Katsayısı": results["gini"],
        "İşlem Hacmi": results["volume"]
    })

    # --- EKRANA ÇIKTI VERME ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Son Arazi Fiyatı", f"{results['price'][-1]:,.2f} TL")
    col2.metric("Son Kamu Hazinesi", f"{results['treasury'][-1]:,.2f} TL")
    col3.metric("Son Gini Katsayısı", f"{results['gini'][-1]:.4f}")
    col4.metric("Toplam İşlem Hacmi", f"{sum(results['volume'])} Adet")

    st.subheader("📈 Gerçek Zamanlı Simülasyon Grafikleri")
    st.line_chart(df.set_index("Dönem")[["Arazi Fiyatı (TL)", "Kamu Hazinesi (TL)"]])

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("⚖️ Gelir Dağılımı (Gini)")
        st.line_chart(df.set_index("Dönem")["Gini Katsayısı"])
    with col_b:
        st.subheader("🔄 Dönemsel İşlem Hacmi")
        st.bar_chart(df.set_index("Dönem")["İşlem Hacmi"])

    st.success("TÜBİTAK Proje Simülasyonu başarıyla tamamlandı!")
else:
    st.info("Sol panelden parametreleri ayarlayıp **'Simülasyonu Başlat'** butonuna basarak projeyi çalıştırabilirsin.")
