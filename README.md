# TGE RDN Scraper dla Home Assistant

Pythonowy skrypt do pobierania cen energii elektrycznej z TGE (Towarowa Giełda Energii) i generowania plików JSON zgodnych z Home Assistant.

## Funkcje

- ✅ dwa czujniki:
  - `sensor.tge_rdn_cena_dzis` - ceny godzinowe na dziś
  - `sensor.tge_rdn_cena_jutro` - ceny godzinowe na jutro
- ✅ pobiera ceny „Fixing I” z TGE i zapisuje je w JSON w PLN/kWh
- ✅ zapisuje daty dostawy i godziny
- ✅ 24 ceny godzinowe na dzień
- ✅ generuje pliki JSON do odczytu w Home Assistant
- ✅ automatyczne uruchamianie co godzinę
- ✅ wyjście w formacie JSON

## Instalacja

1. Zainstaluj wymagane biblioteki:
   ```bash
   pip install -r requirements.txt
   ```

## Składniki projektu

### 1. Scraper (`scraper.py`)
Pobiera dane cenowe z serwisu TGE.

**Użycie:**
```bash
# Domyślnie dla dzisiejszej daty
python scraper.py

# Data w formacie DD-MM-YYYY
python scraper.py 27-05-2026

# Opcjonalny parametr typu
python scraper.py 27-05-2026 1
```

**Wynik:** JSON z cenami godzinowymi.

### 2. Generator YAML (`yaml_generator.py`)
Opcjonalne narzędzie ręczne do konwersji wyjścia JSON na YAML.

**Użycie:**
```bash
# Z pliku JSON do pliku YAML
python yaml_generator.py prices.json output.yaml

# Z piped stdin
python scraper.py 28-05-2026 | python yaml_generator.py -

# Tylko wydruk na stdout
python yaml_generator.py prices.json
```

### 3. Scheduler (`scheduler.py`)
Uruchamia scraper i zapisuje pliki JSON dwa razy dziennie: o 00:01 i 12:01. Można też ustawić własną godzinę dzienną w formacie `HH:MM`.

**Użycie:**
```bash
# Uruchomienie domyślne (generuje w /tmp/tgerdn)
python scheduler.py

# Inny katalog wyjściowy
python scheduler.py --output-dir /home/ha/tgerdn

# Własne godziny (lista oddzielona przecinkami)
python scheduler.py --hour "06:30,18:45"
```

**Opcje:**
- `--output-dir`: katalog na wygenerowane pliki (domyślnie `/tmp/tgerdn`)
- `--hour`: godziny codziennych uruchomień w formacie `HH:MM`, oddzielone przecinkami; domyślnie `00:01,12:01`

## Uruchomienie ciągłe

### Opcja 1: Systemd

1. Dostosuj `tgerdn-scraper.service` do Twoich ścieżek.
2. Skopiuj plik do katalogu systemd:
   ```bash
   sudo cp tgerdn-scraper.service /etc/systemd/system/
   ```
3. Przeładuj systemd i włącz usługę:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tgerdn-scraper.service
   sudo systemctl start tgerdn-scraper.service
   ```

### Opcja 2: Cron

Uruchom skrypt instalacyjny:
```bash
bash setup_cron.sh
```

Lub dodaj ręcznie do crontaba:
```bash
1 0 * * * cd /home/erwin/Projekty/TgeRdn && python3 scheduler.py --output-dir /tmp/tgerdn >> /var/log/tgerdn.log 2>&1
1 12 * * * cd /home/erwin/Projekty/TgeRdn && python3 scheduler.py --output-dir /tmp/tgerdn >> /var/log/tgerdn.log 2>&1
```

### Opcja 3: Kontener Docker

Zbuduj obraz:
```bash
docker build -t tge_rdn_scraper .
```

Uruchom jednorazowo:
```bash
docker run --rm -v /tmp/tgerdn:/data/tgerdn tge_rdn_scraper
```

Uruchom jako usługę ciągłą:
```bash
docker run -d \
  --name tge_rdn_scraper \
  -v /tmp/tgerdn:/data/tgerdn \
  -e OUTPUT_DIR=/data/tgerdn \
   -e HOUR="00:01,12:01" \
  tge_rdn_scraper
