import csv, json
from pathlib import Path
from .metrics import classification_metrics, evidence_stats, score
from .models import Status

def compare(results_by_version, gold_path, out_dir):
    gold=json.loads(Path(gold_path).read_text()); rows=[]; summary={}
    answers={}
    for version,results in results_by_version.items():
        gs=[]; ps=[]
        for r in results:
            if r.call_id not in gold:
                continue  # quality-warning fixtures can be analysed, but have no gold label
            if not r.criteria:
                continue  # failed calls are reported separately, never silently scored
            for g,p in zip(gold[r.call_id]['criteria'],r.criteria):
                gs.append(g['status']); ps.append(p.status.value)
                key=(r.call_id,p.criterion_id)
                answers.setdefault(key, {'call_id':r.call_id,'criterion_id':p.criterion_id,'gold':g['status'],'gold_evidence':json.dumps(g.get('quotes',[]),ensure_ascii=False)})
                answers[key]['answer_'+version]=p.status.value
                answers[key]['evidence_'+version]=json.dumps(p.quotes,ensure_ascii=False)
                if g['status']!=p.status.value or any(not x['valid'] for x in r.evidence_checks if x['criterion_id']==p.criterion_id): answers[key]['error_category']=('status_mismatch' if g['status']!=p.status.value else 'invalid_quote')
        summary[version]={**classification_metrics(gs,ps),'evidence':evidence_stats(results),'calls_success':sum(r.provider_status in ('success','demo') for r in results),'calls_failed':sum(r.provider_status not in ('success','demo') for r in results),'coverage':sum(score(r.criteria)[1] for r in results)/(len(results)*7) if results else 0}
    out_dir.mkdir(exist_ok=True)
    with (out_dir/'discrepancies.csv').open('w',newline='') as f:
      w=csv.DictWriter(f,fieldnames=['call_id','criterion_id','gold','answer_v1','answer_v2','gold_evidence','answer_evidence','error_category']); w.writeheader();
      for row in answers.values():
        if 'error_category' in row:
          row['answer_evidence']=row.get('evidence_v2',row.get('evidence_v1',''))
          w.writerow({k:row.get(k,'') for k in w.fieldnames})
    return summary

def write_report(summary, manifest, run_ids, out_dir):
    accepted=sum(x['status'] in ('accepted','warning') for x in manifest); rejected=sum(x['status']=='rejected' for x in manifest); dups=sum(x['status']=='duplicate' for x in manifest); warnings=sum(x['status']=='warning' for x in manifest)
    catalog_accepted=sum(x['status'] in ('accepted','warning') and x['record_id'].startswith('CALL-') for x in manifest)
    lines=['# CallPilot — отчёт руководителю','', '**Статус:** demo; ответы — демонстрационные фикстуры, не реальная оценка LLM.','',f'- Принято записей каталога: **{catalog_accepted}**',f'- Отклонено проблемных файлов: **{rejected}**',f'- Дубликатов: **{dups}**',f'- Предупреждений качества (CRM/идентификаторы): **{warnings}**',f'- Запуски: `{", ".join(run_ids)}`','', '## Результаты проверки механизма оценивания','', '|Версия|accuracy|macro-F1|coverage|успешно|неуспешно|проверяемые цитаты|некорректные|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for v,s in summary.items(): lines.append(f"|{v}|{s['accuracy']:.3f}|{s['macro_f1']:.3f}|{s['coverage']:.3f}|{s['calls_success']}|{s['calls_failed']}|{s['evidence']['checked_quotes']}|{s['evidence']['invalid_quotes']}|")
    lines += ['', 'Метрики рассчитаны кодом по синтетической AI-подготовленной эталонной разметке, которая требует человеческой проверки. Holdout не является независимой итоговой проверкой; выборка мала и синтетична. Live-метрики отсутствуют.', '', '## Ограничения и рекомендации', '- Наблюдение: проблемные файлы показывают дубли, пустые/некорректные записи и отсутствующие сделки; перед пилотом нужен контроль качества загрузки.', '- Наблюдение: доля `insufficient_data` и отсутствие финальных реплик ограничивают покрытие; полезно собирать полный конец разговора.', '- Гипотеза: уточнение правил доказательств в v2 снизит ошибки цитирования; проверить это разрешённым live-прогоном и человеческой разметкой.', '', 'Исходные записи и SQL-проверки: `data/transcripts/`, `sql/`, `outputs/discrepancies.csv`.']
    (out_dir/'manager_report.md').write_text('\n'.join(lines)+'\n')
