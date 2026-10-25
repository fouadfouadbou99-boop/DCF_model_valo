import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

# =====================================================
# CONFIG
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
    value=3.53
) / 100

market_premium = st.sidebar.number_input(
    "Prime de marché (%)",
    value=6.07
) / 100

specific_risk = st.sidebar.number_input(
    "Prime de risque spécifique (%)",
    value=1.50
) / 100

tax_rate = st.sidebar.number_input(
    "Taux d'impôt (%)",
    value=35.0
) / 100

beta_unlevered = st.sidebar.number_input(
    "Beta désendetté",
    value=0.906
)

debt = st.sidebar.number_input(
    "Dette nette (MMAD)",
    value=11.0
)

equity = st.sidebar.number_input(
    "Valeur des fonds propres cible (MMAD)",
    value=1783.0
)

cost_debt = st.sidebar.number_input(
    "Coût de la dette (%)",
    value=6.0
) / 100

g = st.sidebar.number_input(
    "Croissance à l'infini (%)",
    value=2.0
) / 100

shares = st.sidebar.number_input(
    "Nombre d'actions (millions)",
    value=12.47
)

# =====================================================
# WACC
# =====================================================

beta_levered = beta_unlevered * (
    1 + (1 - tax_rate) * (debt / equity)
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

c1.metric("Beta endetté", f"{beta_levered:.3f}")
c2.metric("Coût des fonds propres", f"{cost_equity*100:.2f}%")
c3.metric("WACC", f"{wacc*100:.2f}%")

# =====================================================
# IMPORT EXCEL
# =====================================================

uploaded_file = st.file_uploader(
    "Importer fichier FCFF",
    type=["xlsx"]
)

if uploaded_file:

    try:

        df = pd.read_excel(uploaded_file)

        st.subheader("Flux importés")
        st.dataframe(df)

        years = df.iloc[:, 0]
        fcff = df.iloc[:, 1].astype(float)

        if g >= wacc:

            st.error(
                "g doit être inférieur au WACC"
            )

            st.stop()

        # ============================================
        # STUB PERIOD
        # ============================================

        periods = [
            0.25,
            1.25,
            2.25,
            3.25,
            4.25
        ]

        discount_factors = np.array([
            1 / ((1 + wacc) ** p)
            for p in periods[:len(fcff)]
        ])

        pv_fcff = fcff.values * discount_factors

        pv_fcff_sum = pv_fcff.sum()

        # ============================================
        # FLUX NORMATIF
        # ============================================

        fcff_normatif = (
            fcff.iloc[-1]
            * (1 + g)
        )

        terminal_value = (
            fcff_normatif
            / (wacc - g)
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
            - debt
        )

        value_per_share = (
            equity_value
            / shares
        )

        # ============================================
        # RESULTATS
        # ============================================

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

        # ============================================
        # TABLEAU DCF
        # ============================================

        dcf_df = pd.DataFrame(
            {
                "Année": years,
                "FCFF": fcff,
                "Facteur": discount_factors,
                "FCFF Actualisé": pv_fcff
            }
        )

        st.dataframe(
            dcf_df,
            use_container_width=True
        )

        st.metric(
            "Somme FCFF actualisés",
            f"{pv_fcff_sum:,.0f}"
        )

        # ============================================
        # COMMENTAIRE AUTOMATIQUE
        # ============================================

        st.header("Commentaire de Gestion")

        terminal_weight = (
            pv_terminal
            / enterprise_value
        ) * 100

        commentaire = f"""
        Enterprise Value : {enterprise_value:,.0f} MMAD

        Equity Value : {equity_value:,.0f} MMAD

        Valeur par action : {value_per_share:,.2f}

        WACC : {wacc*100:.2f} %

        Croissance terminale : {g*100:.2f} %

        La valeur terminale représente
        {terminal_weight:.1f}% de l'Enterprise Value.
        """

        if terminal_weight > 75:

            commentaire += """

            L'essentiel de la valorisation repose
            sur les hypothèses de long terme.

            Une attention particulière doit être portée
            au WACC et au taux de croissance terminale.
            """

        elif terminal_weight > 60:

            commentaire += """

            La valorisation reste cohérente avec
            le profil d'une société en croissance.
            """

        else:

            commentaire += """

            La valorisation repose principalement
            sur les flux explicites.
            """

        st.write(commentaire)

        # ============================================
        # SENSIBILITE
        # ============================================

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
            index=[
                f"{x*100:.1f}%"
                for x in wacc_range
            ],
            columns=[
                f"{x*100:.1f}%"
                for x in g_range
            ]
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
                        * discount_factors[-1]
                    )

                    ev = (
                        pv_fcff_sum
                        + pv_tv
                    )

                    eq = ev - debt

                    px = eq / shares

                    sensitivity.loc[
                        f"{w*100:.1f}%",
                        f"{gg*100:.1f}%"
                    ] = round(px, 2)

        sensitivity = sensitivity.astype(float)

        fig, ax = plt.subplots(
            figsize=(10, 6)
        )

        sns.heatmap(
            sensitivity,
            annot=True,
            fmt=".1f",
            cmap="RdYlGn",
            ax=ax
        )

        st.pyplot(fig)

        # ============================================
        # EXPORT EXCEL
        # ============================================

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
                "Indicateur":[
                    "WACC",
                    "Valeur Terminale",
                    "Enterprise Value",
                    "Equity Value",
                    "Valeur par Action"
                ],
                "Valeur":[
                    wacc,
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
                "Commentaire":[commentaire]
            }).to_excel(
                writer,
                sheet_name="Investment Memo",
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

        st.error(
            f"Erreur : {str(e)}"
        )
