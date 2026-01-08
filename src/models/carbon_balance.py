"""
src/models/carbon_balance.py
Calcolo emissioni CO₂ evitate (semplice modello lineare).
"""

from src.config import constants as const


class CarbonBalance:
    """
    Bilancio carbonio: CO₂ evitata usando FV per mining invece di rete.
    Semplificazione lineare (50k t/anno costante, come paper).
    """

    @staticmethod
    def annual_co2() -> float:
        """CO₂ evitata annua (tonnellate)."""
        return const.ENV_PARAMS.co2_evitata_ton_anno

    @staticmethod
    def cumulative(years: int) -> float:
        """CO₂ cumulata su N anni (lineare, no degrado emissioni)."""
        return years * const.ENV_PARAMS.co2_evitata_ton_anno
