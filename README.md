# DCF Equity Valuation

Application web de valorisation des fonds propres basée sur la méthode des Discounted Cash-Flows (DCF).

## Fonctionnalités

- Calcul du coût des fonds propres (CAPM)
- Calcul du WACC
- Projection des FCFF sur 5 ans
- Calcul de la Valeur Terminale
- Calcul de la Valeur d'Entreprise
- Calcul de la Valeur des Fonds Propres
- Calcul de la Valeur par Action
- Export Excel

## Installation

```bash
git clone https://github.com/votre-compte/dcf-equity-valuation.git
cd dcf-equity-valuation
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app.py
```

## Formules

### Coût des fonds propres

```text
Ke = Rf + Beta × Prime de risque
```

### WACC

```text
WACC = E/V × Ke + D/V × Kd × (1-T)
```

### FCFF

```text
FCFF = NOPAT + Amortissements - CAPEX - Variation BFR
```

### Valeur Terminale

```text
VT = FCFFn × (1+g) / (WACC-g)
```

### Valeur d'Entreprise

```text
EV = Somme des FCFF actualisés + VT actualisée
```

### Valeur des Fonds Propres

```text
Equity Value = EV - Dette Nette
```

### Valeur par Action

```text
Valeur par Action = Equity Value / Nombre d'Actions
```

## Données de référence

- Valeur d'Entreprise : 3 232 MMAD
- Dette Nette : 800 MMAD
- Valeur des Fonds Propres : 2 432 MMAD
- Nombre d'Actions : 1 220 000
- Valeur par Action : 1 993,44 MAD

## Auteur

Fouad Boukhnif
