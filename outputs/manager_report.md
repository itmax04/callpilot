# CallPilot — отчёт руководителю

**Статус:** demo; ответы — демонстрационные фикстуры, не реальная оценка LLM.

- Принято записей каталога: **24**
- Отклонено проблемных файлов: **2**
- Дубликатов: **1**
- Предупреждений качества (CRM/идентификаторы): **3**
- Запуски: `demo-all-v1-f04aa0c7aba692e6, demo-all-v2-56b60468558b1ce9`

## Результаты проверки механизма оценивания

|Версия|accuracy|macro-F1|coverage|успешно|неуспешно|проверяемые цитаты|некорректные|
|---|---:|---:|---:|---:|---:|---:|---:|
|v1|0.976|0.940|0.831|27|0|238|2|
|v2|0.982|0.969|0.794|27|0|238|1|

## Исходные записи
- [CALL-001](../data/transcripts/CALL-001.json)
- [CALL-002](../data/transcripts/CALL-002.json)
- [CALL-003](../data/transcripts/CALL-003.json)
- [CALL-004](../data/transcripts/CALL-004.json)
- [CALL-005](../data/transcripts/CALL-005.json)
- [CALL-006](../data/transcripts/CALL-006.json)
- [CALL-007](../data/transcripts/CALL-007.json)
- [CALL-008](../data/transcripts/CALL-008.json)
- [CALL-009](../data/transcripts/CALL-009.json)
- [CALL-010](../data/transcripts/CALL-010.json)
- [CALL-011](../data/transcripts/CALL-011.json)
- [CALL-012](../data/transcripts/CALL-012.json)
- [CALL-013](../data/transcripts/CALL-013.json)
- [CALL-014](../data/transcripts/CALL-014.json)
- [CALL-015](../data/transcripts/CALL-015.json)
- [CALL-016](../data/transcripts/CALL-016.json)
- [CALL-017](../data/transcripts/CALL-017.json)
- [CALL-018](../data/transcripts/CALL-018.json)
- [CALL-019](../data/transcripts/CALL-019.json)
- [CALL-020](../data/transcripts/CALL-020.json)
- [CALL-021](../data/transcripts/CALL-021.json)
- [CALL-022](../data/transcripts/CALL-022.json)
- [CALL-023](../data/transcripts/CALL-023.json)
- [CALL-024](../data/transcripts/CALL-024.json)
- [missing_deal](../data/problematic/missing_deal.json)
- [prompt_injection](../data/problematic/prompt_injection.json)
- [unknown_deal](../data/problematic/unknown_deal.json)

Метрики рассчитаны кодом по синтетической AI-подготовленной эталонной разметке, которая требует человеческой проверки. Accuracy/macro-F1 используют только 24 записи каталога с эталоном; три warning-фикстуры анализируются, но не входят в этот знаменатель. Coverage и число успешных вызовов относятся ко всем 27 проанализированным записям. Holdout не является независимой итоговой проверкой; выборка мала и синтетична. Live-метрики отсутствуют.

## Ограничения и рекомендации
- Наблюдение: проблемные файлы показывают дубли, пустые/некорректные записи и отсутствующие сделки; перед пилотом нужен контроль качества загрузки.
- Наблюдение: доля `insufficient_data` и отсутствие финальных реплик ограничивают покрытие; полезно собирать полный конец разговора.
- Гипотеза: уточнение правил доказательств в v2 снизит ошибки цитирования; проверить это разрешённым live-прогоном и человеческой разметкой.

SQL-проверки: `sql/`, таблица ошибок: `outputs/discrepancies.csv`.
