import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)

from reportlab.lib.styles import getSampleStyleSheet
st.set_page_config(
    page_title="Corporate Valuation Platform",
    layout="wide"
)

st.title("Corporate Valuation Platform")
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Dashboard",
    "📈 Business Plan",
    "💰 DCF",
    "🎯 Sensibilités",
    "⚠️ Stress Tests",
    "📄 Rapport"
])
st.sidebar.header("Hypothèses")

risk_free = st.sidebar.number_input(
    "Taux sans risque (%)",
    value=3.5
)/100

market_premium = st.sidebar.number_input(
    "Prime de marché (%)",
    value=6.0
)/100

beta = st.sidebar.number_input(
    "Beta",
    value=1.0
)

specific_risk = st.sidebar.number_input(
    "Prime spécifique (%)",
    value=1.0
)/100

tax_rate = st.sidebar.number_input(
    "Impôt (%)",
    value=30.0
)/100

cost_debt = st.sidebar.number_input(
    "Coût dette (%)",
    value=5.0
)/100

terminal_growth = st.sidebar.number_input(
    "Croissance terminale (%)",
    value=2.0
)/100

net_debt = st.sidebar.number_input(
    "Dette nette",
    value=100.0
)

shares = st.sidebar.number_input(
    "Actions (millions)",
    value=10.0
)
with tab2:

    st.subheader("Business Plan")

    revenue0 = st.number_input(
        "CA année 0",
        value=1000.0
    )

    growth_rate = st.number_input(
        "Croissance (%)",
        value=5.0
    )/100

    ebitda_margin = st.number_input(
        "Marge EBITDA (%)",
        value=25.0
    )/100

    depreciation_pct = st.number_input(
        "Amortissements (% CA)",
        value=3.0
    )/100

    capex_pct = st.number_input(
        "CAPEX (% CA)",
        value=5.0
    )/100

    nwc_pct = st.number_input(
        "Variation BFR (% CA)",
        value=2.0
    )/100

    years = 5

    bp = []

    revenue = revenue0

    for y in range(1, years+1):

        revenue *= (1 + growth_rate)

        ebitda = revenue * ebitda_margin

        depreciation = revenue * depreciation_pct

        ebit = ebitda - depreciation

        nopat = ebit * (1-tax_rate)

        capex = revenue * capex_pct

        nwc = revenue * nwc_pct

        fcff = (
            nopat
            + depreciation
            - capex
            - nwc
        )

        bp.append([
            y,
            revenue,
            ebitda,
            ebit,
            fcff
        ])

    bp_df = pd.DataFrame(bp,
        columns=[
            "Année",
            "CA",
            "EBITDA",
            "EBIT",
            "FCFF"
        ])

    st.dataframe(
        bp_df,
        use_container_width=True
    )
    cost_equity = (
    risk_free
    + beta * market_premium
    + specific_risk
)

target_equity = 1000

target_debt = net_debt

capital = (
    target_equity +
    target_debt
)

wacc = (
    target_equity/capital
    * cost_equity +
    target_debt/capital
    * cost_debt
    * (1-tax_rate)
)
fcffs = bp_df["FCFF"].values

discounts = np.array([
    1/(1+wacc)**i
    for i in range(1,6)
])

pv_fcff = (
    fcffs * discounts
)

pv_fcff_sum = pv_fcff.sum()
fcff_norm = (
    fcffs[-1]
    * (1+terminal_growth)
)

tv = (
    fcff_norm /
    (wacc-terminal_growth)
)

pv_tv = tv*discounts[-1]
enterprise_value = (
    pv_fcff_sum
    + pv_tv
)

equity_value = (
    enterprise_value
    - net_debt
)

