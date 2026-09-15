import json, os
from pathlib import Path
import streamlit as st
st.set_page_config(page_title='CallPilot',layout='wide'); root=Path(__file__).resolve().parents[1]; out=root/'outputs'
mode=os.getenv('CALLPILOT_MODE','demo'); st.sidebar.metric('Режим',mode.upper()); st.sidebar.caption('DEMO: демонстрационные ответы, не реальная оценка LLM' if mode=='demo' else 'LIVE: нужен ключ и разрешение расходов')
tab1,tab2,tab3=st.tabs(['Данные и качество','Звонки','Сравнение и отчёт'])
with tab1:
 st.header('Загрузка и качество'); m=out/'manifest.json'
 if not m.exists(): st.info('Сначала выполните: python -m callpilot.cli all')
 else:
  rows=json.loads(m.read_text()); st.dataframe(rows,use_container_width=True); st.write({'всего':len(rows),'принято или предупреждение':sum(x['status'] in ('accepted','warning') for x in rows),'дубли':sum(x['status']=='duplicate' for x in rows),'ошибки':sum(x['status']=='rejected' for x in rows)})
with tab2:
 st.header('Карточки звонков'); files=sorted((root/'data/transcripts').glob('*.json')); selected=st.selectbox('Звонок',[p.stem for p in files]) if files else None
 if selected:
  rec=json.loads((root/'data/transcripts'/f'{selected}.json').read_text()); st.json(rec); ans=json.loads((root/'data/demo_answers_v2.json').read_text())[selected]; st.subheader('Оценка v2'); st.dataframe(ans['criteria'],use_container_width=True)
with tab3:
 st.header('Сравнение промптов и отчёт'); s=out/'summary.json'
 if s.exists(): st.json(json.loads(s.read_text()))
 report=out/'manager_report.md'
 if report.exists(): st.markdown(report.read_text())
