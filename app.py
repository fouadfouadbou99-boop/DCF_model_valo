import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="DCF Valuation Model",
    page_icon="📈",
    layout="wide"
)

st.title("📈 DCF Valuation Model")

st.sidebar.header("Hypothèses")

revenue0 = st.sidebar.number_input(
    "Chiffre d'affaires Année 0",
    value=1000.0
)

growth_rates = []

for i in range(1, 6):
    growth = st.sidebar.number_input(
        f"Croissance Année {i} (%)",
        value=max(8 - i + 1, 1),
        step=0.5
    )
    growth_rates.append(growth / 100)

ebit_margin = st.sidebar.number_input(
    "Marge EBIT (%)",
    value=20.0
) / 100

tax_rate = st.sidebar.number_input(
    "Taux d'impôt (%)",
    value=30.0
) / 100

depreciation_pct = st.sidebar.number_input(
    "Amortissements (% CA)",
    value=5.0
) / 100

capex_pct = st.sidebar.number_input(
    "CAPEX (% CA)",
    value=8.0
) / 100

nwc_pct = st.sidebar.number_input(
    "Variation BFR (% CA)",
    value=2.0
) / 100

risk_free = st.sidebar.number_input(
    "Taux sans risque (%)",
    value=3.0
) / 100

beta = st.sidebar.number_input(
    "Beta",
    value=1.0
)

market_premium = st.sidebar.number_input(
    "Prime de marché (%)",
    value=6.0
) / 100

cost_debt = st.sidebar.number_input(
    "Coût de la dette (%)",
    value=5.0
) / 100

equity_weight = st.sidebar.slider(
    "Poids Capitaux Propres (%)",
    0,
    100,
    70
) / 100

debt_weight = 1 - equity_weight

terminal_growth = st.sidebar.number_input(
    "Croissance Terminale (%)",
    value=3.0
) / 100

cost_equity = risk_free + beta * market_premium

wacc = (
    equity_weight * cost_equity
    + debt_weight * cost_debt * (1 - tax_rate)
)

years = [1, 2, 3, 4, 5]
revenues = []
ebits = []
nopats = []
fcffs = []

revenue = revenue0

for growth in growth_rates:
    revenue *= (1 + growth)
    revenues.append(revenue)

    ebit = revenue * ebit_margin
    ebits.append(ebit)

    nopat = ebit * (1 - tax_rate)
    nopats.append(nopat)

    depreciation = revenue * depreciation_pct
    capex = revenue * capex_pct
    nwc = revenue * nwc_pct

    fcff = nopat + depreciation - capex - nwc

    fcffs.append(fcff)

discounted_fcff = [
    fcff / ((1 + wacc) ** year)
    for year, fcff in zip(years, fcffs)
]

terminal_value = (
    fcffs[-1] * (1 + terminal_growth)
) / (wacc - terminal_growth)

pv_terminal = terminal_value / ((1 + wacc) ** 5)

enterprise_value = sum(discounted_fcff) + pv_terminal

df = pd.DataFrame({
    "Année": years,
    "CA": revenues,
    "EBIT": ebits,
    "NOPAT": nopats,
    "FCFF": fcffs,
    "FCFF Actualisé": discounted_fcff
})

st.subheader("Résultats")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Coût des Fonds Propres",
    f"{cost_equity:.2%}"
)

col2.metric(
    "WACC",
    f"{wacc:.2%}"
)

col3.metric(
    "Enterprise Value",
    f"{enterprise_value:,.2f}"
)

st.dataframe(df, use_container_width=True)

st.subheader("Valeur Terminale")

st.write(f"Valeur Terminale : {terminal_value:,.2f}")
st.write(f"Valeur Terminale Actualisée : {pv_terminal:,.2f}")