```

W kontenerze dane zapisują się do `/data/tgerdn`, co jest mapowane na katalog hosta.

## Instalacja jako repozytorium dodatków HA

Dodaj repozytorium TGE RDN do Home Assistant Add-on Store:

[Dodaj repozytorium TGE RDN](https://my.home-assistant.io/redirect/supervisor_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FErwinRom%2FTgeRdn)

Możesz też dodać ręcznie adres `https://github.com/ErwinRom/TgeRdn` w `Ustawienia` → `Dodatki` → `Sklep z dodatkami` → menu ⋮ → `Repozytoria`. Następnie zainstaluj `TGE RDN Scraper` i ustaw opcje dodatku:
   - `output_dir`: `/config/tgerdn`
   - `hour`: `00:01,12:01` (lub własne godziny, np. `06:30,18:45`)
Uruchom dodatek. Zapisze pliki JSON w katalogu konfiguracji HA pod `/config/tgerdn`.

Po uruchomieniu dodatek zapisuje pliki do katalogu `/config/tgerdn` w środowisku HA.

## Integracja z Home Assistant

Przykład REST sensor w `configuration.yaml`:
```yaml
command_line:
  - sensor:
      name: "TGE RDN Cena Dzis"
      unique_id: "tgerdn_cena_dzis"
      command: "cat /config/tgerdn/tgerdn_prices.json"
      scan_interval: 300
      value_template: "{{ value_json.data_points }}"
      json_attributes:
        - prices
        - last_update
        - data_points
        - unit_of_measurement
        - friendly_name

  - sensor:
      name: "TGE RDN Cena Jutro"
      unique_id: "tgerdn_cena_jutro"
      command: "cat /config/tgerdn/tgerdn_prices_tomorrow.json"
      scan_interval: 300
      value_template: "{{ value_json.data_points }}"
      json_attributes:
        - prices
        - last_update
        - data_points
        - unit_of_measurement
        - friendly_name
```

Możesz też użyć czujnika plikowego (template file sensor) albo innych integracji zgodnych z lokalnym plikiem.

## Pliki wyjściowe

W katalogu wyjściowym będą powstawać następujące pliki:

```
{output_dir}/
├── tgerdn_prices.json
└── tgerdn_prices_tomorrow.json
```

## Rozwiązywanie problemów

### Brak wyjścia z skryptu
- Sprawdź, czy strona TGE jest dostępna.
- Sprawdź datę i parametry w wywołaniu.
- Sprawdź połączenie sieciowe.

### Brak danych JSON
- Sprawdź, czy plik JSON zawiera dane `fixing_i_prices`.

### Scheduler nie działa
- Cron: `crontab -l`
- Systemd: `sudo journalctl -u tgerdn-scraper.service`
- Sprawdź ścieżkę do Pythona i uprawnienia katalogu.

### Uprawnienia plików
```bash
sudo chown homeassistant:homeassistant /tmp/tgerdn
chmod 755 /tmp/tgerdn
chmod 644 /tmp/tgerdn/*.json
```

## Pliki w repozytorium

- `scraper.py` - główny skrypt pobierający dane z TGE
- `yaml_generator.py` - konwertuje JSON na YAML dla HA
- `scheduler.py` - uruchamia zadanie cykliczne
- `requirements.txt` - zależności Pythona
- `Dockerfile` - konteneryzacja
- `run.sh` - entrypoint do kontenera
- `repository.yaml` - metadane repozytorium dodatków Home Assistant
- `tge_rdn_scraper/` - kompletny dodatek Home Assistant (manifest, Dockerfile i kod)
- `tgerdn-scraper.service` - przykładowa usługa systemd
- `setup_cron.sh` - skrypt do utworzenia zadania cron

## Wymagania

- Python 3.6+
- requests
- beautifulsoup4
- PyYAML
- schedule

## Uwagi końcowe

- Scraper pobiera dane dla podanej daty i generuje ceny godzinowe na ten dzień.
- Dane obejmują 24 godziny dla dnia dostawy.
- Strefa czasowa: Polska (UTC+2 latem, UTC+1 zimą).
- Ceny w plikach JSON są podane w PLN/kWh; strona TGE publikuje źródłową kolumnę w PLN/MWh.
- Scheduler aktualizuje dane co godzinę, jeśli jest uruchomiony.
