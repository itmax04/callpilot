# Runbook

1. Создайте `.env` из `.env.example`, установите зависимости и выполните `python -m callpilot.cli all` и `python -m pytest -q`.
2. Для повторного запуска используйте ту же команду: исходники не изменяются, DB upsert и ключи запуска не дублируют оценки внутри запуска.
3. Ошибка demo-фикстуры о неизвестном звонке — ожидаемая защита от выдуманного анализа. Live без `OPENAI_API_KEY` или без `CALLPILOT_ALLOW_PAID_LIVE=true` блокируется. Лимит `CALLPILOT_MAX_REQUESTS` учитывает две версии и повторы; ошибка API не заменяется demo.
4. `streamlit run callpilot/streamlit_app.py` открывает UI. SQL-проверки находятся в `sql/queries.sql`; подробные строки оценок — `outputs/analysis_results.csv`, расхождения — `outputs/discrepancies.csv`.
5. PostgreSQL: `docker compose up -d`, задайте URL из README. Облако: см. `azure/README.md`; deployment, ключи и платные ресурсы вручную и не выполняются проектом.
