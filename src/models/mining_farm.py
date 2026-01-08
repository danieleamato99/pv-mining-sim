"""
src/models/mining_farm.py
Modello simulazione farm mining Bitcoin (159 Antminer S17).
Formula BTC minati: HR * TP * NRR / (ND * 2^32).
"""

from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd

from src.config import constants as const
from src.config.constants import get_block_reward
from src.data.loader import DataFactory


@dataclass
class MiningYear:
    """Record annuo per mining (colonne tabella output)."""

    anno: int
    energia_usata_mwh: float
    btc_minati: float
    prezzo_btc_usd: float
    ricavi_usd: float
    opex_usd: float
    cashflow_annuo_usd: float
    cashflow_cum_usd: float


class MiningFarm:
    """
    Simula cash flow mining usando energia FV disponibile.
    Energia usata = min(produzione FV, consumo farm costante 80k MWh/anno).
    """

    def __init__(self, data_loader: DataFactory):
        self.data = data_loader.load_all()
        self.hashrate_sistema = const.MINING_PARAMS.hashrate_sistema_hs
        self.tempo_sec_anno = const.MINING_PARAMS.seconds_per_year
        self.consumo_max_mwh = const.MINING_PARAMS.consumo_annuo_mwh
        self.reset_simulation()

    def reset_simulation(self) -> None:
        """Reset stato (CAPEX iniziale negativo)."""
        self._cash_cum: float = -const.PV_PARAMS.capex_totale_usd
        self._years: List[MiningYear] = []

    def calculate_btc_mined(
        self, anno: int, energia_pv_mwh: float
    ) -> Tuple[float, float]:
        """
        Formula dal paper: BTC = HR * TP * NRR / (ND * 2^32).
        Energia usata limitata dalla produzione FV.
        """
        nd = self.data["difficulty"][anno]
        nrr = get_block_reward(anno)

        # BTC teorici (indipendente da energia, limitati dopo).
        btc_teorici = self.hashrate_sistema * self.tempo_sec_anno * nrr / (nd * (2**32))
        energia_usata = min(self.consumo_max_mwh, energia_pv_mwh)
        btc_minati = btc_teorici  # Assumiamo efficienza 100% (semplificazione).
        return btc_minati, energia_usata

    def calculate_yearly_cashflow(self, anno: int, energia_pv_mwh: float) -> MiningYear:
        """Calcola CF annuo da BTC minati * prezzo BTC - OPEX."""
        btc_minati, energia_usata = self.calculate_btc_mined(anno, energia_pv_mwh)
        prezzo_btc = self.data["btc_prices"][anno]
        ricavi = btc_minati * prezzo_btc
        cf_annuo = ricavi - const.PV_PARAMS.opex_annuo_usd
        self._cash_cum += cf_annuo

        return MiningYear(
            anno=anno,
            energia_usata_mwh=round(energia_usata, 1),
            btc_minati=round(btc_minati, 6),
            prezzo_btc_usd=round(prezzo_btc, 0),
            ricavi_usd=round(ricavi, 0),
            opex_usd=const.PV_PARAMS.opex_annuo_usd,
            cashflow_annuo_usd=round(cf_annuo, 0),
            cashflow_cum_usd=round(self._cash_cum, 0),
        )

    def run_full_simulation(self, pv_productions: List) -> List[MiningYear]:
        """
        Simula 25 anni: per ogni anno usa energia FV disponibile.
        pv_productions: lista oggetti produzione FV annua.
        """
        self.reset_simulation()
        for i, anno in enumerate(
            range(const.SIM_PARAMS.start_year, const.SIM_PARAMS.end_year + 1)
        ):
            energia_pv = pv_productions[i].energia_mwh
            year_record = self.calculate_yearly_cashflow(anno, energia_pv)
            self._years.append(year_record)
        return self._years

    def get_dataframe(self) -> pd.DataFrame:
        """Restituisce tabella risultati (per UI/grafici)."""
        return pd.DataFrame([y.__dict__ for y in self._years])

    def find_payback_year(self) -> float:
        """Primo anno con CF cumulativo > 0 (o inf se mai)."""
        df = self.get_dataframe()
        positive = df[df["cashflow_cum_usd"] > 0]
        return positive["anno"].iloc[0] if len(positive) > 0 else float("inf")
