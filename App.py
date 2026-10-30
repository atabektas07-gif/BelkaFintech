Import streamlit as st
import pandas as pd
import numpy as np

# 1. Sayfa Yapılandırması
st.set_page_config(
    page_title="Belkafintech | Secure Client Portal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Özel Kurumsal CSS Tasarımı
st.markdown("""
    <style>
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .stButton>button {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        font-weight: bold;
        border: none;
        padding: 10px 20px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 100 Kullanıcılı Veritabanı Sistemi
KULLANICILAR = {
    "Belkafintech": {
        "sifre": "Mnvgt19892015",
        "rol": "admin"
    }
}

for i in range(1, 101):
    KULLANICILAR[f"demo_giris{i}"] = {
        "sifre": f"demo_sifre_{i}",
        "rol": "musteri"
    }

if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False
    st.session_state["aktif_kullanici"] = ""
    st.session_state["rol"] = ""

# 4. GİRİŞ EKRANI
if not st.session_state["giris_yapildi"]:
    col_l, col_r = st.columns([1.3, 1])
    
    with col_l:
        try:
            st.image("final_coached_logo.png", width=300)
        except:
            st.markdown("⚡📊📈")
            
        st.markdown("<h2 style='text-align: left; color: white; margin-top: 10px;'>BELKAFINTECH</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: left; color: #a0aec0; margin-top: -15px;'>Ata Çakar</h4>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("""
            **Macroeconomic Simulation Platform**  
            *Version 3.1 PRO | Secure Client Portal*  
            
            👋 Hoş geldiniz! Devam etmek için lütfen giriş yapınız.
        """)

    with col_r:
        st.markdown("### 🔐 Secure Client Portal")
        kullanici_input = st.text_input("Kullanıcı Adı")
        sifre_input = st.text_input("Şifre", type="password")
        
        if st.button("Giriş Yap"):
            if not kullanici_input or not sifre_input:
                st.warning("⚠️ Lütfen alanları doldurun.")
            elif kullanici_input in KULLANICILAR:
                hesap = KULLANICILAR[kullanici_input]
                if hesap["sifre"] == sifre_input:
                    st.session_state["giris_yapildi"] = True
                    st.session_state["aktif_kullanici"] = kullanici_input
                    st.session_state["rol"] = hesap["rol"]
                    st.rerun()
                else:
                    st.error("❌ Hatalı şifre!")
            else:
                st.error("❌ Kullanıcı bulunamadı!")

# 5. GİRİŞ YAPILDIKTAN SONRA Tam Donanımlı Simülasyon Paneli
else:
    c1, c2 = st.columns([4, 1])
    with c1:
        if st.session_state["rol"] == "admin":
            st.success(f"👑 Kurucu Modu Aktif | Hoş geldin {st.session_state['aktif_kullanici']}")
        else:
            st.info(f"👤 Pilot Müşteri Paneli | Hesap: {st.session_state['aktif_kullanici']}")
    with c2:
        if st.button("Çıkış Yap"):
            st.session_state["giris_yapildi"] = False
            st.rerun()
            
    st.markdown("---")

    st.title("🌐 Belkafintech: Ajan Tabanlı Makroekonomik Araştırma Prototipi")
    st.markdown("### *Gelişmiş Dış Ticaret, Kademeli Vergi Modülü & Akademik Görsel Mimarisi*")

    # Session State Tanımlamaları
    if "num_agents" not in st.session_state: st.session_state.num_agents = 50
    if "initial_capital" not in st.session_state: st.session_state.initial_capital = 100000.0
    if "rounds" not in st.session_state: st.session_state.rounds = 30
    if "policy_rate" not in st.session_state: st.session_state.policy_rate = 18.0
    if "deposit_rate" not in st.session_state: st.session_state.deposit_rate = 12.0
    if "lending_rate" not in st.session_state: st.session_state.lending_rate = 24.0

    with st.sidebar:
        st.header("⚙️ Piyasa ve Sistem Ayarları")
        base_currency = st.selectbox("Görüntüleme Para Birimi", ["Türk Lirası (₺)", "Amerikan Doları ($)", "Euro (€)", "Belka Coin (BC)"])
        currency_symbol = {"Türk Lirası (₺)": "₺", "Amerikan Doları ($)": "$", "Euro (€)": "€", "Belka Coin (BC)": "BC"}[base_currency]

        num_agents = st.slider("Ajan Sayısı", 10, 200, st.session_state.num_agents, 10)
        initial_capital = st.number_input(f"Başlangıç Sermayesi Ölçeği ({currency_symbol})", value=float(st.session_state.initial_capital), step=10000.0, min_value=1000.0)
        rounds = st.slider("Simülasyon Tur Sayısı", 10, 100, st.session_state.rounds)

        st.header("🏛️ Merkez Bankası & Maliye")
        policy_rate_val = st.slider("Merkez Bankası Politika Faizi (%)", 0.0, 50.0, st.session_state.policy_rate)
        deposit_rate_val = st.slider("Mevduat Getiri Faizi (%)", 0.0, 50.0, st.session_state.deposit_rate)
        lending_rate_val = st.slider("Ticari Kredi Faiz Oranı (%)", 0.0, 60.0, st.session_state.lending_rate)
        tax_system = st.selectbox("Vergi Mimarisi Modeli", ["Sabit Oranlı Vergi (%5)", "Kademeli Artan Oranlı Vergi (Max %25)", "İskandinav Model"])

        st.header("🚀 Yatırım, Varlık Dönüşümü & Mülkiyet")
        base_rd_rate_val = st.slider("Taban Ar-Ge Eğilimi (%)", 0.0, 15.0, 3.0)
        fx_allocation_val = st.slider("Döviz Varlık Sepeti Oranı (%)", 0.0, 100.0, 35.0)
        staking_apy_val = st.slider("DeFi / Staking Getiri Oranı (APY %)", 0.0, 40.0, 12.0)
        total_virtual_lands = st.slider("Sanal Arsa Arzı (Adet)", 10, 500, 100)
        monte_carlo_runs = st.slider("Monte Carlo Senaryo Tekrar Sayısı", 5, 50, 10, 5)

        st.markdown("---")
        with st.form("simulation_form"):
            submitted = st.form_submit_button("🚀 Simülasyonu Başlat")

        st.markdown("---")
        st.subheader("👑 Proje Künyesi & Mimari")
        st.markdown("**Kurucu & Geliştirici:** Ata Çakar")
        st.markdown("**Proje:** Akademik Makroekonomik Prototip")

    policy_rate = policy_rate_val / 100.0
    deposit_rate = deposit_rate_val / 100.0
    lending_rate = lending_rate_val / 100.0
    base_rd_rate = base_rd_rate_val / 100.0
    fx_allocation = fx_allocation_val / 100.0
    staking_apy = staking_apy_val / 100.0

    def calculate_safe_gini_and_hhi(gross_assets):
        valid_assets = gross_assets[gross_assets > 0]
        if len(valid_assets) == 0 or np.sum(valid_assets) <= 0:
            return np.nan, np.nan, np.nan
        total_sum = np.sum(valid_assets)
        shares = valid_assets / total_sum
        hhi = float(np.sum((shares * 100.0) ** 2))
        top_5_share = float(np.sum(np.sort(shares)[-5:]) * 100.0) if len(shares) >= 5 else 100.0
        array = np.sort(valid_assets)
        n = array.shape[0]
        index = np.arange(1, n + 1)
        gini = float((np.sum((2 * index - n - 1) * array)) / (n * total_sum))
        return hhi, top_5_share, gini

    def run_methodological_prototype(seed_value, num_agents, initial_capital, rounds, policy_rate, deposit_rate, lending_rate, tax_system, base_rd_rate, fx_allocation, staking_apy, total_virtual_lands):
        np.random.seed(seed_value)
        local_wealth = np.random.exponential(scale=initial_capital * (1.0 - fx_allocation), size=num_agents)
        fx_wealth = np.random.exponential(scale=initial_capital * fx_allocation, size=num_agents)
        defi_staking_pool = np.zeros(num_agents)
        stock_portfolio_value = np.zeros(num_agents)
        lands_owned = np.zeros(num_agents, dtype=int)
        active_status = np.ones(num_agents, dtype=bool)
        employment_status = np.ones(num_agents, dtype=bool)
        
        exchange_rate = 1.0
        state_treasury = 10000.0  # Başlangıç devlet kasası rezervi
        land_price = initial_capital * 0.1
        trade_balance_accumulated = 0.0
        credit_principal = np.random.uniform(initial_capital * 0.1, initial_capital * 0.3, size=num_agents)
        unpaid_interest_liability = np.zeros(num_agents)
        
        history = []
        events_log = []

        for r in range(rounds):
            if np.sum(active_status) == 0:
                break

            event_roll = np.random.rand()
            current_event = "Stabil Piyasa Koşulları"
            trade_shock = np.random.normal(0.0, initial_capital * 500.0)

            if event_roll < 0.07:
                current_event = "⚠️ Likidite Krizi & İstihdam Daralması"
                trade_shock = -initial_capital * 2000.0
                events_log.append(f"Tur {r+1}: {current_event}")
            elif event_roll < 0.14:
                current_event = "💱 Kur Şoku ve Dış Ticaret Açığı"
                exchange_rate *= (1.0 + (policy_rate * 0.1))
                trade_shock = -initial_capital * 5000.0
                events_log.append(f"Tur {r+1}: {current_event}")
            elif event_roll < 0.20:
                current_event = "💡 Teknoloji Patlaması ve İhracat Fazlası"
                trade_shock = initial_capital * 4000.0
                events_log.append(f"Tur {r+1}: {current_event}")

            trade_balance_accumulated += trade_shock
            if trade_shock < 0:
                exchange_rate *= 1.02

            local_wealth += defi_staking_pool * (staking_apy / 12.0)
            local_wealth += np.where(employment_status, initial_capital * 0.04, initial_capital * 0.005) * active_status
            local_wealth += local_wealth * (deposit_rate / 12.0)

            # AKTİF VERGİ TOPLAMA VE DEVLET HAZİNESİ AKTARIMI
            gross_assets_pre_tax = local_wealth + (fx_wealth * exchange_rate) + defi_staking_pool + stock_portfolio_value + (lands_owned * land_price)
            if np.any(active_status):
                if "Kademeli" in tax_system:
                    tax_rate = 0.12
                elif "İskandinav" in tax_system:
                    tax_rate = 0.18
                else:
                    tax_rate = 0.05
                
                collected_taxes = np.sum(local_wealth * tax_rate * active_status)
                local_wealth = np.maximum(0, local_wealth * (1.0 - (tax_rate * active_status)))
                state_treasury += collected_taxes  # Devlet rezervi her tur toplanan vergiyle artar!

            # Sanal Arsa İşlemleri
            available_lands = total_virtual_lands - np.sum(lands_owned)
            if available_lands > 0:
                buyers = (local_wealth >= land_price) & active_status
                buyer_indices = np.where(buyers)[0]
                if len(buyer_indices) > 0:
                    lands_to_buy = min(int(available_lands), int(len(buyer_indices)))
                    selected_buyers = np.random.choice(buyer_indices, size=lands_to_buy, replace=False)
                    local_wealth[selected_buyers] -= land_price
                    lands_owned[selected_buyers] += 1
                    land_price *= 1.05

            gross_assets_final = local_wealth + (fx_wealth * exchange_rate) + defi_staking_pool + stock_portfolio_value + (lands_owned * land_price)
            net_wealth_final = gross_assets_final - credit_principal - unpaid_interest_liability
            active_net = net_wealth_final[active_status]

            hhi, top_5_share, gini = calculate_safe_gini_and_hhi(gross_assets_final[active_status])
            unemployment_rate = float(1.0 - (np.sum(employment_status[active_status]) / max(1, np.sum(active_status))))

            history.append({
                "Tur": r + 1,
                "Brüt Varlık Yoğunlaşması HHI": hhi,
                "Top 5 Brüt Varlık Payı (%)": top_5_share,
                "Gini Katsayısı (Brüt Varlıklar)": gini,
                "İşsizlik Oranı (%)": unemployment_rate * 100.0,
                "Model Enflasyon Vekili (%)": float(np.random.uniform(5.0, 20.0) + (policy_rate * 10.0)),
                "Dış Ticaret Dengesi": trade_balance_accumulated,
                "Döviz Kuru": exchange_rate,
                "Devlet Rezervi": state_treasury,
                "Arsa Fiyatı": land_price,
                "Aktif Ajan Sayısı": int(np.sum(active_status)),
                "Toplam Piyasa Net Serveti": float(np.sum(active_net) if len(active_net) > 0 else 0.0)
            })

        return pd.DataFrame(history), events_log

    if submitted:
        df_history, events_log = run_methodological_prototype(
            42, num_agents, initial_capital, rounds, policy_rate, deposit_rate, lending_rate, tax_system, 
            base_rd_rate, fx_allocation, staking_apy, total_virtual_lands
        )

        last_row = df_history.iloc[-1]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Brüt Varlık Yoğunlaşması HHI", f"{last_row['Brüt Varlık Yoğunlaşması HHI']:.1f}" if not np.isnan(last_row['Brüt Varlık Yoğunlaşması HHI']) else "N/A")
        m2.metric("Gini (Brüt Varlıklar)", f"{last_row['Gini Katsayısı (Brüt Varlıklar)']:.3f}" if not np.isnan(last_row['Gini Katsayısı (Brüt Varlıklar)']) else "N/A")
        m3.metric("Toplam Net Servet", f"{currency_symbol}{last_row['Toplam Piyasa Net Serveti']:,.0f}")
        m4.metric("Devlet Rezervi", f"{currency_symbol}{last_row['Devlet Rezervi']:,.0f}")

        st.markdown("---")
        st.subheader("📊 1. Brüt Konsolidasyon & Eşitsizlik Analitiği")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Brüt Varlık Yoğunlaşması HHI & Gini Eğrisi**")
            st.line_chart(df_history.set_index("Tur")[["Brüt Varlık Yoğunlaşması HHI", "Gini Katsayısı (Brüt Varlıklar)"]])
        with col2:
            st.markdown("**Top 5 Brüt Varlık Payı (%) & Aktif Oyuncu Sayısı**")
            st.line_chart(df_history.set_index("Tur")[["Top 5 Brüt Varlık Payı (%)", "Aktif Ajan Sayısı"]])

        st.markdown("---")
        st.subheader("📉 2. Makroekonomik Göstergeler & Dış Ticaret Dengesi")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**Model Enflasyon Vekili (%) & İşsizlik (%)**")
            st.line_chart(df_history.set_index("Tur")[["Model Enflasyon Vekili (%)", "İşsizlik Oranı (%)"]])
        with col4:
            st.markdown("**Dış Ticaret Dengesi & Döviz Kuru**")
            st.line_chart(df_history.set_index("Tur")[["Dış Ticaret Dengesi", "Döviz Kuru"]])

        st.markdown("---")
        st.subheader("📈 3. Arsa Piyasası & Devlet Rezerv Dinamikleri")
        col5, col6 = st.columns(2)
        with col5:
            st.markdown("**Sanal Arsa Fiyatı Trendi**")
            st.line_chart(df_history.set_index("Tur")["Arsa Fiyatı"])
        with col6:
            st.markdown("**Devlet Rezervi Birikimi (Vergi Gelirleri)**")
            st.line_chart(df_history.set_index("Tur")["Devlet Rezervi"])

        if events_log:
            st.subheader("📜 Risk ve Olay Günlüğü")
            for log in events_log:
                st.warning(log)

        st.markdown("---")
        st.download_button(
            label="📥 Akademik Simülasyon Raporunu İndir (CSV)",
            data=df_history.to_csv(index=False).encode('utf-8'),
            file_name="belkafintech_akademik_simulasyon_raporu.csv",
            mime="text/csv",
        )
    else:
        st.info("Simülasyonu başlatmak için sol taraftaki menüden **🚀 Simülasyonu Başlat** butonuna tıklayın.")
