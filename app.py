import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# ==========================================================
# CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="DCF Valuation Tool",
    layout="wide"
)

st.title("DCF Valuation Tool")

# ==========================================================
# SIDEBAR
# ==========================================================

st.sidebar.header("Hypothèses de valorisation")

risk_free = st.sidebar.number_input(
    "Taux sans risque (%)",
    value=3.53,
    step=0.1
) / 100

market_premium = st.sidebar.number_input(
    "Prime de marché (%)",
    value=6.07,
    step=0.1
) / 100

specific_risk = st.sidebar.number_input(
    "Prime de risque spécifique (%)",
    value=1.50,
    step=0.1
) / 100

tax_rate = st.sidebar.number_input(
    "Taux d'impôt (%)",
    value=35.0,
    step=1.0
) / 100

beta_unlevered = st.sidebar.number_input(
    "Beta désendetté",
    value=0.90,
    step=0.01
)

debt = st.sidebar.number_input(
    "Dette nette",
    value=100.0,
    step=10.0
)

equity = st.sidebar.number_input(
    "Valeur de marché des fonds propres",
    value=500.0,
    step=50.0
)

cost_debt = st.sidebar.number_input(
    "Coût de la dette (%)",
    value=6.0,
    step=0.1
) / 100

g = st.sidebar.number_input(
    "Croissance à l'infini (%)",
    value=2.0,
    step=0.1
) / 100

shares = st.sidebar.number_input(
    "Nombre d'actions",
    value=10.0,
    step=1.0
)

# ==========================================================
# BETA ENDETTE
# ==========================================================

if equity > 0:
    beta_levered = beta_unlevered * (
        1 + (1 - tax_rate) * (debt / equity)
    )
else:
    beta_levered = beta_unlevered

# ==========================================================
# COST OF EQUITY
# ==========================================================

cost_equity = (
    risk_free
    + beta_levered * market_premium
    + specific_risk
)

# ==========================================================
# WACC
# ==========================================================

capital = debt + equity

if capital > 0:
    weight_debt = debt / capital
    weight_equity = equity / capital
else:
    weight_debt = 0
    weight_equity = 1

wacc = (
    weight_equity * cost_equity
    + weight_debt * cost_debt * (1 - tax_rate)
)

# ==========================================================
# METRICS
# ==========================================================

st.subheader("Paramètres financiers")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Beta endetté",
        f"{beta_levered:.3f}"
    )

with col2:
    st.metric(
        "Coût des fonds propres",
        f"{cost_equity*100:.2f}%"
    )

with col3:
    st.metric(
        "WACC",
        f"{wacc*100:.2f}%"
    )

# ==========================================================
# IMPORT FCFF
# ==========================================================

st.header("Import du Business Plan")

uploaded_file = st.file_uploader(
    "Importer un fichier Excel",
    type=["xlsx"]
)

st.info("""
Le fichier Excel doit contenir :

Colonne 1 : Année
Colonne 2 : FCFF

Exemple :

2026 | 37
2027 | 67
2028 | 123
2029 | 157
2030 | 175
""")

# ==========================================================
# TRAITEMENT
# ==========================================================

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    st.subheader("FCFF importés")
    st.dataframe(df)

    years = df.iloc[:, 0]
    fcff = df.iloc[:, 1]

    # --------------------------------------
    # Sécurité Gordon-Shapiro
    # --------------------------------------

    if g >= wacc:

        st.error(
            "Le taux de croissance terminale doit être inférieur au WACC."
        )

        st.stop()

    # --------------------------------------
    # Actualisation
    # --------------------------------------

    discount_factors = []

    for i in range(len(fcff)):
        factor = 1 / ((1 + wacc) ** (i + 1))
        discount_factors.append(factor)

    discount_factors = np.array(discount_factors)

    pv_fcff = fcff * discount_factors

    pv_fcff_sum = pv_fcff.sum()

    # --------------------------------------
    # Flux normatif
    # --------------------------------------

    last_fcff = float(fcff.iloc[-1])

    fcff_normatif = last_fcff * (1 + g)

    # --------------------------------------
    # Valeur terminale
    # --------------------------------------

    terminal_value = (
        fcff_normatif
        / (wacc - g)
    )

    pv_terminal = (
        terminal_value
        * discount_factors[-1]
    )

    # --------------------------------------
    # Valorisation
    # --------------------------------------

    enterprise_value = (
        pv_fcff_sum
        + pv_terminal
    )

    equity_value = (
        enterprise_value
        - debt
    )

    value_per_share = (
        equity_value
        / shares
    )

    # ======================================================
    # RESULTATS
    # ======================================================

    st.header("Résultats DCF")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Valeur Terminale Actualisée",
        f"{pv_terminal:,.0f}"
    )

    c2.metric(
        "Enterprise Value",
        f"{enterprise_value:,.0f}"
    )

    c3.metric(
        "Equity Value",
        f"{equity_value:,.0f}"
    )

    c4.metric(
        "Valeur par action",
        f"{value_per_share:,.2f}"
    )

    # ======================================================
    # TABLEAU DCF
    # ======================================================

    dcf_df = pd.DataFrame({
        "Année": years,
        "FCFF": fcff,
        "Facteur Actualisation": discount_factors,
        "FCFF Actualisé": pv_fcff
    })

    st.subheader("Tableau DCF")

    st.dataframe(
        dcf_df,
        use_container_width=True
    )

    # ======================================================
    # GRAPHIQUE FCFF
    # ======================================================

    st.subheader("Evolution des FCFF")

    fig_fcff = px.bar(
        dcf_df,
        x="Année",
        y="FCFF",
        title="Free Cash Flow Forecast"
    )

    st.plotly_chart(
        fig_fcff,
        use_container_width=True
    )

    # ======================================================
    # SENSIBILITE WACC / g
    # ======================================================

    st.header("Sensibilité WACC / g")

    wacc_range = np.arange(
        max(0.01, wacc - 0.02),
        wacc + 0.021,
        0.005
    )

    g_range = np.arange(
        0.01,
        min(wacc - 0.005, 0.05),
        0.005
    )

    sensitivity = pd.DataFrame(
        index=[f"{x*100:.1f}%" for x in wacc_range],
        columns=[f"{x*100:.1f}%" for x in g_range]
    )

    for w in wacc_range:

        for gg in g_range:

            if w > gg:

                tv = fcff_normatif / (w - gg)

                pv_tv = tv * discount_factors[-1]

                ev = pv_fcff_sum + pv_tv

                eq = ev - debt

                px_value = eq / shares

                sensitivity.loc[
                    f"{w*100:.1f}%",
                    f"{gg*100:.1f}%"
                ] = round(px_value, 2)

    sensitivity = sensitivity.astype(float)

    st.dataframe(
        sensitivity,
        use_container_width=True
    )

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    sns.heatmap(
        sensitivity,
        annot=True,
        fmt=".0f",
        cmap="RdYlGn",
        ax=ax
    )

    ax.set_title(
        "Sensibilité Valeur par Action"
    )

    st.pyplot(fig)

else:

    st.warning(
        "Veuillez importer un fichier Excel contenant les FCFF."
    )
