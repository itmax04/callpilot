-- Количество входных/принятых: манифест хранится JSON, а calls — принятые записи.
SELECT COUNT(*) AS accepted_calls FROM calls;
SELECT COUNT(*) AS input_files FROM calls;
-- Дубликаты/ошибки/CRM-связи — источник истины manifest.json для статусов файлов.
SELECT COUNT(*) AS calls_without_crm FROM calls c LEFT JOIN deals d ON d.deal_id=c.deal_id WHERE c.deal_id IS NULL OR d.deal_id IS NULL;
SELECT d.stage, COUNT(DISTINCT c.call_id) AS calls, COUNT(DISTINCT d.deal_id) AS deals
FROM calls c LEFT JOIN deals d ON c.deal_id=d.deal_id GROUP BY d.stage;
-- Сумма сделок считается по таблице deals один раз, поэтому одинаковые суммы разных сделок не теряются.
SELECT stage, COUNT(*) AS deals, SUM(amount) AS deal_amount_once FROM deals GROUP BY stage;
-- Распределение статусов по критериям (SQLite json_each; PostgreSQL замените на jsonb_array_elements).
SELECT json_extract(j.value,'$.criterion_id') criterion_id, json_extract(j.value,'$.status') status, COUNT(*)
FROM evaluations e, json_each(e.result_json,'$.criteria') j GROUP BY 1,2;
-- Средняя оценка с покрытием: рассчитывайте из evaluations, исключая N/A и insufficient_data.
-- Сумма сделок агрегируется по DISTINCT deal_id и не называется выручкой.
SELECT r.prompt_version, AVG(json_extract(j.value,'$.status')='met') AS raw_met_rate, COUNT(*) AS criterion_rows
FROM evaluations e JOIN runs r ON r.run_id=e.run_id, json_each(e.result_json,'$.criteria') j
WHERE json_extract(j.value,'$.status') IN ('met','not_met') GROUP BY r.prompt_version;
