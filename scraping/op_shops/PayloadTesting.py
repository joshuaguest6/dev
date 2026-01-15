from main import main

payload = [
    {
    "Date": "2026-01-15 12:50:42",
    "Store": "Salvos",
    "StoreID": "766",
    "Suburb": "Devonport",
    "Address": "05/09/24 Stewart Street<br>Devonport TAS 7310",
    "Latitude": "-41.1804229",
    "Longitude": "146.3622719",
    "Hours": "Monday: 10:00:00 to 17:00:00, Tuesday: 09:00:00 to 17:00:00, Wednesday: 09:00:00 to 17:00:00, Thursday: 09:00:00 to 17:00:00, Friday: 09:00:00 to 17:00:00, Saturday: 10:00:00 to 16:00:00, Sunday: Closed"
  },
  {
    "Date": "2026-01-15 12:50:42",
    "Store": "Salvos",
    "StoreID": "763",
    "Suburb": "Port Sorell",
    "Address": "Shop 14/11 Poyston Drive<br>Shearwater TAS 7307",
    "Latitude": "-41.1618099",
    "Longitude": "146.532415",
    "Hours": "Monday: 10:00:00 to 17:00:00, Tuesday: 09:00:00 to 17:00:00, Wednesday: 09:00:00 to 17:00:00, Thursday: 09:00:00 to 17:00:00, Friday: 09:00:00 to 17:00:00, Saturday: 09:00:00 to 17:00:00, Sunday: Closed"
  },
  {
    "Date": "2026-01-15 12:50:42",
    "Store": "Salvos",
    "StoreID": "8124",
    "Suburb": "Helensburgh",
    "Address": "1/123 - 127 Parkes Street<br>Helensburgh NSW 2508",
    "Latitude": "-34.1909246",
    "Longitude": "150.9794434",
    "Hours": "Monday: 10:00:00 to 17:00:00, Tuesday: 08:00:00 to 17:00:00, Wednesday: 08:00:00 to 17:00:00, Thursday: 08:00:00 to 17:00:00, Friday: 08:00:00 to 17:00:00, Saturday: 08:00:00 to 17:00:00, Sunday: Closed"
  },
  {
    "Date": "2026-01-15 12:50:42",
    "Store": "Salvos",
    "StoreID": "0715",
    "Suburb": "Burnie",
    "Address": "5 Ladbrooke  Street<br>Burnie TAS 7320",
    "Latitude": "-41.0536766",
    "Longitude": "145.9062903",
    "Hours": "Monday: 10:00:00 to 17:00:00, Tuesday: 09:00:00 to 17:00:00, Wednesday: 09:00:00 to 17:00:00, Thursday: 09:00:00 to 17:00:00, Friday: 09:00:00 to 17:00:00, Saturday: 10:00:00 to 16:00:00, Sunday: Closed"
  },
  {
    "Date": "2026-01-15 12:50:42",
    "Store": "Salvos",
    "StoreID": "8607",
    "Suburb": "Belconnen",
    "Address": "Units 3&4/38-40 Weedon Close<br>Belconnen ACT 2617",
    "Latitude": "-35.2418099",
    "Longitude": "149.0608735",
    "Hours": "Monday: 10:00:00 to 17:00:00, Tuesday: 09:00:00 to 17:00:00, Wednesday: 09:00:00 to 17:00:00, Thursday: 09:00:00 to 17:00:00, Friday: 09:00:00 to 17:00:00, Saturday: 09:00:00 to 17:00:00, Sunday: Closed"
  },
  {
    "Date": "2026-01-15 12:50:42",
    "Store": "Salvos",
    "StoreID": "8609",
    "Suburb": "Weston",
    "Address": "14 Trennery Street<br>Weston ACT 2611",
    "Latitude": "-35.3410121",
    "Longitude": "149.0491893",
    "Hours": "Monday: 10:00:00 to 17:00:00, Tuesday: 09:00:00 to 17:00:00, Wednesday: 09:00:00 to 17:00:00, Thursday: 09:00:00 to 17:00:00, Friday: 09:00:00 to 17:00:00, Saturday: 09:00:00 to 17:00:00, Sunday: Closed"
  },
  {
    "Date": "2026-01-15 12:50:42",
    "Store": "Salvos",
    "StoreID": "8706",
    "Suburb": "Morayfield",
    "Address": "T03, 321 \u2013 343  Morayfield Road<br>Morayfield QLD 4506",
    "Latitude": "-27.11755",
    "Longitude": "152.9549336",
    "Hours": "Monday: 10:00:00 to 17:30:00, Tuesday: 09:00:00 to 17:30:00, Wednesday: 09:00:00 to 17:30:00, Thursday: 09:00:00 to 17:30:00, Friday: 09:00:00 to 17:30:00, Saturday: 09:00:00 to 17:00:00, Sunday: Closed"
  },
  {
    "Date": "2026-01-15 12:50:42",
    "Store": "Salvos",
    "StoreID": "8699",
    "Suburb": "Mt Gravatt",
    "Address": "1/1478 Logan Road<br>Mt Gravatt QLD 4122",
    "Latitude": "-27.536502",
    "Longitude": "153.0777452",
    "Hours": "Monday: 10:00:00 to 17:30:00, Tuesday: 09:00:00 to 17:30:00, Wednesday: 09:00:00 to 17:30:00, Thursday: 09:00:00 to 17:30:00, Friday: 09:00:00 to 17:30:00, Saturday: 09:00:00 to 17:00:00, Sunday: Closed"
  },
  {
    "Date": "2026-01-15 12:50:42",
    "Store": "Salvos",
    "StoreID": "8753",
    "Suburb": "Nerang",
    "Address": "Shops 4&5 / 23-25 Station Street<br>Nerang QLD 4211",
    "Latitude": "-27.9946019",
    "Longitude": "153.3372148",
    "Hours": "Monday: 10:00:00 to 17:30:00, Tuesday: 09:00:00 to 17:30:00, Wednesday: 09:00:00 to 17:30:00, Thursday: 09:00:00 to 17:30:00, Friday: 09:00:00 to 17:30:00, Saturday: 09:00:00 to 17:00:00, Sunday: Closed"
  },
  {
    "Date": "2026-01-15 12:50:42",
    "Store": "Salvos",
    "StoreID": "8698",
    "Suburb": "Newstead",
    "Address": "142-160  Breakfast Creek Road<br>Newstead QLD 4006",
    "Latitude": "-27.443301",
    "Longitude": "153.043177",
    "Hours": "Monday: 10:00:00 to 17:30:00, Tuesday: 09:00:00 to 17:30:00, Wednesday: 09:00:00 to 17:30:00, Thursday: 09:00:00 to 17:30:00, Friday: 09:00:00 to 17:30:00, Saturday: 09:00:00 to 17:00:00, Sunday: Closed"
  },
  {
    "Date": "2026-01-15 12:50:42",
    "Store": "Salvos",
    "StoreID": "8765",
    "Suburb": "Oxenford",
    "Address": "Shops 2&3 / 160 Old Pacific Highway<br>Oxenford QLD 4210",
    "Latitude": "-27.890563",
    "Longitude": "153.3113642",
    "Hours": "Monday: 10:00:00 to 17:30:00, Tuesday: 09:00:00 to 17:30:00, Wednesday: 09:00:00 to 17:30:00, Thursday: 09:00:00 to 17:30:00, Friday: 09:00:00 to 17:30:00, Saturday: 09:00:00 to 17:00:00, Sunday: Closed"
  },
]

if __name__ == "__main__":
    main(None, PayloadTesting=True, payload=payload)