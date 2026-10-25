import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="DCF Valuation Tool",
    layout="wide"
)

st.title("DCF Valuation Tool")

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("Hypothèses de valorisation")

risk_free = st.sidebar.number_input(
    "Taux sans risque (%)",
    value=3.53,
    step=0.01
) / 100

market_premium = st.sidebar.number_input(
    "Prime de marché (%)",
    value=6.07,
    step=0.01
) / 100

specific_risk = st.sidebar.number_input(
    "Prime de risque spécifique (%)",
    value=1.50,
    step=0.01
) / 100

tax_rate = st.sidebar.number_input(
    "Taux d'impôt (%)",
    value=35.0,
    step=1.0
) / 100

beta_unlevered = st.sidebar.number_input(
    "Beta désendetté",
    value=0.906,
    step=0.001
)

debt = st.sidebar.number_input(
    "Dette nette (MMAD)",
    value=11.0,
    step=1.0
)

equity = st.sidebar.number_input(
    "Valeur cible des fonds propres (MMAD)",
    value=1783.0,
    step=10.0
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

# =====================================================
# NOUVEAU : RECONCILIATION
# =====================================================

use_manual_normative = st.sidebar.checkbox(
    "Flux normatif manuel",
    value=True
)

fcff_normative_manual = st.sidebar.number_input(
    "FCFF normatif",
    value=178.8,
    step=0.1
)

use_manual_factor = st.sidebar.checkbox(
    "Facteur terminal manuel",
    value=True
)

terminal_discount_factor = st.sidebar.number_input(
    "Facteur actualisation terminal",
    value=0.654,
    step=0.001,
    format="%.3f"
)

shares = st.sidebar.number_input(
    "Nombre d'actions (millions)",
    value=12.47,
    step=0.01
)

# =====================================================
# CALCUL WACC
# =====================================================

beta_levered = beta_unlevered * (
    1 +
    (1 - tax_rate)
    * (debt / equity)
)

cost_equity = (
    risk_free
    + beta_levered * market_premium
    + specific_risk
)

capital = debt + equity

weight_debt = debt / capital
weight_equity = equity / capital

wacc = (
    weight_equity * cost_equity
    + weight_debt * cost_debt * (1 - tax_rate)
)

# =====================================================
# METRICS
# =====================================================

st.subheader("Paramètres financiers")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Beta endetté",
    f"{beta_levered:.3f}"
)

c2.metric(
    "Coût des fonds propres",
    f"{cost_equity*100:.2f}%"
)

c3.metric(
    "WACC",
    f"{wacc*100:.2f}%"
)

# =====================================================
# IMPORT EXCEL
# =====================================================

mode = st.radio(
    "Mode de valorisation",
    [
        "Business Plan",
        "Import FCFF"
    ]
)

fcff = None
years = None
bp = None

if mode == "Business Plan":

    bp_file = st.file_uploader(
        "Importer Business Plan",
        type=["xlsx"],
        key="bp"
    )

    if bp_file is not None:

        bp = pd.read_excel(bp_file)

        st.subheader("Business Plan")

        st.dataframe(bp)

        bp["FCFF"] = (
            bp["EBITDA"]
            - bp["IS"]
            - bp["CAPEX"]
            - bp["BFR"]
        )

        years = bp["Année"]

        fcff = bp["FCFF"]

        st.subheader("FCFF Calculés")

        st.dataframe(
            bp[
                [
                    "Année",
                    "FCFF"
                ]
            ]
        )

        bp["Marge EBITDA"] = (
            bp["EBITDA"]
            / bp["CA"]
        )

        c1,c2,c3,c4 = st.columns(4)

        c1.metric(
            "CA Final",
            f"{bp['CA'].iloc[-1]:,.0f}"
        )

        c2.metric(
            "EBITDA Final",
            f"{bp['EBITDA'].iloc[-1]:,.0f}"
        )

        c3.metric(
            "FCFF Final",
            f"{bp['FCFF'].iloc[-1]:,.0f}"
        )

        c4.metric(
            "Marge EBITDA",
            f"{bp['Marge EBITDA'].iloc[-1]*100:.1f}%"
        )

else:

    uploaded_file = st.file_uploader(
        "Importer fichier FCFF",
        type=["xlsx"],
        key="fcff"
    )

    if uploaded_file:

        df = pd.read_excel(uploaded_file)

        years = df.iloc[:,0]

        fcff = df.iloc[:,1].astype(float)

# =====================================================
# TRAITEMENT
# =====================================================

if fcff is not None:

    try:

        df = pd.read_excel(uploaded_file)

        st.subheader("Flux importés")

        st.dataframe(df)

        years = df.iloc[:, 0]
        fcff = df.iloc[:, 1].astype(float)

        if g >= wacc:

            st.error(
                "Le taux de croissance doit être inférieur au WACC."
            )

            st.stop()

        # =================================================
        # STUB PERIOD JET ENERGY
        # =================================================

discounting_method = st.sidebar.selectbox(
    "Méthode d'actualisation",
    [
        "Classique",
        "Stub Period"
    ]
)

if discounting_method == "Classique":

    periods = list(
        range(
            1,
            len(fcff)+1
        )
    )

