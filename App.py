import streamlit as st
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Sayfa Yapılandırması
st.set_page_config(
    page_title="BelkaFintech Makroekonomik Simülasyon",
    layout="wide"
)

st.title("🏛️ BelkaFintech: Dijital Arazi Mülkiyeti & Makro Simülasyon")
st.markdown("TÜBİTAK Proje Sunumu ve Algoritmik Vergi Optimizasyon Paneli")


# =========================================================
# 1. CONFIGURATION
# =========================================================

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

        if not 0 <= self.smoothing_factor <= 1:
            raise ValueError("Smoothing factor 0-1 arasında olmalıdır.")

        if not 0 < self.min_tax_rate <= self.max_tax_rate <= 1:
            raise ValueError("Vergi oranı sınırları geçersiz.")

        if not 0 <= self.initial_tax_rate <= 1:
            raise ValueError("Başlangıç vergi oranı geçersiz.")

        if self.max_subsidy_per_period < 0:
            raise ValueError("Sübvansiyon bütçesi negatif olamaz.")

        initial_owners = (self.num_agents + 1) // 2
        initial_land = initial_owners * self.initial_land_per_owner

        if initial_land > self.total_land_stock:
            raise ValueError("Başlangıç arazi tahsisi toplam stoku aşıyor.")


# =========================================================
# 2. AGENT ENGINE
# =========================================================

class AgentRegistry:

    def __init__(self):
        self.ids = set()

    def register(self, agent_id: int):
        if not isinstance(agent_id, int) or isinstance(agent_id, bool):
            raise ValueError("Ajan ID tam sayı olmalıdır.")

        if agent_id <= 0:
            raise ValueError("Ajan ID pozitif olmalıdır.")

        if agent_id in self.ids:
            raise ValueError("Tekrarlanan ajan ID.")

        self.ids.add(agent_id)


@dataclass
class Portfolio:
    land_units: int = 0
    purchase_cost: float = 0.0
    assets_value: float = 0.0
    realized_pnl: float = 0.0


class EconomicAgent:

    def __init__(
        self,
        agent_id: int,
        cash: float,
        risk_tolerance: float,
        registry: AgentRegistry
    ):

        if not np.isfinite(cash) or cash < 0:
            raise ValueError("Nakit bakiyesi geçersiz.")

        if not np.isfinite(risk_tolerance):
            raise ValueError("Risk toleransı geçersiz.")

        if not 0 <= risk_tolerance <= 1:
            raise ValueError("Risk toleransı 0-1 arasında olmalıdır.")

        registry.register(agent_id)

        self.agent_id = agent_id
        self.cash = float(cash)
        self.risk_tolerance = float(risk_tolerance)
        self.portfolio = Portfolio()

    def revalue(self, market_price: float):

        if not np.isfinite(market_price) or market_price <= 0:
            raise ValueError("Piyasa fiyatı geçersiz.")

        self.portfolio.assets_value = (
            self.portfolio.land_units * market_price
        )

    def decide(self, price: float, expected_roi: float):

        required_roi = 1.0 + (
            0.20 * (1.0 - self.risk_tolerance)
        )

        if expected_roi >= required_roi:
            return "BUY"

        sell_threshold = required_roi * 0.80

        if (
            expected_roi < sell_threshold
            and self.portfolio.land_units > 0
        ):
            return "SELL"

        return "HOLD"


# =========================================================
# 3. LAND MARKET ENGINE
# =========================================================

