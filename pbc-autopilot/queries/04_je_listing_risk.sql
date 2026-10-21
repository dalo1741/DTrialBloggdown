-- PBC-JE-01  Journal entry listing with configurable risk flags (line level, posting lines only).
-- Inner query computes 0/1 flags; outer query applies the tenant's threshold (risk_score >= N).
-- Each flag = one entry in the tenant's risk-rule config, so rules can be switched on/off per client.
SELECT * FROM (
  SELECT
    t.id AS tran_id, t.tranid AS je_no, t.trandate AS tran_date,
    ap.periodname AS period, ap.isadjust AS is_adj_period,
    t.createddate AS created_at, e.entityid AS created_by,
    t.subsidiary AS subsidiary_id,                                      /*OW*/
    a.acctnumber AS account_no, a.accountsearchdisplayname AS account_name, a.accttype AS account_type,
    tl.memo AS line_memo, t.memo AS header_memo,
    tal.debit, tal.credit, tal.amount,
    -- flags ---------------------------------------------------------------
    CASE WHEN MOD(TRUNC(t.trandate) - TO_DATE('1900-01-06','YYYY-MM-DD'), 7) IN (0,1)
         THEN 1 ELSE 0 END                                              AS f_weekend_posting,
    CASE WHEN TRUNC(t.createddate) > ap.enddate THEN 1 ELSE 0 END       AS f_post_period_end,
    CASE WHEN ap.isadjust = 'T' THEN 1 ELSE 0 END                       AS f_adjustment_period,
    CASE WHEN tal.amount <> 0 AND MOD(ABS(tal.amount), 1000) = 0
         THEN 1 ELSE 0 END                                              AS f_round_amount,
    CASE WHEN ABS(tal.amount) >= 500000 THEN 1 ELSE 0 END               AS f_above_threshold,
    CASE WHEN t.memo IS NULL AND tl.memo IS NULL THEN 1 ELSE 0 END      AS f_no_description,
    CASE WHEN LOWER(NVL(tl.memo, t.memo)) LIKE '%correction%'
           OR LOWER(NVL(tl.memo, t.memo)) LIKE '%adjust%'
           OR LOWER(NVL(tl.memo, t.memo)) LIKE '%korrigering%'
           OR LOWER(NVL(tl.memo, t.memo)) LIKE '%justering%'
         THEN 1 ELSE 0 END                                              AS f_keyword,
    CASE WHEN a.accttype IN ('Income','OthIncome','Bank') THEN 1 ELSE 0 END AS f_sensitive_account,
    CASE WHEN t.reversaldate IS NOT NULL THEN 1 ELSE 0 END              AS f_reversing
  FROM transaction t
  JOIN transactionaccountingline tal ON tal.transaction = t.id
  JOIN transactionline tl            ON tl.transaction = tal.transaction AND tl.id = tal.transactionline
  JOIN account a                     ON a.id  = tal.account
  JOIN accountingperiod ap           ON ap.id = t.postingperiod
  LEFT JOIN employee e               ON e.id  = t.createdby
  WHERE t.type = 'Journal'
    AND tal.posting = 'T'
    AND tal.accountingbook IN (SELECT id FROM accountingbook WHERE isprimary = 'T')
    AND ap.startdate >= TO_DATE('2025-01-01','YYYY-MM-DD')
    AND ap.enddate   <= TO_DATE('2025-12-31','YYYY-MM-DD')
    AND t.subsidiary IN (1,2,3)                                         /*OW*/
) x
WHERE (f_weekend_posting + f_post_period_end + f_adjustment_period + f_round_amount
     + f_above_threshold + f_no_description + f_keyword + f_sensitive_account + f_reversing) >= 1
ORDER BY tran_date, je_no;
-- Completeness control (IPE): run the same WHERE without the outer filter and show
-- SUM(debit)=SUM(credit) per JE and population totals vs. TB movement.