else:

    first_period = st.sidebar.number_input(
        "Première période (année)",
        value=0.25,
        step=0.25
    )

    periods = [
        first_period + i
        for i in range(len(fcff))
    ]

        # =================================================
        # FLUX NORMATIF
        # =================================================

        if use_manual_normative:

            fcff_normatif = fcff_normative_manual

        else:

            fcff_normatif = (
                fcff.iloc[-1]
                * (1 + g)
            )

        # =================================================
        # VALEUR TERMINALE
        # =================================================

        terminal_value = (
            fcff_normatif
            / (wacc - g)
        )

        pv_terminal_theoretical = (
            terminal_value
            * discount_factors[-1]
        )

        if use_manual_factor:

            pv_terminal = (
                terminal_value
                * terminal_discount_factor
            )

        else:

            pv_terminal = (
                terminal_value
                * discount_factors[-1]
            )

        # =================================================
        # VALORISATION
        # =================================================

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

        # =================================================
        # RESULTATS
        # =================================================

        st.header("Résultats DCF")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Valeur Terminale Actualisée",
            f"{pv_terminal:,.0f}"
        )

        col2.metric(
            "Enterprise Value",
            f"{enterprise_value:,.0f}"
        )

        col3.metric(
            "Equity Value",
            f"{equity_value:,.0f}"
        )

        col4.metric(
            "Valeur par action",
            f"{value_per_share:,.2f}"
        )

        # =================================================
        # RECONCILIATION
        # =================================================

        st.subheader("Réconciliation DCF")

        r1, r2, r3 = st.columns(3)

        r1.metric(
            "FCFF Normatif",
            f"{fcff_normatif:,.1f}"
        )

        r2.metric(
            "Facteur Théorique",
            f"{discount_factors[-1]:.4f}"
        )

        facteur_utilise = (
            terminal_discount_factor
            if use_manual_factor
            else discount_factors[-1]
        )

        r3.metric(
            "Facteur Utilisé",
            f"{facteur_utilise:.4f}"
        )

        # =================================================
        # TABLEAU DCF
        # =================================================

        dcf_df = pd.DataFrame(
            {
                "Année": years,
                "FCFF": fcff,
                "Facteur Actualisation": discount_factors,
                "FCFF Actualisé": pv_fcff
            }
        )

        st.subheader("Tableau DCF")

        st.dataframe(
            dcf_df,
            use_container_width=True
        )

        st.metric(
            "Somme FCFF actualisés",
            f"{pv_fcff_sum:,.0f}"
        )

        # =================================================
        # COMMENTAIRE DE GESTION
        # =================================================

        st.header("Commentaire de Gestion")

        terminal_weight = (
            pv_terminal
            / enterprise_value
        ) * 100

        commentaire = f"""
Enterprise Value : {enterprise_value:,.0f} MMAD

Valeur des fonds propres : {equity_value:,.0f} MMAD

Valeur théorique par action : {value_per_share:,.2f}

WACC retenu : {wacc*100:.2f} %

Croissance terminale : {g*100:.2f} %

La valeur terminale représente {terminal_weight:.1f}% de la valeur d'entreprise.
"""

        st.write(commentaire)

        # =================================================
        # SENSIBILITE
        # =================================================

        st.header("Sensibilité WACC / g")

        wacc_range = np.arange(
            max(0.05, wacc - 0.02),
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

                    tv = (
                        fcff_normatif
                        / (w - gg)
                    )

                    pv_tv = (
                        tv
                        * facteur_utilise
                    )

                    ev = pv_fcff_sum + pv_tv

                    eq = ev - debt

                    px = eq / shares

                    sensitivity.loc[
                        f"{w*100:.1f}%",
                        f"{gg*100:.1f}%"
                    ] = round(px, 2)

        sensitivity = sensitivity.astype(float)

        fig, ax = plt.subplots(figsize=(10, 6))

        sns.heatmap(
            sensitivity,
            annot=True,
            fmt=".1f",
            cmap="RdYlGn",
            ax=ax
        )

        st.pyplot(fig)

        # =================================================
        # EXPORT EXCEL
        # =================================================

        buffer = BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine="openpyxl"
        ) as writer:

            dcf_df.to_excel(
                writer,
                sheet_name="DCF",
                index=False
            )

            sensitivity.to_excel(
                writer,
                sheet_name="Sensibilite"
            )

            pd.DataFrame({
                "Indicateur": [
                    "WACC",
                    "FCFF Normatif",
                    "Valeur Terminale",
                    "Enterprise Value",
                    "Equity Value",
                    "Valeur par Action"
                ],
                "Valeur": [
                    wacc,
                    fcff_normatif,
                    pv_terminal,
                    enterprise_value,
                    equity_value,
                    value_per_share
                ]
            }).to_excel(
                writer,
                sheet_name="Synthese",
                index=False
            )

            pd.DataFrame({
                "Commentaire": [commentaire]
            }).to_excel(
                writer,
                sheet_name="Investment_Memo",
                index=False
            )

        buffer.seek(0)

        st.download_button(
            "📥 Télécharger le rapport Excel",
            data=buffer,
            file_name="DCF_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(f"Erreur : {str(e)}")
