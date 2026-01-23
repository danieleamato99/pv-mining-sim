"""
src/data/loader.py
Carica i dataset storici e prepara le serie annuali per la simulazione.
Forward-fill per anni futuri (assunzione conservativa).
"""

import json
import logging
from typing import Dict, Tuple, Any

import pandas as pd

from src.config import constants as const

logger = logging.getLogger(__name__)


class PVDataLoader:
    """Carica produzione FV 2020 mensile da CSV (tabella 7 paper)."""

    @staticmethod
    def load() -> Tuple[pd.DataFrame, float]:
        """Legge CSV e valida totale 80890 MWh."""
        df = pd.read_csv("data/pv_production.csv")
        # Assumiamo colonna "energy_ac_mwh" dal dataset pv_production.csv
        total = df["energy_ac_mwh"].sum()
        if abs(total - const.PV_PARAMS.energia_base_2020_mwh) > 809:
            logger.warning("Totale PV mismatch paper (atteso 80890 MWh)")
        logger.info("PV 2020 caricato: %.0f MWh", total)
        return df, float(total)


class BTCPriceLoader:
    """Calcola prezzi BTC medi annuali da CSV."""

    @staticmethod
    def load() -> Dict[int, float]:
        """Media Close USD per anno (da 2013-2026)."""
        df = pd.read_csv("data/BTC-USD.csv")
        df.columns = [c.strip().lower() for c in df.columns]

        df["snapped_at"] = pd.to_datetime(df["snapped_at"], utc=True, errors="coerce")
        df["year"] = pd.DatetimeIndex(df["snapped_at"]).year
        df["price"] = pd.to_numeric(df["price"], errors="coerce")

        return df.groupby("year")["price"].mean().to_dict()


class TimeseriesLoader:
    """Parser generico per JSON timeseries (difficulty/hashrate)."""

    @staticmethod
    def _parse_year_series(data: list[dict]) -> Dict[int, float]:
        """Converte lista {x:ts_ms, y:value} → media annua."""
        records = []
        for item in data:
            ts_ms = item["x"]
            value = item["y"]
            year = pd.to_datetime(ts_ms, unit="ms").year
            records.append({"year": year, "value": value})
        df = pd.DataFrame(records)
        return df.groupby("year")["value"].mean().to_dict()

    @staticmethod
    def load_difficulty() -> Dict[int, float]:
        """Difficulty network media annua."""
        with open("data/difficulty.json", encoding="utf-8") as f:
            data = json.load(f)["difficulty"]
        result = TimeseriesLoader._parse_year_series(data)
        logger.info("Difficulty caricata: %d anni", len(result))
        return result

    @staticmethod
    def load_hashrate() -> Dict[int, float]:
        """Network hashrate medio annuo."""
        with open("data/hash-rate.json", encoding="utf-8") as f:
            data = json.load(f)["hash-rate"]
        result = TimeseriesLoader._parse_year_series(data)
        logger.info("Hashrate caricato: %d anni", len(result))
        return result


class DataFactory:
    """Factory per tutti i dati della simulazione."""

    @classmethod
    def load_all(cls) -> Dict[str, Any]:
        """
        Carica dataset + forward-fill anni 2025-2045 con ultimi valori noti.
        (Conservativo: no previsioni ML).
        """
        data: Dict[str, Any] = {}
        data["pv_monthly"], data["pv_2020_total"] = PVDataLoader.load()
        data["btc_prices"] = BTCPriceLoader.load()
        data["difficulty"] = TimeseriesLoader.load_difficulty()
        data["network_hr"] = TimeseriesLoader.load_hashrate()

        # Estendi serie storiche a 2045.
        all_keys = ["btc_prices", "difficulty", "network_hr"]
        for y in range(const.SIM_PARAMS.start_year, const.SIM_PARAMS.end_year + 1):
            for k in all_keys:
                if y not in data[k]:
                    last_known = max(data[k].keys())
                    data[k][y] = data[k][last_known]

        logger.info("✅ DataFactory: simulazione pronta (2020-2045)")
        return data
