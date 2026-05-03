# System E-Voting z szyfrowaniem homomorficznym

## Opis projektu

Projekt stanowi implementację systemu głosowania elektronicznego działającego w środowisku terminalowym (CLI), zaprojektowanego z uwzględnieniem wysokich wymagań w zakresie prywatności, integralności danych oraz audytowalności procesu wyborczego.

Kluczowym elementem systemu jest wykorzystanie kryptografii homomorficznej (schemat Pailliera), umożliwiającej przeprowadzanie operacji na zaszyfrowanych danych. Dzięki temu możliwe jest zliczanie głosów bez konieczności ujawniania pojedynczych decyzji wyborców.

## Funkcjonalności

- szyfrowanie głosów przy użyciu kryptosystemu Pailliera
- homomorficzna agregacja głosów
- interfejs użytkownika w trybie CLI
- trwałe przechowywanie danych w formacie JSON
- obsługa listy uprawnionych wyborców
- mechanizmy zapobiegające wielokrotnemu głosowaniu
- możliwość definiowania wielu pytań oraz opcji odpowiedzi
- obsługa różnych typów głosowań:
  - wybory (wiele opcji do wyboru)
  - referendum (pytania typu tak/nie)
- rejestrowanie zdarzeń w logach audytowych
- zestaw testów jednostkowych i integracyjnych

## Struktura projektu

```text
e-voting-system/
├── src/                # kod źródłowy aplikacji
├── data/               # dane wejściowe (wyborcy, pytania, głosy)
├── scripts/            # skrypty pomocnicze
├── tests/              # testy
├── pyproject.toml      # konfiguracja projektu (uv)
├── uv.lock             # blokada zależności
```

## Wymagania

- Python w wersji 3.12 lub nowszej
- narzędzie `uv` do zarządzania środowiskiem i zależnościami

## Instalacja i uruchomienie

### Instalacja narzędzia uv

Jeżeli narzędzie `uv` nie jest zainstalowane:

```bash
pip install uv
```

lub:

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

### Klonowanie repozytorium

```bash
git clone <repo-url>
cd e-voting-system
```

### Instalacja zależności

```bash
uv sync
```

### Generowanie kluczy kryptograficznych

```bash
uv run python scripts/generate_keys.py
```

### Uruchomienie aplikacji

```bash
uv run python -m src.main
```

Opcjonalnie (tryb demonstracyjny):

```bash
uv run python scripts/run_demo.py
```

## Typy obsługiwanych głosowań

System umożliwia przeprowadzanie różnych form głosowań.

### Wybory

- wiele możliwych opcji (np. kandydaci)
- wyborca wskazuje jedną z dostępnych opcji
- konfiguracja w plikach danych, np. `questions_election.json`

### Referendum

- pytania o charakterze binarnym (tak/nie)
- uproszczony model odpowiedzi
- konfiguracja w plikach danych, np. `questions_referendum.json`

## Przebieg procesu głosowania

1. weryfikacja uprawnień wyborcy
2. prezentacja pytań lub listy kandydatów
3. oddanie głosu i jego natychmiastowe zaszyfrowanie
4. zapis zaszyfrowanego głosu w systemie
5. agregacja głosów przy użyciu własności homomorficznych
6. odszyfrowanie wyłącznie wyniku końcowego

## Testy

Uruchomienie testów:

```bash
uv run pytest
```

## Aspekty bezpieczeństwa

- brak przechowywania głosów w postaci jawnej
- szyfrowanie danych na etapie oddawania głosu
- brak możliwości odtworzenia pojedynczych decyzji wyborców
- możliwość audytu procesu bez naruszenia prywatności

## Uwagi

Projekt ma charakter demonstracyjny i edukacyjny. Nie jest przeznaczony do wykorzystania w rzeczywistych systemach wyborczych bez przeprowadzenia dodatkowych analiz bezpieczeństwa, wdrożenia infrastruktury kryptograficznej oraz spełnienia wymogów formalnych i prawnych.

## Licencja

Szczegóły znajdują się w pliku `LICENSE`.
