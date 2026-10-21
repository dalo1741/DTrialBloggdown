-- PBC-IC-01  Intercompany reconciliation. OneWorld ONLY - not applicable to single-subsidiary accounts
-- (use the related-party variant in docs/query-design.md section 7 there).
-- 06a: balance matrix per (subsidiary, counterparty) on IC accounts; Python nets A->B against B->A.
SELECT
  t.subsidiary                                   AS sub_id,
  COALESCE(c.representingsubsidiary, v.representingsubsidiary) AS counterparty_sub_id,
  a.id AS account_id, a.acctnumber AS account_no,
  SUM(tal.amount)                                AS balance_sub_ccy,
  -- translate to group currency so both legs are comparable (arg 5 = root subsidiary id, 6 = period id)
  SUM(BUILTIN.CONSOLIDATE(tal.amount, 'LEDGER', 'DEFAULT', 'DEFAULT', 1, 100, 'DEFAULT')) AS balance_group_ccy
FROM transactionaccountingline tal
JOIN transaction t       ON t.id  = tal.transaction
JOIN transactionline tl  ON tl.transaction = tal.transaction AND tl.id = tal.transactionline
JOIN account a           ON a.id  = tal.account
JOIN accountingperiod ap ON ap.id = t.postingperiod
LEFT JOIN customer c     ON c.id  = tl.entity
LEFT JOIN vendor   v     ON v.id  = tl.entity
WHERE tal.posting = 'T'
  AND tal.accountingbook IN (SELECT id FROM accountingbook WHERE isprimary = 'T')
  AND a.eliminate = 'T'                       -- or tenant-configured IC account list
  AND ap.enddate <= TO_DATE('2025-12-31','YYYY-MM-DD')
GROUP BY t.subsidiary, COALESCE(c.representingsubsidiary, v.representingsubsidiary), a.id, a.acctnumber;

-- 06b: transaction-level pairs and orphans (unmatched = no paired transaction on the other side).
SELECT
  a.id AS tran_id_a, a.tranid AS doc_no_a, a.type AS type_a, a.subsidiary AS sub_a, a.trandate AS date_a,
  a.foreigntotal AS amount_fc_a,
  b.id AS tran_id_b, b.tranid AS doc_no_b, b.type AS type_b, b.subsidiary AS sub_b, b.trandate AS date_b,
  b.foreigntotal AS amount_fc_b,
  CASE WHEN b.id IS NULL THEN 'ORPHAN' ELSE 'PAIRED' END AS match_status
FROM transaction a
LEFT JOIN transaction b ON b.id = a.intercotransaction
WHERE a.intercostatus IS NOT NULL
  AND a.trandate BETWEEN TO_DATE('2025-01-01','YYYY-MM-DD') AND TO_DATE('2025-12-31','YYYY-MM-DD')
ORDER BY a.trandate;
