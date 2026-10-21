-- PBC-FA-01  Fixed asset rollforward, GL-based (works in every account, no FAM SuiteApp needed).
-- Long format: Python pivots into Opening | Additions | Disposals | Depreciation | Other | Closing
-- using the tenant's account map (cost vs accumulated depreciation vs depreciation expense).
-- Account selection below is a placeholder: BAS 11xx-12xx. Replace with the tenant account map.
SELECT 'OPENING' AS bucket, a.id AS account_id, a.acctnumber AS account_no,
       a.accountsearchdisplayname AS account_name,
       t.subsidiary AS subsidiary_id,                                   /*OW*/
       CAST(NULL AS VARCHAR(20)) AS tran_type,
       SUM(tal.debit) AS debit, SUM(tal.credit) AS credit, SUM(tal.amount) AS net
FROM transactionaccountingline tal
JOIN transaction t       ON t.id  = tal.transaction
JOIN account a           ON a.id  = tal.account
JOIN accountingperiod ap ON ap.id = t.postingperiod
WHERE tal.posting = 'T'
  AND tal.accountingbook IN (SELECT id FROM accountingbook WHERE isprimary = 'T')
  AND a.acctnumber BETWEEN '1100' AND '1299'
  AND ap.enddate < TO_DATE('2025-01-01','YYYY-MM-DD')
GROUP BY a.id, a.acctnumber, a.accountsearchdisplayname, t.subsidiary   /*OW: drop t.subsidiary*/
UNION ALL
SELECT 'MOVEMENT', a.id, a.acctnumber, a.accountsearchdisplayname,
       t.subsidiary,                                                    /*OW*/
       t.type, SUM(tal.debit), SUM(tal.credit), SUM(tal.amount)
FROM transactionaccountingline tal
JOIN transaction t       ON t.id  = tal.transaction
JOIN account a           ON a.id  = tal.account
JOIN accountingperiod ap ON ap.id = t.postingperiod
WHERE tal.posting = 'T'
  AND tal.accountingbook IN (SELECT id FROM accountingbook WHERE isprimary = 'T')
  AND a.acctnumber BETWEEN '1100' AND '1299'
  AND ap.startdate >= TO_DATE('2025-01-01','YYYY-MM-DD')
  AND ap.enddate   <= TO_DATE('2025-12-31','YYYY-MM-DD')
GROUP BY a.id, a.acctnumber, a.accountsearchdisplayname, t.subsidiary, t.type;  /*OW: drop t.subsidiary*/
-- Drill-down for each movement cell = same WHERE, no GROUP BY, returning t.id.
-- Register-level (per asset) variant: Oracle FAM custom records customrecord_ncfar_asset /
-- customrecord_ncfar_assethistory - verify field ids in the account (see docs/query-design.md section 6).
