# CallPilot

Небольшой учебный pet-проект для анализа качества синтетических звонков продаж. Он показывает подготовку данных, воспроизводимый запуск промптов, проверку цитат, сравнение v1/v2 и отчётность. Проект не разработан для Deyteris, не использует закрытую методику и не подключается к настоящей CRM.

## Возможности

- 24 синтетические русско-украинские расшифровки, CRM CSV, проблемные фикстуры и манифест SHA-256.
- 7-критериальная открытая рубрика, статусы и строгий Pydantic-контракт.
- Безсетевой demo-провайдер и отдельный OpenAI Responses API live-адаптер с JSON Schema, таймаутом, лимитом запросов и флагом разрешения расходов.
- SQLAlchemy/PostgreSQL-совместимое хранилище, Streamlit, CSV расхождений, Markdown-отчёт.
- Azure Functions HTTP-trigger/Bicep как непроверенный облачный дополнительный путь.

## Быстрый запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.lock
pip install -e '.[test]'
cp .env.example .env
python -m callpilot.cli all
python -m pytest -q
streamlit run callpilot/streamlit_app.py
```

Результаты (включая готовый demo-отчёт): `outputs/manager_report.md`, `outputs/manifest.json`, `outputs/summary.json`, `outputs/discrepancies.csv`, `outputs/callpilot.db`. Demo не требует ключа и не делает сетевых запросов. Для PostgreSQL: `docker compose up -d`, задайте `CALLPILOT_DATABASE_URL=postgresql+psycopg://callpilot:callpilot_local_only@localhost:5432/callpilot` и повторите команду. Если Docker недоступен, локально проверяется SQLite, это не доказательство PostgreSQL-интеграции.

## Поток данных

```mermaid
flowchart LR
 A[transcripts + CRM] --> B[ingest + manifest]
 B --> C[demo/live provider]
 C --> D[Pydantic validation + quote check]
 D --> E[SQLAlchemy]
 D --> F[metrics + discrepancies]
 E --> G[Streamlit]
 F --> H[manager_report.md]
```

## Пример результата

В отчёте видны accuracy, macro-F1, покрытие, успешные/неуспешные вызовы и некорректные цитаты по v1/v2. Это проверка механизма на синтетических фикстурах, а не измерение качества модели. Live-результаты требуют ключа, явного разрешения расходов и человеческой проверки разметки.
