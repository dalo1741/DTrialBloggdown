# contract-tool

Scaffold för kontraktsverktyget: formulär → validering → två oberoende
exportspår (kontraktsdokument + NetSuite), enligt modellen som togs fram i
designdiskussionen (se commit-historik / chattsammanfattning).

## Arkitektur

```
formulär (public/) --POST /api/contracts--> server.ts --validerar (zod)--> contractStore
                                                  |
                                                  v
                                        emitContractSubmitted (events.ts)
                                          /                      \
                                         v                        v
                          exportContractDocument          exportToNetsuite
                          (PDF via pdfkit, eller           (customer + sales order
                           stub e-signering)                + rentCalculationSetup-stub)
```

De två exportspåren är helt oberoende lyssnare på samma event. Ett fel i det
ena blockerar aldrig det andra — status för respektive spår finns separat på
kontraktsposten (`contractExport.status`, `netsuiteExport.status`) och kan
pollas via `GET /api/contracts/:id`.

## Varumärkesprofil (branding och layout)

En global, disk-persisterad "brand profile" (`src/storage/brandProfileStore.ts`,
`data/brand/profile.json` + `data/brand/logo.*`) styr hur alla genererade
kontrakts-PDF:er ser ut: logga, primär-/sekundärfärg, typsnitt (begränsat
till pdfkits inbyggda standardfonter), marginaler, sidhuvud/-fot-text och
logotypens placering. Ställs in via `/brand.html` (`GET`/`PUT
/api/brand-profile`, `POST`/`GET /api/brand-profile/logo`) och tillämpas i
`src/pdf/renderContractPdf.ts` på varje genererad PDF.

## Kontraktsmallar (Phase 3)

Ett andra, fristående kontraktsflöde vid sidan av det fasta Aimo Park-schemat:
`src/types/contractTemplate.ts` + `src/storage/templateStore.ts` låter dig
definiera en mall (namn + fri text) med `{{platshållare}}` i texten -
fältlistan härleds automatiskt ur texten, inget separat fältschema att hålla
i synk. CRUD via `/templates.html` (`/api/templates`, `/api/templates/:id`,
`/api/templates/:id/duplicate`). Ett konkret avtal skapas via
`/new-template-contract.html`: välj mall → dynamiskt formulär (ett fält per
platshållare, typvaliderat med ett zod-schema som byggs vid körning i
`buildFieldValuesSchema`) → `POST /api/templates/:id/render` ersätter
platshållarna och renderar en branded PDF direkt (`src/pdf/renderTemplatedContract.ts`,
synkront - inget NetSuite/e-sign-spår för den här kontraktstypen).

`src/pdf/pdfHeader.ts` innehåller den delade sidhuvud/-fot-logiken
(logga/färger/marginaler enligt varumärkesprofilen) som både
`renderContractPdf.ts` (Aimo Park) och `renderTemplatedContract.ts` (mallar)
återanvänder.

## Vad som är stubbat och måste bytas ut

- `src/exporters/eSignClient.ts` — riktigt API-anrop mot vald
  e-signeringsleverantör (Scrive/Oneflow/DocuSign m.fl.).
- `src/netsuite/client.ts` — riktiga anrop mot NetSuite SuiteTalk REST API
  (OAuth 1.0a/TBA-autentisering, se `.env.example`). `upsertRentCalculationSetup`
  ska pekas mot den custom record-typ (eller de fält) som er befintliga
  hyres-/självfaktureringsmotor redan läser från — namnet
  `customrecord_charging_contract_terms` är en platshållare.
- `src/storage/contractStore.ts` — in-memory just nu, byt mot en riktig
  databas (t.ex. Postgres) innan produktion.
- `src/events.ts` — in-process EventEmitter, byt mot en riktig kö (SQS m.m.)
  om ni vill ha garanterad leverans/retry oberoende av processens livstid.

## Köra lokalt

```bash
npm install
cp .env.example .env   # fyll i vid behov
npm run dev
```

Öppna http://localhost:3000, fyll i formuläret, tryck "Kör". Genererad PDF
hamnar i `data/contracts/`, NetSuite-anropen loggas till konsollen (stubbar).

## Nästa steg

1. Välj e-signeringsleverantör och implementera `eSignClient.ts`.
2. Bekräfta NetSuite-fältnamn (subsidiary, item-koder, custom record för
   hyresmotorn) och implementera `netsuite/client.ts` mot SuiteTalk REST.
3. Byt in-memory store mot riktig databas.
4. Lägg till autentisering på formuläret (idag helt öppet).
