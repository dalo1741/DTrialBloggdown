-- PBC-AP-01  AP aging / Leverantörsreskontra as of a historical date (bills; credits/prepayments mirror AR).
-- NB: for bills t.tranid is the VENDOR's invoice ref; the NetSuite number is t.transactionnumber.
-- Bills pending approval are non-posting and drop out via posting='T' - list them separately
-- in the cut-off schedule (completeness of liabilities).
SELECT
  b.id                 AS tran_id,
  b.type               AS tran_type,
  b.tranid             AS vendor_invoice_no,
  b.transactionnumber  AS ns_doc_no,
  b.trandate           AS tran_date,
  b.duedate            AS due_date,
  v.id                 AS vendor_id,
  v.entityid           AS vendor_no,
  v.companyname        AS vendor_name,
  b.subsidiary         AS subsidiary_id,                               /*OW*/
  cur.symbol           AS currency,
  ABS(b.foreigntotal)                                        AS original_fc,
  NVL(app.applied_fc, 0)                                     AS applied_to_asof_fc,
  ABS(b.foreigntotal) - NVL(app.applied_fc, 0)               AS open_fc_asof,
  (ABS(b.foreigntotal) - NVL(app.applied_fc, 0)) * b.exchangerate AS open_base_at_tran_rate,
  TO_DATE('2025-12-31','YYYY-MM-DD') - b.duedate             AS days_past_due
FROM transaction b
JOIN vendor v     ON v.id   = b.entity
JOIN currency cur ON cur.id = b.currency
LEFT JOIN (
  SELECT ntl.previousdoc AS bill_id, SUM(ABS(ntl.foreignamount)) AS applied_fc
  FROM NextTransactionLineLink ntl
  JOIN transaction pay ON pay.id = ntl.nextdoc
  WHERE ntl.linktype = 'Payment'
    AND pay.trandate <= TO_DATE('2025-12-31','YYYY-MM-DD')
  GROUP BY ntl.previousdoc
) app ON app.bill_id = b.id
WHERE b.type = 'VendBill'
  AND b.posting = 'T'
  AND b.voided  = 'F'
  AND b.trandate <= TO_DATE('2025-12-31','YYYY-MM-DD')
  AND ABS(b.foreigntotal) - NVL(app.applied_fc, 0) <> 0
ORDER BY v.entityid, b.duedate;
-- Control: same GL tie-out as AR, with a.accttype = 'AcctPay'.
