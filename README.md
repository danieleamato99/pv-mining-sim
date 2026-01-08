# PV vs Bitcoin Mining Simulator

**Web App Streamlit open-source** per simulare in **25 anni (2020-2045)** il confronto economico/ambientale tra:

- **Vendita energia FV 50.91 MWp alla rete**
- **Mining Bitcoin** con stessa energia

Basata sull'articolo:

**Renewable energy and cryptocurrency: A dual approach to economic viability and environmental sustainability**
**[Ali Hakimi, Mohammad-Mahdi Pazuki, Mohsen Salimi, Majid Amidpour]**

[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pv-mining-sim.streamlit.app)

## Risultati Chiave simulatore

| Scenario        | Payback    | CO₂ Evitata/anno   |
| --------------- | ---------- | ------------------ |
| Vendita Energia | 6 anni     | ------------------ |
| Mining BTC      | **3 anni** | **50.000 t**       |

## Setup (bash)

# 1. Clone/scarica

git clone [link repo](https://github.com/danieleamato99/pv-mining-sim) pv-mining-sim

cd pv-mining-sim

# 2. Ambiente virtuale

python -m venv venv

source venv/bin/activate

# 3. Installa

pip install -r requirements.txt

# 4. Dati (scarica dai link o tuoi file)

mkdir data

Copia: pv_production.csv, BTC-USD.csv, difficulty.json, hash-rate.json in data/

# 5. Avvia

streamlit run src/main.py
