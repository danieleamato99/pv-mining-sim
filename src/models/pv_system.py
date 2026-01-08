"""
src/models/pv_system.py
Simulatore impianto FV 50.91 MWp (tabelle 3-5 paper).
Produzione: E_2020 * (1 - 0.0043)^(anno-2020).
"""

from typing import List
from dataclasses import dataclass

import pandas as pd

from src.config import constants as const
from src.data.loader import DataFactory


@dataclass
class PVProductionYear:
    """Record output annuo (colonne tabella vendita energia)."""

    anno: int
    energia_mwh: float
    ricavi_vendita_usd: float
    opex_usd: float
    cashflow_annuo_usd: float
    cashflow_cum_usd: float


class PVSystem:
    """
    Scenario vendita energia alla rete.
    Degrado lineare 0.43%/anno (da paper).
    """

    def __init__(self, data_loader: DataFactory):
        self.data = data_loader.load_all()
        self.e_2020 = self.data["pv_2020_total"]  # Baseline 80890 MWh.
        self.reset_simulation()

    def reset_simulation(self) -> None:
        """Reset per nuova run (CAPEX iniziale)."""
        self._cash_cum = -const.PV_PARAMS.capex_totale_usd
        self._productions: List[PVProductionYear] = []

    def simulate_production(self, anno: int) -> float:
        """
        E_n = E_2020 * (1 - degrado)^(n-2020).
        Degrado: 0.43%/anno lineare.
        """
        years_passed = anno - const.SIM_PARAMS.start_year
        degrado_factor = (1 - const.PV_PARAMS.degrado_annuo) ** years_passed
        return self.e_2020 * degrado_factor

    def calculate_yearly_cashflow(
        self, anno: int, energia_mwh: float
    ) -> PVProductionYear:
        """
        Ricavi: energia (MWh) → kWh * prezzo rete (0.094 USD/kWh).
        CF = ricavi - OPEX annuo.
        """
        ricavi = energia_mwh * 1000 * const.ENERGYPARAMS.prezzo_vendita_usd_kwh
        cf_annuo = ricavi - const.PV_PARAMS.opex_annuo_usd
        self._cash_cum += cf_annuo

        record = PVProductionYear(
            anno=anno,
            energia_mwh=round(energia_mwh, 1),
            ricavi_vendita_usd=round(ricavi, 0),
            opex_usd=const.PV_PARAMS.opex_annuo_usd,
            cashflow_annuo_usd=round(cf_annuo, 0),
            cashflow_cum_usd=round(self._cash_cum, 0),
        )
        self._productions.append(record)
        return record

    def run_full_simulation(self) -> List[PVProductionYear]:
        """Simula 2020-2045 e salva record interni."""
        self.reset_simulation()
        for anno in range(const.SIM_PARAMS.start_year, const.SIM_PARAMS.end_year + 1):
            energia = self.simulate_production(anno)
            self.calculate_yearly_cashflow(anno, energia)
        return self._productions

    def get_dataframe(self) -> pd.DataFrame:
        """Tabella risultati (per UI e tabelle Markdown)."""
        if not self._productions:
            raise ValueError("Run prima run_full_simulation()")
        return pd.DataFrame([p.__dict__ for p in self._productions])

    def find_payback_year(self) -> float:
        """Primo anno CF cumulativo positivo."""
        df = self.get_dataframe()
        positive_cf = df[df["cashflow_cum_usd"] > 0]
        return positive_cf["anno"].iloc[0] if not positive_cf.empty else float("inf")