class LandMarketEngine:

    def __init__(
        self,
        initial_price: float,
        total_land_stock: int,
        alpha: float,
        max_change: float
    ):

        if not np.isfinite(initial_price) or initial_price <= 0:
            raise ValueError("Başlangıç fiyatı geçersiz.")

        if total_land_stock <= 0:
            raise ValueError("Arazi stoku pozitif olmalıdır.")

        if not np.isfinite(alpha) or alpha < 0:
            raise ValueError("Alpha geçersiz.")

        if not np.isfinite(max_change) or not 0 < max_change <= 1:
            raise ValueError("Fiyat değişim sınırı geçersiz.")

        self.current_price = float(initial_price)
        self.total_land_stock = total_land_stock
        self.alpha = alpha
        self.max_change = max_change

        self.price_history = [self.current_price]
        self.demand_history = []
        self.supply_history = []

    def update_price(self, demand: int, supply: int):

        if demand < 0 or supply < 0:
            raise ValueError("Talep ve arz negatif olamaz.")

        if supply > self.total_land_stock:
            raise ValueError("Arz toplam arazi stokunu aşıyor.")

        if demand == 0 and supply == 0:
            new_price = self.current_price

        elif demand > 0 and supply == 0:
            new_price = self.current_price * (
                1 + self.max_change
            )

        else:
            pressure = (demand - supply) / max(1, supply)

            raw_price = self.current_price * (
                1 + self.alpha * pressure
            )

            lower = self.current_price * (1 - self.max_change)
            upper = self.current_price * (1 + self.max_change)

            new_price = np.clip(raw_price, lower, upper)

        if not np.isfinite(new_price):
            raise RuntimeError("Piyasa fiyatı sayısal olarak geçersiz.")

        self.current_price = round(max(1.0, float(new_price)), 4)

        self.demand_history.append(demand)
        self.supply_history.append(supply)
        self.price_history.append(self.current_price)

        return self.current_price


# =========================================================
# 4. TAX AND PUBLIC BUDGET ENGINE
# =========================================================

class DynamicTaxAndBudgetEngine:

    def __init__(self, config: SimulationConfig):

        self.treasury = float(config.initial_treasury)
        self.target = float(config.target_treasury)

        self.tax_rate = config.initial_tax_rate
        self.min_rate = config.min_tax_rate
        self.max_rate = config.max_tax_rate

        self.smoothing = config.smoothing_factor
        self.max_subsidy = config.max_subsidy_per_period

        self.budget_history = [self.treasury]
        self.tax_history = [self.tax_rate]
        self.revenue_history = []
        self.subsidy_history = []

    def optimize_tax_rate(self, recent_volume: int):

        if recent_volume < 0:
            raise ValueError("İşlem hacmi negatif olamaz.")

        gap = (self.target - self.treasury) / max(1.0, self.target)

        target_rate = 0.05 + 0.12 * gap

        if recent_volume < 4:
            target_rate *= 0.75

        updated = self.tax_rate + self.smoothing * (
            target_rate - self.tax_rate
        )

        self.tax_rate = round(
            float(np.clip(updated, self.min_rate, self.max_rate)),
            4
        )

        self.tax_history.append(self.tax_rate)

        return self.tax_rate

    def collect_tax(self, transaction_amount: float):

        tax = transaction_amount * self.tax_rate

        if not np.isfinite(tax) or tax < 0:
            raise ValueError("Vergi tutarı geçersiz.")

        self.treasury += tax
        self.revenue_history.append(tax)

        return tax

    def distribute_subsidies(
        self,
        agents: List[EconomicAgent],
        poverty_threshold: float
    ):

        distributed = 0.0

        if self.treasury > self.target * 0.40:

            for agent in sorted(agents, key=lambda a: a.cash):

                if distributed >= self.max_subsidy:
                    break

                if agent.cash >= poverty_threshold:
                    continue

                amount = min(
                    500.0,
                    self.max_subsidy - distributed,
                    self.treasury
                )

                if amount <= 0:
                    break

                agent.cash += amount
                self.treasury -= amount
                distributed += amount

        self.budget_history.append(self.treasury)
        self.subsidy_history.append(distributed)

        return distributed


# =========================================================
# 5. ATOMIC TRANSACTION ENGINE
# =========================================================

def execute_atomic_trade(
    buyer: EconomicAgent,
    seller: EconomicAgent,
    price: float,
    market_price: float,
    tax_engine: DynamicTaxAndBudgetEngine
):

    if buyer is seller:
        return False

    if price <= 0 or not np.isfinite(price):
        return False

    if seller.portfolio.land_units < 1:
        return False

    tax = price * tax_engine.tax_rate
    total_cost = price + tax

    if buyer.cash < total_cost:
        return False

    units = seller.portfolio.land_units

    if units <= 0:
        return False

    average_cost = seller.portfolio.purchase_cost / units

    buyer.cash -= total_cost
    seller.cash += price

    buyer.portfolio.land_units += 1
    buyer.portfolio.purchase_cost += price

    seller.portfolio.land_units -= 1
    seller.portfolio.purchase_cost -= average_cost

    seller.portfolio.purchase_cost = max(
        0.0, seller.portfolio.purchase_cost
    )

    seller.portfolio.realized_pnl += price - average_cost

    buyer.revalue(market_price)
    seller.revalue(market_price)

    tax_engine.collect_tax(price)

    return True


