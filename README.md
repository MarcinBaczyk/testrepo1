# testrepo1

Skrypt `rdn_prices.py` pobiera historyczne ceny energii elektrycznej z Rynku Dnia Następnego (RDN)
przez oficjalne API PSE i generuje wykres liniowy z ostatnich 30 dni.

## Źródło danych

Domyślnie używany jest endpoint API PSE dla RDN:
`https://api.pse.pl/api/market-data/price-dam`.
Jeśli API zmieni adres lub wymaga innego endpointu, użyj parametru `--pse-url`
(albo zmiennej środowiskowej `PSE_DAM_URL`).

## Uruchomienie

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python rdn_prices.py --days 30 --output rdn_prices.png
```

Opcjonalnie:
- `--show` – wyświetla wykres w oknie.
- `RDN_DAYS` – domyślna liczba dni (np. `export RDN_DAYS=14`).
- `RDN_OUTPUT` – domyślna ścieżka zapisu.

Wynikowy wykres zostanie zapisany w pliku PNG.