share_price = (
    equity_value
    / shares
)
with tab1:

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
        "Valeur Action",
        f"{share_price:,.2f}"
    )

    c4.metric(
        "WACC",
        f"{wacc*100:.2f}%"
    )
    with tab3:

       st.subheader("Valorisation DCF")

       st.metric(
        "Enterprise Value",
        f"{enterprise_value:,.0f}"
    )

    st.metric(
        "Equity Value",
        f"{equity_value:,.0f}"
    )

    st.metric(
        "Valeur Action",
        f"{share_price:,.2f}"
    )

    dcf_table = pd.DataFrame({
        "Année": bp_df["Année"],
        "FCFF": fcffs,
        "Facteur": discounts,
        "PV FCFF": pv_fcff
    })

    st.dataframe(
        dcf_table,
        width="stretch"
    )
    with tab4:

        st.subheader("Sensibilité WACC / g")

    results = []

    for w in np.arange(
        wacc - 0.02,
        wacc + 0.021,
        0.005
    ):

        for g_test in np.arange(
            0.01,
            0.05,
            0.005
        ):

            if w > g_test:

                tv = (
                    fcff_norm
                    /
                    (w - g_test)
                )

                ev = (
                    pv_fcff_sum
                    +
                    tv * discounts[-1]
                )

                eq = ev - net_debt

                px = eq / shares

                results.append(
                    [w, g_test, px]
                )

    sensitivity = pd.DataFrame(
        results,
        columns=[
            "WACC",
            "Croissance",
            "Prix Action"
        ]
    )

    st.dataframe(
        sensitivity,
        width="stretch"
    )
   with tab5:

    st.subheader("Stress Tests")

    scenarios = pd.DataFrame({
        "Scénario": [
            "Optimiste",
            "Base",
            "Dégradé",
            "Crise"
        ],
        "Facteur": [
            1.15,
            1.00,
            0.85,
            0.70
        ]
    })

    scenarios["Enterprise Value"] = (
        enterprise_value
        * scenarios["Facteur"]
    )

    scenarios["Equity Value"] = (
        equity_value
        * scenarios["Facteur"]
    )

    scenarios["Valeur Action"] = (
        share_price
        * scenarios["Facteur"]
    )

    st.dataframe(scenarios)

    st.bar_chart(
        scenarios.set_index("Scénario")[
            "Valeur Action"
        ]
    )


    scenarios["Valeur Action"] = (
        share_price
        * scenarios["Facteur"]
    )

    st.dataframe(scenarios)

    st.bar_chart(
        scenarios.set_index("Scénario")[
            "Valeur Action"
        ]
    )


    scenarios["Equity Value"] = (
        equity_value
        * scenarios["Facteur"]
    )

    scenarios["Valeur Action"] = (
        share_price
        * scenarios["Facteur"]
    )

    st.dataframe(
        scenarios,
        width="stretch"
    )

    fig = px.bar(
    scenarios,
    x="Scénario",
    y="Valeur Action",
    color="Scénario",
    title="Stress Test - Valeur par action"
)

st.plotly_chart(
    fig,
    use_container_width=True
)
    )
committee_note = f"""
EXECUTIVE SUMMARY

La valorisation DCF conduit à une
Enterprise Value de
{enterprise_value:,.0f} MMAD.

La valeur des capitaux propres
ressort à
{equity_value:,.0f} MMAD.

La valeur théorique par action
est estimée à
{share_price:,.2f} DH.

Le modèle repose sur un WACC de
{wacc*100:.2f}% et une croissance
terminale de
{terminal_growth*100:.2f}%.

La valeur terminale représente
{terminal_weight:.1f}% de la valeur
totale.

Les stress tests démontrent une
résilience satisfaisante de
la valorisation.

Sous réserve de réalisation du
Business Plan, les hypothèses
retenues paraissent raisonnables
pour une présentation au
Comité d'Investissement.
"""
def create_pdf():

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer
    )

    styles = (
        getSampleStyleSheet()
    )

    story = []

    story.append(
        Paragraph(
            "Rapport de Valorisation",
            styles["Title"]
        )
    )

    story.append(
        Spacer(1,20)
    )

    story.append(
        Paragraph(
            committee_note,
            styles["BodyText"]
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer
    excel_buffer = BytesIO()
with tab6:

    st.subheader("Exports")

    excel_buffer = BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        if 'bp_df' in locals():
            bp_df.to_excel(
                writer,
                sheet_name="BusinessPlan",
                index=False
            )

        if 'sensitivity' in locals():
            sensitivity.to_excel(
                writer,
                sheet_name="Sensibilites",
                index=False
            )

        if 'scenarios' in locals():
            scenarios.to_excel(
                writer,
                sheet_name="StressTests",
                index=False
            )

    excel_buffer.seek(0)

    st.download_button(
        label="📥 Télécharger Excel",
        data=excel_buffer.getvalue(),
        file_name="DCF_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
