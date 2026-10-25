import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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
    "Valeur des fonds propres cible (MMAD)",
    value=1783.0,
    step=10.0
)

cost_debt = st.sidebar.number_input(
    "Coût de la dette (%)",
    value=6.0,
    step=0.10
) / 100

g = st.sidebar.number_input(
    "Croissance à l'infini (%)",
    value=2.0,
    step=0.10
) / 100

shares = st.sidebar.number_input(
    "Nombre d'actions (millions)",
    value=12.47,
    step=0.01
)

# ==========================================================
# CALCUL BETA ENDETTE
# ==========================================================

beta_levered = beta_unlevered * (
    1 + (1 - tax_rate) * (debt / equity)
)

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

weight_debt = debt / capital
weight_equity = equity / capital

wacc = (
    weight_equity * cost_equity
    + weight_debt * cost_debt * (1 - tax_rate)
)

# ==========================================================
# AFFICHAGE PARAMETRES
# ==========================================================

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

# ==========================================================
# IMPORT EXCEL
# ==========================================================

st.header("Import du Business Plan")

uploaded_file = st.file_uploader(
    "Importer un fichier Excel",
    type=["xlsx"]
)

st.info("""
Format attendu :

Année | FCFF

2026 | 37
2027 | 67
2028 | 123
2029 | 157
2030 | 175
""")

if uploaded_file:

    try:

        df = pd.read_excel(uploaded_file)

        st.subheader("FCFF Importés")
        st.dataframe(df)

        years = df.iloc[:, 0]
        fcff = df.iloc[:, 1].astype(float)

        # ==================================================
        # CONTROLE GORDON SHAPIRO
        # ==================================================

        if g >= wacc:

            st.error(
                "Le taux de croissance terminale doit être inférieur au WACC."
            )

            st.stop()

        # ==================================================
        # STUB PERIOD
        # Méthode Jet Energy
        # ==================================================

        periods = [
            0.25,
            1.25,
            2.25,
            3.25,
            4.25
        ]

        discount_factors = np.array([
            1 / ((1 + wacc) ** p)
            for p in periods
        ])

        pv_fcff = fcff.values * discount_factors

        pv_fcff_sum = pv_fcff.sum()

        # ==================================================
        # FLUX NORMATIF
        # ==================================================

        fcff_normatif = fcff.iloc[-1] * (1 + g)

        # ==================================================
        # VALEUR TERMINALE
        # ==================================================

        terminal_value = (
            fcff_normatif
            / (wacc - g)
        )

        pv_terminal = (
            terminal_value
            * discount_factors[-1]
        )

        # ==================================================
        # VALORISATION
        # ==================================================

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

        # ==================================================
        # RESULTATS
        # ==================================================

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

        # ==================================================
        # TABLEAU DCF
        # ==================================================

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

        st.metric(
            "Somme des FCFF Actualisés",
            f"{pv_fcff_sum:,.0f}"
        )

        # ==================================================
        # HEATMAP SENSIBILITE
        # ==================================================

        st.header(
            "Sensibilité Valeur par Action (WACC / g)"
        )

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
            index=[f"{w*100:.1f}%" for w in wacc_range],
            columns=[f"{gg*100:.1f}%" for gg in g_range]
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
                    ] = round(px, 1)

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
            fmt=".1f",
            cmap="RdYlGn",
            ax=ax
        )

        ax.set_title(
            "Sensibilité Valeur par Action"
        )

        st.pyplot(fig)

    except Exception as e:

        st.error(
            f"Erreur lors de la lecture du fichier : {e}"
        )

else:

    st.warning(
        "Veuillez importer un fichier FCFF au format Excel."
    )
