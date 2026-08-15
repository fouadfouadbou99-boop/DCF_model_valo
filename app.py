import streamlit as st
import pandas as pd
from io import BytesIO

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="DCF Equity Valuation",
    page_icon="📈",
    layout="wide"
)

st.title("📈 DCF Equity Valuation")
st.markdown("Valorisation des Fonds Propres par la méthode DCF")

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.header("Hypothèses")

revenue0 = st.sidebar.number_input(
    "CA Année 0 (MMAD)",
    value=1000.0
)

growth_defaults = [8.0, 7.0, 6.0, 5.0, 4.0]

growth_rates = []

for i, growth_default in enumerate(growth_defaults, start=1):
    growth = st.sidebar.number_input(
        f"Croissance A{i} (%)",
        value=float(growth_default),
        step=0.1
    )

    growth_rates.append(growth / 100)

ebit_margin = st.sidebar.number_input(
    "Marge EBIT (%)",
    value=20.0
) / 100

tax_rate = st.sidebar.number_input(
    "Taux Impôt (%)",
    value=30.0
) / 100

depreciation_pct = st.sidebar.number_input(
    "Amortissements (% CA)",
    value=3.0
) / 100

capex_pct = st.sidebar.number_input(
    "CAPEX (% CA)",
    value=5.0
) / 100

bfr_pct = st.sidebar.number_input(
    "BFR (% CA)",
    value=2.0
) / 100

terminal_growth = st.sidebar.number_input(
    "Croissance Terminale (%)",
    value=3.0
) / 100

risk_free = st.sidebar.number_input(
    "Taux Sans Risque (%)",
    value=3.0
) / 100

beta = st.sidebar.number_input(
    "Beta",
    value=1.0
)

market_premium = st.sidebar.number_input(
    "Prime de Risque (%)",
    value=6.0
) / 100

cost_debt = st.sidebar.number_input(
    "Coût Dette (%)",
    value=5.0
) / 100

equity_weight = st.sidebar.number_input(
    "Poids Fonds Propres (%)",
    value=70.0
) / 100

debt_weight = 1 - equity_weight

st.sidebar.subheader("Structure Financière")

net_debt = st.sidebar.number_input(
    "Dette nette (MMAD)",
    value=800.0
)

shares_outstanding = st.sidebar.number_input(
    "Nombre d'actions",
    value=1220000
)

# --------------------------------------------------
# WACC
# --------------------------------------------------

cost_equity = risk_free + beta * market_premium

wacc = (
    equity_weight * cost_equity
    + debt_weight * cost_debt * (1 - tax_rate)
)

# --------------------------------------------------
# PROJECTIONS
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
# ACTUALISATION
# --------------------------------------------------

discount_factors = []
pv_fcff = []

for year, fcff in zip(years, fcffs):

    factor = 1 / ((1 + wacc) ** year)

    discount_factors.append(factor)

    pv_fcff.append(fcff * factor)

sum_pv_fcff = sum(pv_fcff)

# --------------------------------------------------
# VALEUR TERMINALE
# --------------------------------------------------

if wacc <= terminal_growth:

    st.error(
        "Le WACC doit être supérieur à la croissance terminale."
    )

    terminal_value = 0
    pv_terminal_value = 0

else:

    terminal_value = (
        fcffs[-1] * (1 + terminal_growth)
    ) / (wacc - terminal_growth)

    pv_terminal_value = (
        terminal_value /
        ((1 + wacc) ** 5)
    )

# --------------------------------------------------
# VALORISATION
# --------------------------------------------------

enterprise_value = (
    sum_pv_fcff +
    pv_terminal_value
)

equity_value = (
    enterprise_value -
    net_debt
)

equity_value_mad = (
    equity_value *
    1000000
)

if shares_outstanding > 0:

    value_per_share = (
        equity_value_mad /
        shares_outstanding
    )

else:

    value_per_share = 0

# --------------------------------------------------
# KPI
# --------------------------------------------------

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Coût Fonds Propres",
    f"{cost_equity:.2%}"
)

col2.metric(
    "WACC",
    f"{wacc:.2%}"
)

col3.metric(
    "Valeur Entreprise",
    f"{enterprise_value:,.2f} MMAD"
)

col4.metric(
    "Valeur Fonds Propres",
    f"{equity_value:,.2f} MMAD"
)

col5.metric(
    "Valeur / Action",
    f"{value_per_share:,.2f} MAD"
)

# --------------------------------------------------
# TABLEAU DCF
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
    "VA FCFF": pv_fcff
})

st.subheader("Flux Prévisionnels")

st.dataframe(
    df.round(2),
    use_container_width=True
)

# --------------------------------------------------
# SYNTHESE
# --------------------------------------------------

st.subheader("Synthèse de Valorisation")

resume = pd.DataFrame(
    {
        "Indicateur": [
            "Valeur Entreprise",
            "Dette Nette",
            "Valeur Fonds Propres",
            "Nombre Actions",
            "Valeur par Action"
        ],
        "Valeur": [
            enterprise_value,
            net_debt,
            equity_value,
            shares_outstanding,
            value_per_share
        ]
    }
)

st.dataframe(
    resume,
    use_container_width=True
)

# --------------------------------------------------
# EXPORT EXCEL
# --------------------------------------------------

output = BytesIO()

with pd.ExcelWriter(
    output,
    engine="openpyxl"
) as writer:

    df.to_excel(
        writer,
        sheet_name="DCF",
        index=False
    )

    resume.to_excel(
        writer,
        sheet_name="Synthese",
        index=False
    )

excel_data = output.getvalue()

st.download_button(
    label="📥 Télécharger Excel",
    data=excel_data,
    file_name="DCF_Equity_Valuation.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
