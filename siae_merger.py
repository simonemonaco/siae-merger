import streamlit as st
import pandas as pd

st.header('SIAEE Merger')
upload_files = st.file_uploader('', accept_multiple_files=True, type=['csv'])
css='''
<style>
[data-testid="stFileUploadDropzone"] div div::before {content:"Trascina i file da unire qui"}
[data-testid="stFileUploadDropzone"] div div span{display:none;}
[data-testid="stFileUploadDropzone"] div div::after {font-size: .8em; content:"Limite 200Mb per file • CSV"}
[data-testid="stFileUploadDropzone"] div div small{display:none;}
</style>
'''

st.markdown(css, unsafe_allow_html=True)
	
full = None
for rep in upload_files:
	report = pd.read_csv(rep, sep=';', header=4)
	report = report[report['CODICE OPERA'] != 'TOTALE']
	report = report.set_index('CODICE OPERA')
	if full is None:
		full = report
	else:
		full = full.join(report, how='outer', rsuffix='_new')
		full['TITOLO OPERE'] = full[['TITOLO OPERE', 'TITOLO OPERE_new']].apply(lambda x: x[0] if not isinstance(x[0], float) else x[1], axis=1)
		full['CLASSE DI RIPARTIZIONE'] = full[['CLASSE DI RIPARTIZIONE', 'CLASSE DI RIPARTIZIONE_new']].apply(lambda x: x[0] if not isinstance(x[0], float) else x[1], axis=1)

if full is not None:
	full = full[['TITOLO OPERE', 'CLASSE DI RIPARTIZIONE'] + sorted([c for c in full.columns if c.startswith('MATURATO')])]

	st.write('Scarica il file')
	st.download_button('Download', key='dl', data=pd.DataFrame.to_csv(full, encoding='utf-8'), file_name='SIAEE.csv', mime='text/csv')