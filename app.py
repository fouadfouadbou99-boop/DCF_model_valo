import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

st.set_page_config(
    page_title="DCF Valuation V3",
    layout="wide"
)

st.title("DCF Valuation Platform")

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("Hypothèses WACC")

rf = st.sidebar.number_input(
    "Taux sans risque (%)",
    value=3.5
) / 100

market_risk_premium = st.sidebar.number_input(
    "Prime de marché (%)",
    value=6.0
) / 100

specific_risk = st.sidebar.number_input(
    "Prime spécifique (%)",
    value=0.0
) / 100

tax_rate = st.sidebar.number_input(
    "Taux d'impôt (%)",
    value=30.0
) / 100

beta_mode = st.sidebar.selectbox(
    "Méthode Beta",
    [
        "Beta Manuel",
        "Beta Hamada"
    ]
)

if beta_mode == "Beta Manuel":

    beta = st.sidebar.number_input(
        "Beta",
        value=1.00
    )

else:

    beta_unlevered = st.sidebar.number_input(
        "Beta Désendetté",
        value=0.90
    )

    debt = st.sidebar.number_input(
        "Dette",
        value=100.0
    )

    equity = st.sidebar.number_input(
        "Fonds Propres",
        value=500.0
    )

    beta = beta_unlevered * (
        1 + (1-tax_rate)*(debt/equity)
    )

cost_debt = st.sidebar.number_input(
    "Coût Dette (%)",
    value=5.0
) / 100

terminal_growth = st.sidebar.number_input(
    "Croissance terminale (%)",
    value=2.0
) / 100

shares = st.sidebar.number_input(
    "Nombre d'actions",
    value=100.0
)

debt_net = st.sidebar.number_input(
    "Dette nette",
    value=100.0
)
cost_equity = (
    rf
    + beta * market_risk_premium
    + specific_risk
)

capital = debt_net + max(1, shares)

equity_weight = 0.80
debt_weight = 0.20

wacc = (
    equity_weight * cost_equity
    + debt_weight * cost_debt * (1-tax_rate)
)

col1,col2,col3 = st.columns(3)

col1.metric(
    "Beta",
    round(beta,3)
)

col2.metric(
    "Coût FP",
    f"{cost_equity*100:.2f}%"
)

col3.metric(
    "WACC",
    f"{wacc*100:.2f}%"
)
st.header("Business Plan")

bp_file = st.file_uploader(
    "Importer Excel Business Plan",
    type=["xlsx"]
)

if bp_file is not None:

    bp = pd.read_excel(bp_file)

    st.dataframe(
        bp,
        width="stretch"
    )

    required = [
        "Année",
        "CA",
        "EBITDA",
        "Impot",
        "CAPEX",
        "BFR"
    ]

    missing = [
        c
        for c in required
        if c not in bp.columns
    ]

    if missing:

        st.error(
            f"Colonnes manquantes : {missing}"
        )

        st.stop()

    bp["FCFF"] = (
        bp["EBITDA"]
        - bp["Impot"]
        - bp["CAPEX"]
        - bp["BFR"]
    )

    st.subheader(
        "FCFF générés"
    )

    st.dataframe(
        bp[
            [
                "Année",
                "FCFF"
            ]
        ],
        width="stretch"
    )
        fcff = bp["FCFF"]

    periods = np.arange(
        1,
        len(fcff)+1
    )

    discount_factors = np.array([
        1/((1+wacc)**p)
        for p in periods
    ])

    pv_fcff = (
        fcff.values
        * discount_factors
    )

    pv_fcff_sum = pv_fcff.sum()

    fcff_terminal = (
        fcff.iloc[-1]
        * (1+terminal_growth)
    )

    terminal_value = (
        fcff_terminal
        /(wacc-terminal_growth)
    )

    pv_terminal = (
        terminal_value
        * discount_factors[-1]
    )

    enterprise_value = (
        pv_fcff_sum
        + pv_terminal
    )

    equity_value = (
        enterprise_value
        - debt_net
    )

    price_target = (
        equity_value
        / shares
    )
    st.header("Valorisation")

    c1,c2,c3,c4 = st.columns(4)

    c1.metric(
        "Enterprise Value",
        f"{enterprise_value:,.0f}"
    )

    c2.metric(
        "Equity Value",
        f"{equity_value:,.0f}"
    )

    c3.metric(
        "Valeur Terminale",
        f"{pv_terminal:,.0f}"
    )

    c4.metric(
        "Valeur / Action",
        f"{price_target:,.2f}"
    )
    st.header("Sensibilité")

    wacc_range = np.arange(
        wacc-0.02,
        wacc+0.021,
        0.005
    )

    g_range = np.arange(
        0.01,
        0.05,
        0.005
    )

    sensitivity = pd.DataFrame(
        index=[
            f"{w*100:.1f}%"
            for w in wacc_range
        ],
        columns=[
            f"{g*100:.1f}%"
            for g in g_range
        ]
    )

    for w in wacc_range:

        for g in g_range:

            if w > g:

                tv = (
                    fcff_terminal
                    /(w-g)
                )

                pv_tv = (
                    tv
                    * discount_factors[-1]
                )

                ev = (
                    pv_fcff_sum
                    + pv_tv
                )

                eq = ev - debt_net

                px = eq/shares

                sensitivity.loc[
                    f"{w*100:.1f}%",
                    f"{g*100:.1f}%"
                ] = round(px,1)

    sensitivity = (
        sensitivity
        .fillna(0)
        .astype(float)
    )

    fig, ax = plt.subplots(
        figsize=(10,6)
    )

    sns.heatmap(
        sensitivity,
        annot=True,
        fmt=".1f",
        cmap="RdYlGn",
        ax=ax
    )

    st.pyplot(fig)
    buffer = BytesIO()

    with pd.ExcelWriter(
        buffer,
        engine="openpyxl"
    ) as writer:

        bp.to_excel(
            writer,
            sheet_name="BusinessPlan",
            index=False
        )

        sensitivity.to_excel(
            writer,
            sheet_name="Sensitivity"
        )

    buffer.seek(0)

    st.download_button(
        "Télécharger le modèle",
        data=buffer,
        file_name="DCF_Output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
