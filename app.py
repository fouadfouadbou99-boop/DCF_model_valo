# ==========================================
# MODULE DE VALORISATION DCF COMPLET
# ==========================================

import numpy as np
import pandas as pd

# ==========================================
# 1. HYPOTHESES
# ==========================================

# Marché

risk_free_rate = 0.0353      # 3.53 %
market_risk_premium = 0.0607 # 6.07 %
specific_risk_premium = 0.015 # 1.50 %

# Fiscalité

tax_rate = 0.35

# Structure cible

debt = 11.0          # Dette nette MMAD
equity = 1783.0      # Valeur FP cible MMAD

# Béta comparable

beta_unlevered = 0.906

# Dette

cost_of_debt = 0.06

# Nombre d'actions

shares_outstanding = 13.125

# Croissance terminale

g = 0.02

# ==========================================
# 2. RELEVER LE BETA (HAMADA)
# ==========================================

de_ratio = debt / equity

beta_levered = beta_unlevered * (
    1 + (1 - tax_rate) * de_ratio
)

print("Beta endetté :", round(beta_levered, 3))

# ==========================================
# 3. CAPM AJUSTE
# ==========================================

cost_of_equity = (
    risk_free_rate
    + beta_levered * market_risk_premium
    + specific_risk_premium
)

print("Coût des fonds propres :", round(cost_of_equity * 100, 2), "%")

# ==========================================
# 4. WACC
# ==========================================

total_capital = debt + equity

weight_equity = equity / total_capital
weight_debt = debt / total_capital

after_tax_cost_debt = cost_of_debt * (1 - tax_rate)

wacc = (
    weight_equity * cost_of_equity
    + weight_debt * after_tax_cost_debt
)

print("WACC :", round(wacc * 100, 2), "%")

# ==========================================
# 5. PROJECTION DES FCFF
# ==========================================

years = [2026, 2027, 2028, 2029, 2030]

fcff = np.array([
    37,
    67,
    123,
    157,
    175
])

# ==========================================
# 6. ACTUALISATION DES FCFF
# ==========================================

discount_factors = np.array([
    1 / (1 + wacc) ** 0.25,
    1 / (1 + wacc) ** 1.25,
    1 / (1 + wacc) ** 2.25,
    1 / (1 + wacc) ** 3.25,
    1 / (1 + wacc) ** 4.25
])

pv_fcff = fcff * discount_factors

pv_fcff_sum = pv_fcff.sum()

print("Somme FCFF actualisés :", round(pv_fcff_sum, 1))

# ==========================================
# 7. FLUX NORMATIF
# ==========================================

fcff_2030 = fcff[-1]

fcff_normatif = fcff_2030 * (1 + g)

print("FCFF normatif :", round(fcff_normatif, 1))

# ==========================================
# 8. VALEUR TERMINALE
# ==========================================

terminal_value = (
    fcff_normatif
    / (wacc - g)
)

print("Valeur terminale brute :", round(terminal_value, 1))

# ==========================================
# 9. VALEUR TERMINALE ACTUALISEE
# ==========================================

pv_terminal_value = (
    terminal_value
    * discount_factors[-1]
)

print(
    "Valeur terminale actualisée :",
    round(pv_terminal_value, 1)
)

# ==========================================
# 10. ENTREPRISE VALUE
# ==========================================

enterprise_value = (
    pv_fcff_sum
    + pv_terminal_value
)

print(
    "Valeur d'entreprise :",
    round(enterprise_value, 1)
)

# ==========================================
# 11. EQUITY VALUE
# ==========================================

equity_value = (
    enterprise_value
    - debt
)

print(
    "Valeur des fonds propres :",
    round(equity_value, 1)
)

# ==========================================
# 12. VALEUR PAR ACTION
# ==========================================

value_per_share = (
    equity_value
    / shares_outstanding
)

print(
    "Valeur par action :",
    round(value_per_share, 2)
)

# ==========================================
# 13. TABLEAU DE SYNTHESE
# ==========================================

results = pd.DataFrame({
    "Année": years,
    "FCFF": fcff,
    "Facteur Actu.": discount_factors,
    "FCFF Actualisé": pv_fcff
})

print("\n")
print(results)
