import streamlit as st
import pandas as pd

# ---------------------------------------------------
# Configuration de la page
# ---------------------------------------------------

st.set_page_config(
    page_title="DCF Valuation Model",
    page_icon="📈",
    layout="wide"
)

st.title("📈 DCF Valuation Model")
st.markdown("Application de valorisation d'entreprise par la méthode DCF")

# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------

st.sidebar.header("Hypothèses")

revenue0 = st.sidebar.number_input(
    "Chiffre d'affaires Année 0",
    value=1000.0,
    step=100.0
)

default_growths = [8.0, 7.0, 6.0, 5.0, 4.0]

growth_rates = []

for i, default_growth in enumerate(default_growths, start=1):
    growth = st.sidebar.number_input(
        f"Croissance Année {i} (%)",
        min_value=-100.0,
        max_value=100.0,
        value=default_growth,
        step=0.5,
        format="%.1f"
    )
    growth_rates.append(growth / 100)

ebit_margin = st.sidebar.number_input(
    "Marge EBIT (%)",
    value=20.0,
    step=0.5
) / 100

tax_rate = st.sidebar.number_input(
    "Taux d'impôt (%)",
    value=30.0,
    step=0.5
) / 100

depreciation_pct = st.sidebar.number_input(
    "Amortissements (% CA)",
    value=5.0,
    step=0.5
) / 100

capex_pct = st.sidebar.number_input(
    "CAPEX (% CA)",
    value=8.0,
    step=0.5
) / 100

nwc_pct = st.sidebar.number_input(
    "Variation BFR (% CA)",
    value=2.0,
    step=0.5
) / 100

risk_free = st.sidebar.number_input(
    "Taux sans risque (%)",
    value=3.0,
    step=0.1
) / 100

beta = st.sidebar.number_input(
    "Beta",
    value=1.0,
    step=0.1
)

market_premium = st.sidebar.number_input(
    "Prime de marché (%)",
    value=6.0,
    step=0.1
) / 100

cost_debt = st.sidebar.number_input(
    "Coût de la dette (%)",
    value=5.0,
    step=0.1
) / 100

equity_weight = st.sidebar.slider(
    "Poids Capitaux Propres (%)",
    min_value=0,
    max_value=100,
    value=70
) / 100

debt_weight = 1 - equity_weight

terminal_growth = st.sidebar.number_input(
    "Croissance Terminale (%)",
    value=3.0,
    step=0.1
) / 100

# ---------------------------------------------------
# WACC
# ---------------------------------------------------

cost_equity = risk_free + beta * market_premium

wacc = (
    equity_weight * cost_equity
    + debt_weight * cost_debt * (1 - tax_rate)
)

# ---------------------------------------------------
# Prévisions
# ---------------------------------------------------

years = [1, 2, 3, 4, 5]

revenues = []
ebits = []
nopats = []
fcffs = []

revenue = revenue0

for growth in growth_rates:

    revenue = revenue * (1 + growth)

    ebit = revenue * ebit_margin

    nopat = ebit * (1 - tax_rate)

    depreciation = revenue * depreciation_pct

    capex = revenue * capex_pct

    nwc = revenue * nwc_pct

    fcff = nopat + depreciation - capex - nwc

    revenues.append(revenue)
    ebits.append(ebit)
    nopats.append(nopat)
    fcffs.append(fcff)

# ---------------------------------------------------
# Actualisation
# ---------------------------------------------------

discounted_fcff = []

for year, fcff in zip(years, fcffs):
    discounted_fcff.append(
        fcff / ((1 + wacc) ** year)
    )

# ---------------------------------------------------
# Valeur terminale
# ---------------------------------------------------

if wacc <= terminal_growth:

    terminal_value = 0
    pv_terminal = 0

    st.warning(
        "Le WACC doit être supérieur à la croissance terminale."
    )

else:

    terminal_value = (
        fcffs[-1] * (1 + terminal_growth)
    ) / (wacc - terminal_growth)

    pv_terminal = terminal_value / ((1 + wacc) ** 5)

enterprise_value = (
    sum(discounted_fcff)
    + pv_terminal
)

# ---------------------------------------------------
# Tableau résultats
# ---------------------------------------------------

df = pd.DataFrame({
    "Année": years,
    "CA": revenues,
    "EBIT": ebits,
    "NOPAT": nopats,
    "FCFF": fcffs,
    "FCFF Actualisé": discounted_fcff
})

# ---------------------------------------------------
# Affichage
# ---------------------------------------------------

st.subheader("Résultats")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Coût des Fonds Propres",
        f"{cost_equity:.2%}"
    )

with col2:
    st.metric(
        "WACC",
        f"{wacc:.2%}"
    )

with col3:
    st.metric(
        "Valeur d'Entreprise",
        f"{enterprise_value:,.2f}"
    )

st.subheader("Flux Prévisionnels")

st.dataframe(
    df.style.format({
        "CA": "{:,.2f}",
        "EBIT": "{:,.2f}",
        "NOPAT": "{:,.2f}",
        "FCFF": "{:,.2f}",
        "FCFF Actualisé": "{:,.2f}"
    }),
    use_container_width=True
)

st.subheader("Valeur Terminale")

st.write(
    f"**Valeur Terminale :** {terminal_value:,.2f}"
)

st.write(
    f"**Valeur Terminale Actualisée :** {pv_terminal:,.2f}"
)

st.write(
    f"**Enterprise Value :** {enterprise_value:,.2f}"
)
