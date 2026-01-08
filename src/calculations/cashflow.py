"""
src/calculations/cashflow.py
Analisi del cash flow: vendita energia FV vs mining Bitcoin.
"""

from typing import Dict, Tuple

import pandas as pd
import plotly.graph_objects as go

from src.data.loader import DataFactory
from src.models.pv_system import PVSystem
from src.models.mining_farm import MiningFarm
from src.config import constants as const


class CashflowAnalyzer:
    """Gestisce il confronto economico tra i due scenari (FV vs mining)."""

    def __init__(self) -> None:
        # Inizializzo factory dati e i due modelli di simulazione.
        self.data_factory = DataFactory()
        self.pv_system = PVSystem(self.data_factory)
        self.mining_farm = MiningFarm(self.data_factory)

    def run_complete_analysis(self) -> Tuple[Dict[str, pd.DataFrame], Dict[str, float]]:
        """
        Esegue la simulazione su 25 anni e restituisce:
        - dfs: tabelle annuali per vendita e mining
        - metrics: payback per i due scenari
        """
        # Scenario vendita energia alla rete.
        pv_results = self.pv_system.run_full_simulation()
        df_vendita = self.pv_system.get_dataframe()

        # Scenario mining: usa la stessa energia FV come input.
        self.mining_farm.run_full_simulation(pv_results)
        df_mining = self.mining_farm.get_dataframe()

        dfs = {"vendita": df_vendita, "mining": df_mining}
        metrics = {
            "payback_vendita": self.pv_system.find_payback_year(),
            "payback_mining": self.mining_farm.find_payback_year(),
        }
        return dfs, metrics

    def create_payback_chart(self, dfs: Dict[str, pd.DataFrame]) -> go.Figure:
        """
        Crea il grafico del cash flow cumulativo per i due scenari
        con la linea orizzontale a 0 per evidenziare il payback.
        """
        fig = go.Figure()

        # Curva: vendita energia FV.
        df_v = dfs["vendita"]
        fig.add_trace(
            go.Scatter(
                x=df_v["anno"],
                y=df_v["cashflow_cum_usd"],
                name="Vendita Energia",
                line=dict(color="blue", width=3),
            )
        )

        # Curva: mining Bitcoin con stessa energia FV.
        df_m = dfs["mining"]
        fig.add_trace(
            go.Scatter(
                x=df_m["anno"],
                y=df_m["cashflow_cum_usd"],
                name="Mining Bitcoin",
                line=dict(color="orange", width=3),
            )
        )

        # Asse di riferimento per il rientro dell'investimento.
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        fig.update_layout(
            title="Payback: Mining vs Vendita Energia FV",
            xaxis_title="Anno (2020-2045)",
            yaxis_title="Cash Flow Cumulativo (USD)",
            template="plotly_white",
            width=900,
            height=500,
        )
        return fig

    def create_co2_chart(self) -> go.Figure:
        """
        Crea il grafico della CO₂ evitata cumulata, assumendo valore annuo costante
        (semplificazione coerente con l'astrazione usata nella tesi).
        """
        anni = list(range(const.SIM_PARAMS.start_year, const.SIM_PARAMS.end_year + 1))
        # Cumulata semplice: anno i-esimo = i * CO₂ evitata/anno.
        co2_cum = [
            const.ENV_PARAMS.co2_evitata_ton_anno * i for i in range(1, len(anni) + 1)
        ]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=anni,
                y=co2_cum,
                name="CO₂ Evitata Cumulata",
                line=dict(color="green", width=4),
            )
        )
        fig.update_layout(
            title="CO₂ Evitata: 50.000 t/anno × 25 anni",
            xaxis_title="Anno",
            yaxis_title="Tonnellate CO₂",
        )
        return fig
