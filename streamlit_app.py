"""
Main della web app Streamlit per la tesi.
"""

from src.utils.visualizer import StreamlitVisualizer


def main() -> None:
    """Istanzia il visualizzatore e avvia l'app."""
    app = StreamlitVisualizer()
    app.run()


if __name__ == "__main__":
    # Permette di eseguire il file sia come script sia come modulo importabile.
    main()
