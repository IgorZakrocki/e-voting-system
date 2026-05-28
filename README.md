# Secure E-Voting System

Terminalowy system głosowania elektronicznego wykorzystujący szyfrowanie homomorficzne Pailliera. Projekt obsługuje lokalne głosowanie w interfejsie TUI/CLI, tryb klient-serwer w sieci lokalnej, zapis danych w plikach JSON oraz automatyczne testy logiki głosowania, kryptografii i warstwy pomocniczej.

> Projekt ma charakter demonstracyjny i edukacyjny. Nie powinien być używany jako produkcyjny system wyborczy bez pełnego audytu kryptograficznego, infrastrukturalnego i prawnego.

## Spis treści

- [Najważniejsze funkcje](#najważniejsze-funkcje)
- [Stos technologiczny](#stos-technologiczny)
- [Struktura projektu](#struktura-projektu)
- [Instalacja](#instalacja)
- [Przygotowanie danych i kluczy](#przygotowanie-danych-i-kluczy)
- [Uruchamianie aplikacji](#uruchamianie-aplikacji)
- [Format danych](#format-danych)
- [Przebieg głosowania](#przebieg-głosowania)
- [Testy](#testy)
- [Bezpieczeństwo i ograniczenia](#bezpieczeństwo-i-ograniczenia)

## Najważniejsze funkcje

- szyfrowanie pojedynczych głosów za pomocą kryptosystemu Pailliera,
- homomorficzne sumowanie zaszyfrowanych głosów bez ujawniania decyzji pojedynczego wyborcy,
- obsługa referendum oraz wyborów kandydackich,
- terminalowy interfejs użytkownika oparty o `curses`,
- lokalny tryb głosowania oraz tryb klient-serwer w sieci lokalnej,
- automatyczne wykrywanie serwera przez klienta z wykorzystaniem UDP broadcast,
- trwałe repozytoria JSON dla wyborców, pytań, głosów, wyników i audytu,
- walidacja wyborcy na podstawie imienia i nazwiska, końcówki PESEL oraz numeru dokumentu,
- mechanizmy blokujące ponowne oddanie głosu,
- log audytowy zdarzeń głosowania i zliczania wyników,
- skrypty serwisowe do czyszczenia środowiska i regeneracji kluczy,
- zestaw testów jednostkowych i integracyjnych obejmujący główne ścieżki systemu.

## Stos technologiczny

| Obszar | Technologia |
|---|---|
| Język | Python `>=3.11` |
| Kryptografia | `phe` — implementacja Pailliera |
| Interfejs terminalowy | `curses` |
| Format danych | JSON |
| Testy | `pytest` |
| Zarządzanie zależnościami | `uv` |

## Struktura projektu

```text
e-voting-system/
├── data/
│   ├── voters.json                 # lista wyborców
│   ├── questions_referendum.json   # pytania referendalne
│   └── questions_election.json     # lista kandydatów / pytań wyborczych
├── keys/
│   ├── public_key.json             # klucz publiczny Pailliera, generowany skryptem
│   └── private_key.json            # klucz prywatny Pailliera, generowany skryptem
├── scripts/
│   ├── clean_system.py             # usuwa dane runtime i resetuje status wyborców
│   └── prepare_system.py           # czyści runtime, resetuje wyborców i regeneruje klucze
├── src/
│   ├── cli.py                      # interfejs TUI/CLI i obsługa formularzy
│   ├── crypto.py                   # szyfrowanie, deszyfrowanie, serializacja i klucze
│   ├── exceptions.py               # wyjątki domenowe
│   ├── main.py                     # punkt startowy aplikacji
│   ├── models.py                   # modele danych
│   ├── network.py                  # tryb klient-serwer oraz protokół JSON-line
│   ├── repositories.py             # repozytorium JSON
│   └── services.py                 # logika głosowania, audytu i zliczania
├── tests/
│   ├── conftest.py                 # fixtures testowe
│   ├── test_cli_helpers.py         # testy pomocników CLI
│   ├── test_crypto.py              # testy kryptografii Pailliera
│   ├── test_network_helpers.py     # testy pomocników sieciowych
│   ├── test_repositories.py        # testy repozytorium JSON
│   ├── test_scripts.py             # testy skryptów serwisowych
│   └── test_services.py            # testy logiki domenowej
├── pyproject.toml                  # konfiguracja projektu i pytest
├── uv.lock                         # lockfile zależności
└── README.md
```

## Instalacja

### 1. Klonowanie repozytorium

```bash
git clone <repo-url>
cd e-voting-system
```

### 2. Instalacja `uv`

Jeżeli `uv` nie jest jeszcze zainstalowane:

```bash
pip install uv
```

albo:

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

### 3. Instalacja zależności

```bash
uv sync
```

## Przygotowanie danych i kluczy

Przed uruchomieniem głosowania przygotuj środowisko:

```bash
uv run python scripts/prepare_system.py
```

Skrypt wykonuje trzy operacje:

1. usuwa pliki runtime: `data/votes.json`, `data/results.json`, `data/audit_log.json`, `keys/private_key.json`, `keys/public_key.json`,
2. ustawia `voted: false` dla wszystkich wyborców z `data/voters.json`,
3. generuje nową parę kluczy Pailliera i zapisuje ją w katalogu `keys/`.

Do samego wyczyszczenia danych runtime można użyć:

```bash
uv run python scripts/clean_system.py
```

## Uruchamianie aplikacji

### Tryb lokalny — referendum

```bash
uv run python src/main.py local data/questions_referendum.json
```

### Tryb lokalny — wybory

```bash
uv run python src/main.py local data/questions_election.json
```

### Tryb sieciowy — serwer

```bash
uv run python src/main.py server data/questions_referendum.json
```

albo dla wyborów:

```bash
uv run python src/main.py server data/questions_election.json
```

Domyślnie serwer nasłuchuje na porcie TCP `8765` i rozgłasza swoją obecność przez UDP na porcie `8766`.

### Tryb sieciowy — klient

```bash
uv run python src/main.py client
```

Klient automatycznie szuka serwera w sieci lokalnej. Adres IP serwera nie musi być podawany ręcznie, jeśli UDP broadcast jest dostępny w danej sieci.

### Pomoc CLI

```bash
uv run python src/main.py --help
```

## Format danych

### Wyborcy — `data/voters.json`

Każdy rekord wyborcy zawiera m.in.:

```json
{
  "name": "Jan Kowalski",
  "pesel": "90211801608",
  "id_card_number": "ZBY839334",
  "voted": false,
  "voter_id": "90211801608"
}
```

Podczas weryfikacji użytkownik podaje:

- imię i nazwisko,
- cztery ostatnie cyfry PESEL,
- numer dokumentu tożsamości.

### Referendum — `data/questions_referendum.json`

Referendum składa się z pytań typu tak/nie/brak odpowiedzi:

```json
{
  "question_id": "q01",
  "text": "Czy organizacja powinna wprowadzić głosowanie elektroniczne w kolejnych wyborach?"
}
```

### Wybory — `data/questions_election.json`

Wybory są reprezentowane jako lista kandydatów/opcji. Wyborca powinien wskazać dokładnie jedną opcję:

```json
{
  "question_id": "q01",
  "text": "Anna Kowalska"
}
```

### Pliki generowane w trakcie działania

| Plik | Znaczenie |
|---|---|
| `data/votes.json` | zaszyfrowane głosy |
| `data/results.json` | wyniki po zliczeniu |
| `data/audit_log.json` | historia zdarzeń i odrzuceń |
| `keys/public_key.json` | publiczny klucz szyfrowania |
| `keys/private_key.json` | prywatny klucz odszyfrowania wyników |

## Przebieg głosowania

1. System ładuje listę wyborców, pytania oraz klucze kryptograficzne.
2. Wyborca przechodzi weryfikację danych.
3. Aplikacja wykrywa typ głosowania na podstawie pliku pytań.
4. Wyborca oddaje głos w interfejsie terminalowym.
5. Głos jest walidowany i szyfrowany.
6. Zaszyfrowany głos trafia do repozytorium JSON.
7. System zapisuje zdarzenie w logu audytowym.
8. Wyniki są zliczane homomorficznie, a odszyfrowany zostaje wyłącznie wynik końcowy.

## Testy

Uruchomienie pełnego zestawu testów:

```bash
uv run pytest
```

Aktualny zestaw obejmuje **42 testy** pogrupowane w sześć obszarów:

| Plik testowy | Zakres |
|---|---|
| `tests/test_cli_helpers.py` | normalizacja danych wejściowych, maskowanie dokumentów, wykrywanie trybu głosowania, weryfikacja wyborcy oraz składanie głosów z poziomu CLI |
| `tests/test_crypto.py` | szyfrowanie i deszyfrowanie głosów, agregacja homomorficzna, serializacja zaszyfrowanych liczb oraz obsługa kluczy |
| `tests/test_network_helpers.py` | konwersja odpowiedzi klienta, walidacja macierzy referendum, wektora wyborczego oraz komunikacja JSON-line przez socket |
| `tests/test_repositories.py` | zapis, odczyt, czyszczenie i walidacja plików JSON |
| `tests/test_scripts.py` | działanie skryptów czyszczących, resetujących wyborców i regenerujących klucze |
| `tests/test_services.py` | reguły domenowe głosowania, blokowanie nieuprawnionych wyborców, odrzucanie błędnych głosów i zliczanie wyników |

### Szczegółowy opis testów

#### `tests/test_cli_helpers.py`

| Test | Co sprawdza |
|---|---|
| `test_normalize_digits_removes_non_digits` | usuwa z tekstu wszystko poza cyframi, np. z numerów PESEL lub dokumentów |
| `test_normalize_text_ignores_case_spaces_and_polish_characters` | normalizuje wielkość liter, odstępy i polskie znaki, żeby porównywanie danych wyborcy było odporne na różnice w zapisie |
| `test_mask_id_number_hides_document_number` | maskuje numer dokumentu w interfejsie, aby nie wyświetlać go jawnie na ekranie |
| `test_question_helpers_use_fallback_fields` | pozwala odczytać identyfikator i tekst pytania także z alternatywnych pól, np. `candidate_id` i `candidate_name` |
| `test_infer_mode_detects_referendum_from_question_text` | rozpoznaje referendum, gdy dane zawierają klasyczne pola pytania referendalnego |
| `test_infer_mode_detects_election_from_candidate_field` | rozpoznaje wybory, gdy dane zawierają pola kandydackie |
| `test_verify_voter_accepts_correct_data` | akceptuje wyborcę po podaniu poprawnych danych identyfikacyjnych |
| `test_verify_voter_rejects_wrong_document` | odrzuca wyborcę, gdy numer dokumentu nie zgadza się z danymi w repozytorium |
| `test_submit_referendum_saves_only_marked_answers` | zapisuje tylko poprawnie zaznaczone odpowiedzi referendalne i oznacza wyborcę jako głosującego |
| `test_submit_election_requires_exactly_one_candidate` | pilnuje zasady, że w wyborach można zaznaczyć dokładnie jednego kandydata |

#### `tests/test_crypto.py`

| Test | Co sprawdza |
|---|---|
| `test_encrypt_and_decrypt_yes_vote` | głos `TAK` po zaszyfrowaniu i odszyfrowaniu nadal ma wartość `1` |
| `test_encrypt_and_decrypt_no_vote` | głos `NIE` po zaszyfrowaniu i odszyfrowaniu nadal ma wartość `0` |
| `test_homomorphic_addition_counts_only_yes_votes` | suma zaszyfrowanych głosów poprawnie zlicza tylko głosy pozytywne |
| `test_empty_vote_sum_is_zero` | zliczanie pustej listy głosów daje wynik `0` |
| `test_encrypted_number_can_be_serialized_and_restored` | zaszyfrowany głos można zapisać do JSON i odtworzyć bez utraty wartości |
| `test_invalid_vote_value_is_not_encrypted` | wartości inne niż dopuszczalne głosy są odrzucane przed szyfrowaniem |
| `test_encryption_requires_public_key` | szyfrowanie nie może wystartować bez załadowanego klucza publicznego |
| `test_key_manager_saves_and_loads_keys` | `KeyManager` poprawnie zapisuje i odczytuje klucze publiczny oraz prywatny |

#### `tests/test_network_helpers.py`

| Test | Co sprawdza |
|---|---|
| `test_referendum_matrix_is_accepted_when_each_question_has_one_answer` | akceptuje macierz referendum, gdy każde pytanie ma dokładnie jeden stan odpowiedzi |
| `test_referendum_text_answers_are_converted_to_matrix` | konwertuje odpowiedzi tekstowe, np. `tak`, `nie`, `brak`, na macierz głosów |
| `test_referendum_rejects_question_with_two_answers` | odrzuca referendum, w którym jedno pytanie ma więcej niż jedną odpowiedź |
| `test_election_answers_are_converted_to_zero_one_vector` | zamienia odpowiedzi wyborcze na wektor wartości `0/1` |
| `test_election_rejects_wrong_number_of_answers` | odrzuca wektor wyborczy o nieprawidłowej liczbie odpowiedzi |
| `test_json_line_helpers_send_and_read_payload` | sprawdza wysyłanie i odbieranie pojedynczego komunikatu JSON zakończonego znakiem nowej linii |
| `test_json_line_reader_rejects_closed_connection` | zgłasza błąd, gdy połączenie zostanie zamknięte przed odebraniem danych |

#### `tests/test_repositories.py`

| Test | Co sprawdza |
|---|---|
| `test_repository_returns_empty_list_when_file_does_not_exist` | brak pliku danych jest traktowany jako pusta lista rekordów |
| `test_repository_saves_and_loads_json_list` | repozytorium poprawnie zapisuje i odczytuje listę obiektów JSON |
| `test_repository_clear_overwrites_file_with_empty_list` | metoda czyszczenia nadpisuje plik pustą listą |
| `test_repository_rejects_json_object_instead_of_list` | repozytorium odrzuca plik, którego głównym elementem jest obiekt zamiast listy |

#### `tests/test_scripts.py`

| Test | Co sprawdza |
|---|---|
| `test_clean_system_removes_runtime_files` | skrypt czyszczący usuwa pliki głosów, wyników, audytu i kluczy |
| `test_clean_system_resets_voters_status` | resetuje wszystkim wyborcom flagę `voted` na `false` |
| `test_clean_system_rejects_wrong_voters_file_format` | odrzuca niepoprawny format pliku wyborców |
| `test_prepare_system_regenerates_key_files` | skrypt przygotowujący środowisko generuje i zapisuje nowe pliki kluczy |

#### `tests/test_services.py`

| Test | Co sprawdza |
|---|---|
| `test_authorized_voter_can_cast_vote` | uprawniony wyborca może oddać głos, a zdarzenie trafia do audytu |
| `test_unknown_voter_is_rejected` | wyborca spoza listy jest odrzucany, a głos nie zostaje zapisany |
| `test_voter_cannot_vote_twice_on_same_question` | ten sam wyborca nie może zagłosować dwa razy na to samo pytanie |
| `test_voter_can_vote_on_different_questions_before_final_mark` | wyborca może odpowiedzieć na różne pytania przed finalnym oznaczeniem jako głosujący |
| `test_marked_voter_cannot_vote_again` | wyborca oznaczony jako `voted` nie może ponownie rozpocząć głosowania |
| `test_invalid_question_is_rejected` | głos na nieistniejące pytanie jest odrzucany |
| `test_invalid_vote_value_is_rejected` | wartość głosu spoza dozwolonego typu jest odrzucana |
| `test_tally_single_question_counts_yes_and_no` | zliczanie pojedynczego pytania poprawnie zwraca liczbę głosów `TAK`, `NIE` i sumę ważnych głosów |
| `test_tally_all_questions_saves_results` | zliczanie wszystkich pytań zapisuje wyniki i końcowe zdarzenie audytowe |

## Bezpieczeństwo i ograniczenia

System demonstruje podstawowe mechanizmy bezpiecznego głosowania, ale nie jest kompletnym rozwiązaniem produkcyjnym.

Zastosowane mechanizmy:

- brak zapisu głosów jawnych w pliku `votes.json`,
- szyfrowanie głosu przed utrwaleniem,
- agregacja zaszyfrowanych wartości,
- odszyfrowanie dopiero wyniku końcowego,
- walidacja wyborców przed dopuszczeniem do głosowania,
- log audytowy dla zaakceptowanych i odrzuconych operacji.

Ograniczenia wersji demonstracyjnej:

- klucz prywatny jest przechowywany lokalnie w pliku JSON,
- brak rozdzielenia ról administratora, komisji i wyborcy,
- brak podpisów cyfrowych oraz zaawansowanej ochrony integralności plików,
- brak formalnej weryfikacji protokołu kryptograficznego,
- brak zgodności z wymaganiami prawnymi dla rzeczywistych wyborów publicznych.

## Uwagi dla dewelopera

- Kod źródłowy znajduje się w katalogu `src` i w obecnej strukturze jest importowany jako moduły top-level, np. `from crypto import PaillierService`.
- Testy mają skonfigurowany `pythonpath = ["src", "."]` w `pyproject.toml`, dlatego importy typu `from crypto import ...` działają podczas uruchamiania `pytest`.
- Skrypty z katalogu `scripts/` najlepiej uruchamiać z katalogu głównego projektu.
- Nie używaj importu `from src.crypto import ...`, jeśli środowisko nie traktuje katalogu projektu jako pakietu nadrzędnego.
- Pliki `data/votes.json`, `data/results.json`, `data/audit_log.json` i klucze w `keys/` są danymi runtime i mogą być odtwarzane przez `prepare_system.py`.

## Licencja

Projekt jest udostępniany na warunkach licencji Apache License 2.0. Szczegóły znajdują się w pliku [`LICENSE`](LICENSE).
