# e-voting-system

Krótki opis projektu oraz jego celu.

## Spis treści

- [Opis](#opis)
- [Funkcje](#funkcje)
- [Technologie](#technologie)
- [Instalacja](#instalacja)
- [Użytkowanie](#użytkowanie)
- [Wkład](#wkład)
- [Licencja](#licencja)

## Opis

Opis projektu, jego cel oraz co chcesz osiągnąć. Możesz również dodać informacje o tym, dlaczego projekt jest ważny i jakie problemy rozwiązuje.

## Funkcje

- Funkcja 1
- Funkcja 2
- Funkcja 3

## Technologie

- Technologia 1 (np. język programowania, framework)
- Technologia 2
- Technologia 3

## Instalacja

Poniżej znajduje się konfiguracja projektu z użyciem `uv`. Polecenie to służy do zarządzania wersją Pythona, środowiskiem wirtualnym oraz zależnościami projektu.

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/użytkownik/nazwa-projektu.git
cd nazwa-projektu
```

### 2. Instalacja `uv`

#### Linux / macOS

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

#### Windows

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Sprawdzenie:
```bash
uv --version
```

### 3. Utworzenie środowiska wirtualnego

```bash
uv venv
```

Domyślnie zostanie utworzony katalog `.venv` w katalogu projektu.

### 4. Aktywacja środowiska wirtualnego

#### Linux / macOS

```bash
source .venv/bin/activate
```

#### Windows

```cmd
.venv\Scripts\activate.bat
```

### 5. Instalacja wszystkich bibliotek

Jeżeli projekt zawiera plik `pyproject.toml`, zainstaluj zależności poleceniem:

```bash
uv sync
```

### 6. Uruchomienie projektu

Po aktywowaniu środowiska wirtualnego uruchom aplikację zgodnie z jej punktem wejścia, np.:

```bash
python /src/main.py
```

Możesz też uruchamiać komendy bez ręcznej aktywacji środowiska przez `uv run`, np.:

```bash
uv run python /srv/main.py
```