# Konfiguracja Home Assistant dla TGE RDN

## Przegląd
Dwa czujniki REST, które aktualizują się automatycznie co godzinę:
1. `sensor.tge_rdn_cena_dzis` - ceny dzisiejsze
2. `sensor.tge_rdn_cena_jutro` - ceny jutrzejsze

## Wymagania wstępne
1. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```
2. Uruchom scheduler:
   ```bash
   python scheduler.py --output-dir /tmp/tgerdn
   ```
3. Jeśli używasz HA OS add-on, ustaw `output_dir` na `/config/tgerdn` i sprawdź dostępność tego katalogu dla Home Assistant.

## Home Assistant OS jako lokalny dodatek

W repozytorium znajduje się manifest dodatku: `config.yaml`.
Możesz użyć tego projektu jako lokalnego dodatku w Home Assistant OS.

### Jak zainstalować lokalny dodatek
1. Home Assistant OS: umieść katalog dodatku jako `/addons/tgerdn/` (obok katalogu `config`, nie w `/config/addons/`).
2. W Home Assistant przejdź do `Supervisor` → `Add-on Store` → `Repositories`.
3. Jeśli dodatek nie pojawi się automatycznie, dodaj repozytorium zawierające katalog z `config.yaml`.
4. Zainstaluj dodatek `TGE RDN Scraper`.
5. Skonfiguruj opcje dodatku:
   - `output_dir`: `/config/tgerdn`
   - `interval`: `1`
   - `hour`: `*`
6. Uruchom dodatek.

Po uruchomieniu dodatek zapisuje pliki do katalogu `/config/tgerdn` wewnątrz Home Assistant.

## Krok po kroku: uruchomienie wersji kontenerowej na HA OS
1. Skopiuj całe repozytorium do lokalnego repozytorium dodatków Home Assistant.
2. W Home Assistant przejdź do `Supervisor` → `Add-on Store` → `Repositories` i dodaj repozytorium.
3. Zainstaluj dodatek `TGE RDN Scraper`.
4. W ustawieniach dodatku ustaw:
   - `output_dir`: `/config/tgerdn`
   - `interval`: `1`
   - `hour`: `*`
5. Uruchom dodatek.
6. Sprawdź, że pliki powstały w katalogu `config/tgerdn` Home Assistant.
7. Dodaj konfigurację `command_line` poniżej, aby używać plików JSON jako encji.

> Jeśli używasz HA OS, plik zapisany w `/config/tgerdn` jest dostępny dla samego Home Assistant.

## Konfiguracja w `configuration.yaml`

Dodaj definicje sensorów `command_line`:

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

## Opcjonalne czujniki szablonowe

Możesz dodać czujnik pokazujący aktualną godzinę lub wartości min/max:

```yaml
template:
  - sensor:
      - name: "TGE RDN Aktualna Cena Dzis"
        unique_id: tgerdn_current_price_dzis
        unit_of_measurement: "PLN/kWh"
        state_class: measurement
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- set hour = now().hour %}
          {%- if prices %}
            {%- for p in prices if p.period.split(' - ')[0][:2]|int == hour %}
              {{ p.rce_pln }}
            {%- endif %}
          {%- endif %}

      - name: "TGE RDN Aktualna Cena Jutro"
        unique_id: tgerdn_current_price_jutro
        unit_of_measurement: "PLN/kWh"
        state_class: measurement
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_jutro', 'prices') %}
          {%- set hour = now().hour %}
          {%- if prices %}
            {%- for p in prices if p.period.split(' - ')[0][:2]|int == hour %}
              {{ p.rce_pln }}
            {%- endif %}
          {%- endif %}

      - name: "TGE RDN Min Cena Dzis"
        unique_id: tgerdn_min_price_dzis
        unit_of_measurement: "PLN/kWh"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | min) }}
          {%- endif %}

      - name: "TGE RDN Max Cena Dzis"
        unique_id: tgerdn_max_price_dzis
        unit_of_measurement: "PLN/kWh"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | max) }}
          {%- endif %}

      - name: "TGE RDN Min Cena Jutro"
        unique_id: tgerdn_min_price_jutro
        unit_of_measurement: "PLN/kWh"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_jutro', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | min) }}
          {%- endif %}

      - name: "TGE RDN Max Cena Jutro"
        unique_id: tgerdn_max_price_jutro
        unit_of_measurement: "PLN/kWh"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_jutro', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | max) }}
          {%- endif %}
```

## Automatyzacje

### Przykład 1: powiadomienie, gdy cena jest niska

```yaml
automation:
  - alias: "TGE RDN - niska cena dziś"
    trigger:
      platform: state
      entity_id: sensor.tge_rdn_cena_dzis
      for: "00:05:00"
    condition:
      - condition: template
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | min) < 100 }}
          {%- endif %}
    action:
      service: notify.mobile_app_<twoj_urzadzenie>
      data:
        title: "TGE RDN"
        message: "Cena prądu jest niska dziś!"
```

## Dostęp do danych w szablonach

```jinja
# Wszystkie ceny
{{ state_attr('sensor.tge_rdn_cena_dzis', 'prices') }}

# Aktualna godzina
{{ now().hour }}

# Najniższa cena
{{ (state_attr('sensor.tge_rdn_cena_dzis', 'prices') | map(attribute='rce_pln') | list | min) }}

# Najwyższa cena
{{ (state_attr('sensor.tge_rdn_cena_dzis', 'prices') | map(attribute='rce_pln') | list | max) }}

# Cena o konkretnej godzinie
{% set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
{% for p in prices %}
  {% if '10:00' in p.dtime %}
    {{ p.rce_pln }}
  {% endif %}
{% endfor %}
```

## Pliki wyjściowe

Scheduler tworzy pliki w katalogu `/config/tgerdn/` dla HA OS add-on:

```
/config/tgerdn/
├── tgerdn_prices.json
└── tgerdn_prices_tomorrow.json
```

## Rozwiązywanie problemów

### Czujniki są niedostępne
1. Sprawdź, czy scheduler działa: `ps aux | grep scheduler.py`
2. Sprawdź, czy pliki istnieją: `ls -la /config/tgerdn/`
3. Sprawdź zawartość: `cat /config/tgerdn/tgerdn_prices.json | head`
4. Przeładuj integrację REST w Home Assistant.

### Problem z uprawnieniami
```bash
sudo chown homeassistant:homeassistant /config/tgerdn
chmod 755 /config/tgerdn
chmod 644 /config/tgerdn/*.json
```

### Brak danych w atrybucie `prices`
- Upewnij się, że plik JSON zawiera dane `prices`.
- Sprawdź działanie scraper-a ręcznie: `python scraper.py 28-05-2026`

## Uwagi końcowe
- Integracja oparta jest na lokalnym pliku JSON.
- Home Assistant odczytuje dane co 5 minut.
- Scheduler aktualizuje dane co godzinę.
- Pliki wyjściowe muszą być dostępne dla użytkownika Home Assistant.
- Dane obejmują 24 ceny godzinowe na dany dzień dostawy.
- Jeśli używasz lokalnego dodatku HA, ustaw `output_dir` w konfiguracji dodatku.
- Wartość `scan_interval` 300 oznacza odczyt co 5 minut.