# =========================================================
# 6. ECONOMIC INDICATORS
# =========================================================

def calculate_gini(values):

    values = np.asarray(values, dtype=float)

    if values.size == 0:
        return 0.0

    values = np.maximum(values, 0.0)
    total = values.sum()

    if total <= 0:
        return 0.0

    values = np.sort(values)
    n = len(values)

    indexes = np.arange(1, n + 1)

    gini = (
        2 * np.sum(indexes * values) / (n * total)
        - (n + 1) / n
    )

    return float(np.clip(gini, 0.0, 1.0))


def calculate_wealth(agents, treasury):

    private_wealth = np.array([
        agent.cash + agent.portfolio.assets_value
        for agent in agents
    ])

    public_wealth = float(treasury)

    return private_wealth, public_wealth


# =========================================================
# 7. MAIN SIMULATION ENGINE
# =========================================================

class BelkaFintechSimulation:

    def __init__(self, config: SimulationConfig):

        config.validate()

        self.config = config
        self.rng = np.random.default_rng(config.seed)

        self.registry = AgentRegistry()

        self.market = LandMarketEngine(
            initial_price=config.initial_land_price,
            total_land_stock=config.total_land_stock,
            alpha=config.alpha,
            max_change=config.max_price_change_pct
        )

        self.tax_engine = DynamicTaxAndBudgetEngine(config)

        self.agents = []

        self.results = {
            "period": [],
            "price": [],
            "demand": [],
            "supply": [],
            "executed_volume": [],
            "tax_rate": [],
            "treasury": [],
            "private_wealth": [],
            "total_system_wealth": [],
            "gini": [],
            "subsidies": []
        }

        self.initialize_agents()

    def initialize_agents(self):

        for i in range(1, self.config.num_agents + 1):

            cash = (
                self.rng.exponential(
                    self.config.initial_cash_scale
                )
                + self.config.minimum_initial_cash
            )

            risk = self.rng.uniform(0.1, 0.9)

            agent = EconomicAgent(
                agent_id=i,
                cash=float(cash),
                risk_tolerance=float(risk),
                registry=self.registry
            )

            self.agents.append(agent)

        for index, agent in enumerate(self.agents):

            if index % 2 == 0:
                units = self.config.initial_land_per_owner

                agent.portfolio.land_units = units
                agent.portfolio.purchase_cost = (
                    units * self.config.initial_land_price
                )

                agent.revalue(self.config.initial_land_price)

    def run_period(self, period: int):

        price = self.market.current_price

        for agent in self.agents:
            agent.revalue(price)

        previous_volume = (
            self.results["executed_volume"][-1]
            if self.results["executed_volume"]
            else 5
        )

        tax_rate = self.tax_engine.optimize_tax_rate(
            previous_volume
        )

        buyers = []
        sellers = []

        for agent in self.agents:

            expected_roi = (
                1.25 if agent.risk_tolerance > 0.5
                else 1.05
            )

            action = agent.decide(price, expected_roi)

            if action == "BUY":
                buyers.append(agent)

            elif action == "SELL":
                sellers.append(agent)

        desired_demand = len(buyers)

        desired_supply = sum(
            agent.portfolio.land_units
            for agent in sellers
        )

        if desired_supply > self.market.total_land_stock:
            raise RuntimeError("Piyasaya sunulan arz stok sınırını aştı.")

        seller_queue = []

        for seller in sellers:
            seller_queue.extend(
                [seller] * seller.portfolio.land_units
            )

        executed = 0

        for buyer in buyers:

            if not seller_queue:
                break

            seller = seller_queue.pop(0)

            success = execute_atomic_trade(
                buyer=buyer,
                seller=seller,
                price=price,
                market_price=price,
                tax_engine=self.tax_engine
            )

            if success:
                executed += 1

        subsidy = self.tax_engine.distribute_subsidies(
            self.agents,
            self.config.poverty_threshold
        )

        new_price = self.market.update_price(
            desired_demand,
            desired_supply
        )

        for agent in self.agents:
            agent.revalue(new_price)

        private_wealth, public_wealth = calculate_wealth(
            self.agents,
            self.tax_engine.treasury
        )

        gini = calculate_gini(private_wealth)

        total_system_wealth = (
            private_wealth.sum() + public_wealth
        )

        self.results["period"].append(period)
        self.results["price"].append(new_price)
        self.results["demand"].append(desired_demand)
        self.results["supply"].append(desired_supply)
        self.results["executed_volume"].append(executed)
        self.results["tax_rate"].append(tax_rate)
        self.results["treasury"].append(public_wealth)
        self.results["private_wealth"].append(
            float(private_wealth.sum())
        )
        self.results["total_system_wealth"].append(
            float(total_system_wealth)
        )
        self.results["gini"].append(gini)
        self.results["subsidies"].append(subsidy)

    def run(self):
        for period in range(1, self.config.periods + 1):
            self.run_period(period)
        return self.results


