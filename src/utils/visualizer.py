"""
src/utils/visualizer.py
Dashboard Streamlit: tabelle, grafici e parametri interattivi.
Session state per modificare live CAPEX/OPEX senza ricaricare.
"""

from typing import Dict, Tuple

import streamlit as st
import pandas as pd

from src.calculations.cashflow import CashflowAnalyzer
from src.config import constants as const


class StreamlitVisualizer:
    """UI tesi: sidebar parametri + risultati."""

    def __init__(self):
        st.set_page_config(page_title="PV vs Mining", layout="wide")
        self.analyzer = CashflowAnalyzer()
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Inizializza parametri editabili."""
        defaults = {
            "capex": const.PV_PARAMS.capex_totale_usd,
            "opex": const.PV_PARAMS.opex_annuo_usd,
            "prezzo_kwh": const.ENERGYPARAMS.prezzo_vendita_usd_kwh,
            "co2_ton": const.ENV_PARAMS.co2_evitata_ton_anno,
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def render_sidebar_params(self) -> Dict[str, float]:
        """Sidebar: input parametri -> aggiorna session state."""
        st.sidebar.header("Parametri configurabili")

        col1, col2 = st.sidebar.columns(2)
        with col1:
            capex = st.number_input(
                "CAPEX $", value=int(st.session_state.capex), step=100000
            )
            opex = st.number_input(
                "OPEX $/anno", value=int(st.session_state.opex), step=10000
            )
        with col2:
            prezzo = st.number_input(
                "$/kWh", value=float(st.session_state.prezzo_kwh), step=0.001
            )
            co2 = st.number_input(
                "CO₂ t/anno", value=int(st.session_state.co2_ton), step=1000
            )

        # Salva in session (persistente tra rerun Streamlit).
        st.session_state.capex = capex
        st.session_state.opex = opex
        st.session_state.prezzo_kwh = prezzo
        st.session_state.co2_ton = co2

        return {
            "capex_totale_usd": capex,
            "opex_annuo_usd": opex,
            "prezzo_vendita_usd_kwh": prezzo,
            "co2_evitata_ton_anno": co2,
        }

    def get_params(self) -> Dict[str, float]:
        """Parametri correnti da session state."""
        return {
            "capex_totale_usd": st.session_state.capex,
            "opex_annuo_usd": st.session_state.opex,
            "prezzo_vendita_usd_kwh": st.session_state.prezzo_kwh,
            "co2_evitata_ton_anno": st.session_state.co2_ton,
        }

    def render_header(self) -> None:
        """Titolo e intro."""
        st.title("PV 50.91 MWp vs Bitcoin Mining")
        st.markdown("**Simulazione economica/ambientale 2020-2045**")

    def render_results(
        self, results: Tuple[Dict[str, pd.DataFrame], Dict[str, float]]
    ) -> None:
        """Tabelle CF, grafici payback/CO₂, KPI."""
        dfs, metrics = results

        # Tabelle cash flow (rename colonne per UI).
        pv_cols = {
            "anno": "Anno",
            "energia_mwh": "Energia immessa rete (MWh)",
            "ricavi_vendita_usd": "Ricavi vendita ($)",
            "opex_usd": "OPEX ($/anno)",
            "cashflow_annuo_usd": "CF annuo ($)",
        }
        df_pv_ui = dfs["vendita"].rename(columns=pv_cols)

        mining_cols = {
            "anno": "Anno",
            "energia_usata_mwh": "Energia mining (MWh)",
            "btc_minati": "BTC minati",
            "prezzo_btc_usd": "Prezzo BTC ($)",
            "ricavi_usd": "Ricavi ($)",
            "opex_usd": "OPEX ($/anno)",
            "cashflow_annuo_usd": "CF annuo ($)",
        }
        df_mining_ui = dfs["mining"].rename(columns=mining_cols)

        st.header("Cash Flow Annuale")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Vendita energia FV")
            st.dataframe(df_pv_ui, use_container_width=True)
        with col2:
            st.subheader("Mining Bitcoin")
            st.dataframe(df_mining_ui, use_container_width=True)

        # Grafico payback principale.
        st.header("Analisi Payback")
        fig_payback = self.analyzer.create_payback_chart(dfs)
        st.plotly_chart(fig_payback, use_container_width=True)

        # KPI.
        col_k1, col_k2 = st.columns(2)
        col_k1.metric("Payback Mining", f"{metrics['payback_mining']}")
        col_k2.metric("Payback Vendita", f"{metrics['payback_vendita']}")

        # CO₂.
        st.header("CO₂ Evitata")
        fig_co2 = self.analyzer.create_co2_chart()
        st.plotly_chart(fig_co2, use_container_width=True)

    def render_methodology(self) -> None:
        """Riferimenti e formule (expander per prof)."""
        with st.expander("Metodologia e fonti"):
            st.markdown(
                """ 
                #### Riferimenti per formule e dati   
                Le formule, i parametri tecnici e i dati di riferimento utilizzati 
                per costruire il modello di simulazione (sistema PV, mining farm e 
                impostazione economica/energetica) sono tratti e adattati dal paper 
                *Renewable energy and cryptocurrency: A dual approach to economic viability 
                and environmental sustainability* di Ali Hakimi, Mohammad-Mahdi Pazuki, 
                Mohsen Salimi e Majid Amidpour. 
                """
            )

    def run(self) -> None:
        """Main dashboard flow."""
        self.render_header()
        self.render_sidebar_params()

        if st.button("Esegui simulazione 25 anni", type="primary"):
            with st.spinner("Calcolo cash flow..."):
                results = self.analyzer.run_complete_analysis()
            self.render_results(results)

        self.render_methodology()
