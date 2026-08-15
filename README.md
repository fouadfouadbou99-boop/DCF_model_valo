# DCF Valuation Model

Application Streamlit permettant d'automatiser la valorisation d'entreprise par la méthode des Discounted Cash Flows (DCF).

## Fonctionnalités

- Calcul automatique du coût des fonds propres (CAPM)
- Calcul du WACC
- Projection du chiffre d'affaires
- Calcul du NOPAT
- Calcul du FCFF
- Actualisation des flux
- Calcul de la valeur terminale
- Calcul de la valeur d'entreprise

## Installation

Cloner le dépôt :

```bash
git clone https://github.com/votre-compte/dcf-streamli.git
cd dcf-streamli
```

Créer un environnement virtuel :

```bash
python -m venv venv
```

Activer l'environnement :

Windows :

```bash
venv\Scripts\activate
```

Linux / Mac :

```bash
source venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Exécution

```bash
streamlit run app.py
```

## Hypothèses supportées

- Taux sans risque
- Beta
- Prime de risque marché
- Coût de la dette
- Structure financière
- Taux d'imposition
- Croissance terminale

## Formule utilisée

### Coût des fonds propres

```text
Ke = Rf + Beta × Prime de marché
```

### WACC

```text
WACC = E/V × Ke + D/V × Kd × (1-T)
```

### FCFF

```text
FCFF = NOPAT + D&A - CAPEX - ΔBFR
```

### Valeur Terminale

```text
TV = FCFFn × (1+g) / (WACC-g)
```

## Déploiement sur Streamlit Cloud

1. Pousser le projet vers GitHub.
2. Créer un compte Streamlit Community Cloud.
3. Connecter le repository GitHub.
4. Sélectionner app.py.
5. Déployer.

## Auteur

Fouad Boukhnif
