"""
src/config/constants.py
Centralizza tutti i parametri del modello:
- da paper (es. CAPEX, OPEX, CO2 evitata)
- da dati (path file CSV/JSON)
- calcoli derivati (hashrate, reward halving).

Usa dataclass frozen per riproducibilità + costanti legacy per compatibilità.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict

# -----------------------------
# Path progetto / data
# -----------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]  # root del progetto
DATA_DIR = ROOT_DIR / "data"


def _resolve_data_file(*candidates: str) -> str:
    """
    Trova il primo file esistente tra i possibili nomi in /data.
    Fallback sul primo candidato se nessuno trovato.
    """
    for name in candidates:
        p = DATA_DIR / name
        if p.exists():
            return str(p)
    return str(DATA_DIR / candidates[0])


# Nomi file dati (tollera variazioni nei nomi).
PVFILE = _resolve_data_file("pvproduction.csv", "pv_production.csv")
BTCFILE = _resolve_data_file("BTC-USD.csv", "btc-usd.csv", "BTC_USD.csv")
HASHFILE = _resolve_data_file("hash-rate.json", "hash_rate.json")
DIFFICULTYFILE = _resolve_data_file("difficulty.json")


# -----------------------------
# Parametri modello (da paper + calcoli derivati)
# -----------------------------
@dataclass
class PVSystemParams:
    """Parametri impianto FV (Table 5-7 paper)."""

    potenza_mwp: float = 50.91
    energia_base_2020_mwh: float = 80890.0
    degrado_annuo: float = 0.0043
    opex_annuo_usd: float = 902_263.0
    capex_totale_usd: float = 42_000_000.0


@dataclass
class EnergyMarketParams:
    """Parametri mercato energia."""

    prezzo_vendita_usd_kwh: float = 0.094


@dataclass
class MiningParams:
    """
    Parametri farm mining (tabelle 2,8 paper).
    Hashrate derivato da potenza / efficienza miner.
    """

    potenza_farm_mw: float = 9.3
    pue: float = 1.1
    efficienza_j_per_th: float = 39.5

    consumo_annuo_mwh: float = 80_766.0
    seconds_per_year: float = 365.25 * 24 * 3600

    @property
    def hashrate_sistema_hs(self) -> float:
        # Calcolo: Potenza netta / efficienza → TH/s → *1e12 → H/s.
        potenza_miners_w = (self.potenza_farm_mw * 1e6) / self.pue
        th_s = potenza_miners_w / self.efficienza_j_per_th
        return th_s * 1e12


@dataclass
class EnvironmentalParams:
    """Emissioni evitate (paper)."""

    co2_evitata_ton_anno: float = 50_000.0

    # Alias per codice legacy.
    @property
    def co2_evitata_ton_annue(self) -> float:
        return self.co2_evitata_ton_anno

    @property
    def co2evitatatonanno(self) -> float:
        return self.co2_evitata_ton_anno


@dataclass
class SimulationParams:
    """Parametri intervallo simulazione."""

    start_year: int = 2020
    end_year: int = 2045

    @property
    def startyear(self) -> int:
        return self.start_year

    @property
    def endyear(self) -> int:
        return self.end_year


# Istanza globali (thread-safe per Streamlit).
PVPARAMS = PVSystemParams()
ENERGYPARAMS = EnergyMarketParams()
MININGPARAMS = MiningParams()
ENVPARAMS = EnvironmentalParams()
SIMPARAMS = SimulationParams()

# -----------------------------
# Costanti legacy (per moduli vecchi)
# -----------------------------
CAPEX = float(PVPARAMS.capex_totale_usd)
OPEXANNUO = float(PVPARAMS.opex_annuo_usd)
PREZZOENERGIA = float(ENERGYPARAMS.prezzo_vendita_usd_kwh)
CO2EVITATAANNUA = float(ENVPARAMS.co2_evitata_ton_anno)

DEGRADOFV = float(PVPARAMS.degrado_annuo)
POTENZAFVMW = float(PVPARAMS.potenza_mwp)
ENERGIABASE2020 = float(PVPARAMS.energia_base_2020_mwh)

HASHRATESISTEMA = float(MININGPARAMS.hashrate_sistema_hs)
CONSUMO_MINING_ANNUO_MWH = float(MININGPARAMS.consumo_annuo_mwh)
SECONDS_PER_YEAR = float(MININGPARAMS.seconds_per_year)

START_YEAR = int(SIMPARAMS.start_year)
END_YEAR = int(SIMPARAMS.end_year)

# -----------------------------
# Bitcoin reward (gestisce halving 2020 con media annua)
# -----------------------------
HALVING_REWARD_BY_START_YEAR: Dict[int, float] = {
    2009: 50.0,
    2012: 25.0,
    2016: 12.5,
    2020: 6.25,
    2024: 3.125,
}


def getblockreward(year: int) -> float:
    """Alias legacy → reward medio annuo."""
    return get_block_reward(year)


def getblockreward_constant(year: int) -> float:
    """Reward costante per epoca (scalini)."""
    starts = sorted(HALVING_REWARD_BY_START_YEAR.keys())
    chosen_start = starts[0]
    for s in starts:
        if year >= s:
            chosen_start = s
        else:
            break
    return float(HALVING_REWARD_BY_START_YEAR[chosen_start])


def get_average_block_reward(year: int) -> float:
    """
    Reward medio annuo (per 2020: media pre/post halving).
    Halving 11/05/2020 → ~133 gg 12.5 BTC + 233 gg 6.25 BTC.
    """
    if year != 2020:
        return getblockreward_constant(year)

    halving_day = date(2020, 5, 11)
    year_start = date(2020, 1, 1)
    year_end = date(2021, 1, 1)

    total_days = (year_end - year_start).days  # 366 (bisestile)
    days_before = (halving_day - year_start).days
    days_after = total_days - days_before

    reward_before = 12.5
    reward_after = 6.25
    return float((reward_before * days_before + reward_after * days_after) / total_days)


# Alias per compatibilità.
PV_PARAMS = PVPARAMS
ENERGY_PARAMS = ENERGYPARAMS
MINING_PARAMS = MININGPARAMS
ENV_PARAMS = ENVPARAMS
SIM_PARAMS = SIMPARAMS


def get_block_reward(year: int) -> float:
    """Reward medio annuo (default per simulazioni annuali)."""
    return get_average_block_reward(year)


__all__ = [
    "PVFILE",
    "BTCFILE",
    "HASHFILE",
    "DIFFICULTYFILE",
    "PVPARAMS",
    "ENERGYPARAMS",
    "MININGPARAMS",
    "ENVPARAMS",
    "SIMPARAMS",
    "CAPEX",
    "OPEXANNUO",
    "PREZZOENERGIA",
    "CO2EVITATAANNUA",
    "DEGRADOFV",
    "POTENZAFVMW",
    "ENERGIABASE2020",
    "HASHRATESISTEMA",
    "CONSUMO_MINING_ANNUO_MWH",
    "SECONDS_PER_YEAR",
    "START_YEAR",
    "END_YEAR",
    "getblockreward",
    "getblockreward_constant",
    "get_average_block_reward",
    "PV_PARAMS",
    "ENERGY_PARAMS",
    "MINING_PARAMS",
    "ENV_PARAMS",
    "SIM_PARAMS",
    "get_block_reward",
]
