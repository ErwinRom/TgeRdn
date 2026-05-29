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
3. Upewnij się, że katalog `/tmp/tgerdn/` jest czytelny dla Home Assistant.

## Home Assistant OS jako lokalny dodatek

W repozytorium znajduje się manifest dodatku: `config.json`.
Możesz użyć tego projektu jako lokalnego dodatku w Home Assistant OS.

### Jak zainstalować lokalny dodatek
1. Umieść to repozytorium w katalogu lokalnych dodatków lub utwórz własne repozytorium lokalne.
2. W Home Assistant przejdź do `Supervisor` → `Add-on Store` → `Repositories`.
3. Dodaj lokalne repozytorium (ścieżka do katalogu z `config.json`).
4. Zainstaluj dodatek `TGE RDN Scraper`.
5. Skonfiguruj opcje dodatku:
   - `output_dir`: `/data/tgerdn`
   - `interval`: `1`
   - `hour`: `*`
6. Uruchom dodatek.

Po uruchomieniu dodatek zapisuje pliki do katalogu `output_dir` w środowisku Home Assistant.

## Konfiguracja w `configuration.yaml`

Dodaj definicje REST sensorów:

```yaml
rest:
  - resource: "file:///tmp/tgerdn/tgerdn_prices.yaml"
    name: "TGE RDN Cena Dzis"
    unique_id: "tgerdn_cena_dzis"
    scan_interval: 300
    value_template: "{{ value_json.data_points }}"
    json_attributes:
      - prices
      - last_update
      - data_points
      - unit_of_measurement
      - friendly_name

  - resource: "file:///tmp/tgerdn/tgerdn_prices_tomorrow.yaml"
    name: "TGE RDN Cena Jutro"
    unique_id: "tgerdn_cena_jutro"
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
        unit_of_measurement: "PLN/MWh"
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
        unit_of_measurement: "PLN/MWh"
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
        unit_of_measurement: "PLN/MWh"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | min) }}
          {%- endif %}

      - name: "TGE RDN Max Cena Dzis"
        unique_id: tgerdn_max_price_dzis
        unit_of_measurement: "PLN/MWh"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_dzis', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | max) }}
          {%- endif %}

      - name: "TGE RDN Min Cena Jutro"
        unique_id: tgerdn_min_price_jutro
        unit_of_measurement: "PLN/MWh"
        value_template: |
          {%- set prices = state_attr('sensor.tge_rdn_cena_jutro', 'prices') %}
          {%- if prices %}
            {{ (prices | map(attribute='rce_pln') | list | min) }}
          {%- endif %}

      - name: "TGE RDN Max Cena Jutro"
        unique_id: tgerdn_max_price_jutro
        unit_of_measurement: "PLN/MWh"
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

Scheduler tworzy pliki w katalogu `/tmp/tgerdn/`:

```
/tmp/tgerdn/
├── tgerdn_prices.json
├── tgerdn_prices.yaml
├── tgerdn_prices_tomorrow.json
└── tgerdn_prices_tomorrow.yaml
```

## Rozwiązywanie problemów

### Czujniki są niedostępne
1. Sprawdź, czy scheduler działa: `ps aux | grep scheduler.py`
2. Sprawdź, czy pliki istnieją: `ls -la /tmp/tgerdn/`
3. Sprawdź zawartość: `cat /tmp/tgerdn/tgerdn_prices.yaml | head`
4. Przeładuj integrację REST w Home Assistant.

### Problem z uprawnieniami
```bash
sudo chown homeassistant:homeassistant /tmp/tgerdn
chmod 755 /tmp/tgerdn
chmod 644 /tmp/tgerdn/*.yaml
```

### Brak danych w atrybucie `prices`
- Upewnij się, że plik YAML jest poprawny.
- Sprawdź działanie scraper-a ręcznie: `python scraper.py 28-05-2026`

## Uwagi końcowe
- Integracja oparta jest na lokalnym pliku YAML.
- Home Assistant odczytuje dane co 5 minut.
- Scheduler aktualizuje dane co godzinę.
- Pliki wyjściowe muszą być dostępne dla użytkownika Home Assistant.
- Dane obejmują 24 ceny godzinowe na dany dzień dostawy.
- Jeśli używasz lokalnego dodatku HA, ustaw `output_dir` w konfiguracji dodatku.
- Wartość `scan_interval` 300 oznacza odczyt co 5 minut.
