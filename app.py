import streamlit as st
import pandas as pd
from io import BytesIO

# --------------------------------------------------
# Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="DCF Valuation Model",
    page_icon="📈",
    layout="wide"
)

st.title("📈 DCF Valuation Model")
st.write("Application de valorisation d'entreprise par la méthode DCF")

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.header("Hypothèses")

revenue0 = st.sidebar.number_input(
    "Chiffre d'affaires Année 0",
    value=1000.0,
    step=100.0
)

growth_defaults = [8.0, 7.0, 6.0, 5.0, 4.0]

growth_rates = []

for i, g in enumerate(growth_defaults, start=1):
    growth = st.sidebar.number_input(
        f"Croissance Année {i} (%)",
        value=g,
        step=0.1
    )
    growth_rates.append(growth / 100)

ebit_margin = st.sidebar.number_input(
    "Marge EBIT (%)",
    value=20.0,
    step=0.1
) / 100

tax_rate = st.sidebar.number_input(
    "Taux d'impôt (%)",
    value=30.0,
    step=0.1
) / 100

# Valeurs conformes au fichier Excel

depreciation_pct = st.sidebar.number_input(
    "Amortissements (% CA)",
    value=3.0,
    step=0.1
) / 100

capex_pct = st.sidebar.number_input(
    "CAPEX (% CA)",
    value=5.0,
    step=0.1
) / 100

bfr_pct = st.sidebar.number_input(
    "BFR (% CA)",
    value=2.0,
    step=0.1
) / 100

terminal_growth = st.sidebar.number_input(
    "Croissance Terminale (%)",
    value=3.0,
    step=0.1
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
    "Prime de risque (%)",
    value=6.0,
    step=0.1
) / 100

cost_debt = st.sidebar.number_input(
    "Coût de la dette (%)",
    value=5.0,
    step=0.1
) / 100

equity_weight = st.sidebar.number_input(
    "Poids Fonds Propres (%)",
    value=70.0,
    step=1.0
) / 100

debt_weight = 1 - equity_weight

# --------------------------------------------------
# WACC
# --------------------------------------------------

cost_equity = risk_free + beta * market_premium

wacc = (
    equity_weight * cost_equity
    + debt_weight * cost_debt * (1 - tax_rate)
)

# --------------------------------------------------
# DCF
# --------------------------------------------------

years = [1, 2, 3, 4, 5]

revenues = []
ebits = []
nopats = []
depreciations = []
capexs = []
bfrs = []
fcffs = []

revenue = revenue0
previous_bfr = revenue0 * bfr_pct

for growth in growth_rates:

    revenue = revenue * (1 + growth)

    ebit = revenue * ebit_margin

    nopat = ebit * (1 - tax_rate)

    depreciation = revenue * depreciation_pct

    capex = revenue * capex_pct

    current_bfr = revenue * bfr_pct

    delta_bfr = current_bfr - previous_bfr

    previous_bfr = current_bfr

    fcff = nopat + depreciation - capex - delta_bfr

    revenues.append(revenue)
    ebits.append(ebit)
    nopats.append(nopat)
    depreciations.append(depreciation)
    capexs.append(capex)
    bfrs.append(delta_bfr)
    fcffs.append(fcff)

# --------------------------------------------------
# Actualisation
# --------------------------------------------------

discount_factors = []
pv_fcff = []

for year, fcff in zip(years, fcffs):

    factor = 1 / ((1 + wacc) ** year)

    discount_factors.append(factor)

    pv_fcff.append(fcff * factor)

sum_pv_fcff = sum(pv_fcff)

# --------------------------------------------------
# Valeur terminale
# --------------------------------------------------

if wacc <= terminal_growth:

    terminal_value = 0.0
    pv_terminal_value = 0.0

else:

    terminal_value = (
        fcffs[-1] * (1 + terminal_growth)
    ) / (wacc - terminal_growth)

    pv_terminal_value = (
        terminal_value /
        ((1 + wacc) ** 5)
    )

enterprise_value = (
    sum_pv_fcff +
    pv_terminal_value
)

# --------------------------------------------------
# DataFrame
# --------------------------------------------------

df = pd.DataFrame({
    "Année": years,
    "CA": revenues,
    "EBIT": ebits,
    "NOPAT": nopats,
    "Amortissements": depreciations,
    "CAPEX": capexs,
    "Variation BFR": bfrs,
    "FCFF": fcffs,
    "Coefficient Actualisation": discount_factors,
    "VA FCFF": pv_fcff
})

# --------------------------------------------------
# AFFICHAGE
# --------------------------------------------------

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
    "Valeur Entreprise",
    f"{enterprise_value:,.2f}"
)

st.subheader("Flux Prévisionnels")

st.dataframe(
    df.round(2),
    use_container_width=True
)

st.subheader("Synthèse DCF")

st.write(
    f"Somme des FCFF actualisés : **{sum_pv_fcff:,.2f}**"
)

st.write(
    f"Valeur Terminale : **{terminal_value:,.2f}**"
)

st.write(
    f"Valeur Terminale Actualisée : **{pv_terminal_value:,.2f}**"
)

st.write(
    f"Valeur Entreprise : **{enterprise_value:,.2f}**"
)

# --------------------------------------------------
# EXPORT EXCEL
# --------------------------------------------------

output = BytesIO()

with pd.ExcelWriter(
        output,
        engine="openpyxl") as writer:

    df.to_excel(
        writer,
        sheet_name="DCF",
        index=False
    )

    resume = pd.DataFrame({
        "Indicateur": [
            "Coût des Fonds Propres",
            "WACC",
            "Somme VA FCFF",
            "Valeur Terminale",
            "VA Valeur Terminale",
            "Valeur Entreprise"
        ],
        "Valeur": [
            cost_equity,
            wacc,
            sum_pv_fcff,
            terminal_value,
            pv_terminal_value,
            enterprise_value
        ]
    })

    resume.to_excel(
        writer,
        sheet_name="Synthese",
        index=False
    )

excel_data = output.getvalue()

st.download_button(
    label="📥 Télécharger Excel",
    data=excel_data,
    file_name="DCF_Resultats.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
