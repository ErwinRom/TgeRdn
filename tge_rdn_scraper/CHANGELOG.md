# Changelog

## 1.0.3

- Fixed the default scraper schedule to run only at 00:01 and 12:01.
- Updated the cron setup to match the same two execution times.
- Added the changelog entry for the schedule change.

## 1.0.2

- Add a PLN lightning-bolt icon and TGE RDN logo for the Home Assistant add-on.

## 1.0.1

- Log whether price data was read from the TGE page for today and tomorrow, including the delivery date.
- Compare fetched data with the existing JSON before writing; leave files untouched when the data has not changed.
- Log whether each JSON file was updated or left unchanged.