# =========================================================
# 8. STREAMLIT UI INTEGRATION
# =========================================================

st.sidebar.header("⚙️ Simülasyon Parametreleri")

num_agents = st.sidebar.slider("Ajan Sayısı", 10, 100, 20)
periods = st.sidebar.slider("Dönem Sayısı", 10, 100, 30)
initial_land_price = st.sidebar.number_input("Başlangıç Arazi Fiyatı (TL)", 500.0, 5000.0, 1000.0)
total_land_stock = st.sidebar.number_input("Toplam Arazi Stoku", 100, 2000, 500)
initial_treasury = st.sidebar.number_input("Başlangıç Kamu Hazinesi (TL)", 10000.0, 500000.0, 100000.0)
target_treasury = st.sidebar.number_input("Hedef Hazine (TL)", 10000.0, 300000.0, 80000.0)

if st.sidebar.button("🚀 Simülasyonu Başlat"):
    
    config = SimulationConfig(
        seed=42,
        num_agents=num_agents,
        periods=periods,
        initial_land_price=initial_land_price,
        total_land_stock=int(total_land_stock),
        initial_treasury=initial_treasury,
        target_treasury=target_treasury
    )
    
    simulation = BelkaFintechSimulation(config)
    results = simulation.run()

    df = pd.DataFrame({
        "Dönem": results["period"],
        "Arazi Fiyatı (TL)": results["price"],
        "Kamu Hazinesi (TL)": results["treasury"],
        "Gini Katsayısı": results["gini"],
        "İşlem Hacmi": results["executed_volume"],
        "Vergi Oranı": results["tax_rate"]
    })

    # --- METRİKLER ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Son Arazi Fiyatı", f"{results['price'][-1]:,.2f} TL", f"{((results['price'][-1]/initial_land_price)-1)*100:.1f}%")
    col2.metric("Son Kamu Hazinesi", f"{results['treasury'][-1]:,.2f} TL")
    col3.metric("Son Gini Katsayısı", f"{results['gini'][-1]:.4f}")
    col4.netric_vol = sum(results['executed_volume']) if hasattr(st, 'netric_vol') else None
    col4.metric("Toplam İşlem", f"{sum(results['executed_volume'])} Adet")

    # --- GRAFİKLER ---
    st.subheader("📈 Fiyat ve Kamu Hazinesi Dinamikleri")
    st.line_chart(df.set_index("Dönem")[["Arazi Fiyatı (TL)", "Kamu Hazinesi (TL)"]])

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("⚖️ Gelir Dağılımı Adaleti (Gini)")
        st.line_chart(df.set_index("Dönem")["Gini Katsayısı"])
    with col_b:
        st.subheader("🔄 Dönemsel İşlem Hacmi")
        st.bar_chart(df.set_index("Dönem")["İşlem Hacmi"])

    st.success("TÜBİTAK Proje Simülasyonu başarıyla tamamlandı ve tüm motor entegre edildi!")
else:
    st.info("Sol panelden ayarları yapılandırıp **'Simülasyonu Başlat'** butonuna tıkla.")
