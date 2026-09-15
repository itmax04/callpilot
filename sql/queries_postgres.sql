-- PostgreSQL-вариант проверок для JSON-текста, сохранённого в TEXT.
SELECT COUNT(*) AS accepted_calls FROM calls;
SELECT status, COUNT(*) FROM manifest GROUP BY status;
SELECT COUNT(*) AS calls_without_crm FROM calls c LEFT JOIN deals d ON d.deal_id=c.deal_id WHERE c.deal_id IS NULL OR d.deal_id IS NULL;
SELECT d.stage, COUNT(DISTINCT c.call_id) AS calls, COUNT(DISTINCT d.deal_id) AS deals
FROM calls c LEFT JOIN deals d ON d.deal_id=c.deal_id GROUP BY d.stage;
SELECT stage, COUNT(*) AS deals, SUM(amount) AS deal_amount_once FROM deals GROUP BY stage;
SELECT (j->>'criterion_id')::int AS criterion_id, j->>'status' AS status, COUNT(*)
FROM evaluations e CROSS JOIN LATERAL jsonb_array_elements(e.result_json::jsonb->'criteria') j
GROUP BY 1,2 ORDER BY 1,2;
SELECT r.prompt_version,
       AVG(CASE WHEN j->>'status'='met' THEN 1.0 ELSE 0 END) AS usable_met_rate,
       COUNT(*) AS usable_criterion_rows
FROM evaluations e JOIN runs r ON r.run_id=e.run_id
CROSS JOIN LATERAL jsonb_array_elements(e.result_json::jsonb->'criteria') j
WHERE j->>'status' IN ('met','not_met') GROUP BY r.prompt_version;
WITH criteria AS (
 SELECT e.run_id,e.call_id,j->>'status' AS status
 FROM evaluations e CROSS JOIN LATERAL jsonb_array_elements(e.result_json::jsonb->'criteria') j
), per_call AS (
 SELECT run_id,call_id,
   COUNT(*) FILTER (WHERE status='met') AS met_n,
   COUNT(*) FILTER (WHERE status IN ('met','not_met')) AS usable_n,
   COUNT(*) AS criterion_n
 FROM criteria GROUP BY run_id,call_id
)
SELECT r.prompt_version,
 AVG(CASE WHEN p.usable_n=0 THEN NULL ELSE p.met_n::numeric/p.usable_n END) AS average_score,
 AVG(p.usable_n::numeric/p.criterion_n) AS coverage,
 COUNT(*) AS calls
FROM per_call p JOIN runs r ON r.run_id=p.run_id GROUP BY r.prompt_version;
