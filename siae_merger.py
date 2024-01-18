import streamlit as st
import pandas as pd
import re

st.header('SIAE Merger')
upload_files = st.file_uploader('', accept_multiple_files=True, type=['csv', 'xlsx'])
css='''
<style>
[data-testid="stFileUploadDropzone"] div div::before {content:"Trascina i file da unire qui"}
[data-testid="stFileUploadDropzone"] div div span{display:none;}
[data-testid="stFileUploadDropzone"] div div::after {font-size: .8em; content:"Limite 200Mb per file • CSV/XLSX"}
[data-testid="stFileUploadDropzone"] div div small{display:none;}
</style>
'''

st.markdown(css, unsafe_allow_html=True)
	
full = None
for rep in upload_files:
	if rep.name.lower().endswith('csv'):
		report = pd.read_csv(rep, sep=';', header=4, decimal=',', thousands='.')
	elif rep.name.lower().endswith('xlsx'):
		report = pd.read_excel(rep, header=4, dtype=str, engine='openpyxl')
		report['MATURATO'] = report['MATURATO'].astype(float)
		
	anno, semestre = re.findall(r'(\d{4})[-_](\d)', rep.name)[0][:2]
	report = report.drop_duplicates().rename(columns={
									'TITOLO OPERA': 'TITOLO OPERE', 
								    'CLASSE': 'CLASSE DI RIPARTIZIONE', 
									'MATURATO': f'MATURATO {anno} - {semestre}'})
	report = report[report['CODICE OPERA'].notna() & ~report['CODICE OPERA'].eq('TOTALE') & ~report['CLASSE DI RIPARTIZIONE'].eq('TOTALE')]
	report = report.groupby(['CODICE OPERA', 'CLASSE DI RIPARTIZIONE']).agg({
		'TITOLO OPERE': 'first',
		f'MATURATO {anno} - {semestre}': 'sum'
	})
	
	if full is None:
		full = report
	else:
		full = full.join(report, how='outer', rsuffix='_new', on=['CODICE OPERA', 'CLASSE DI RIPARTIZIONE'])
		full['TITOLO OPERE'] = full[['TITOLO OPERE', 'TITOLO OPERE_new']].apply(lambda x: x[0] if not isinstance(x[0], float) else x[1], axis=1)
		full = full.drop(columns=['TITOLO OPERE_new'])

if full is not None:
	full = full[['TITOLO OPERE', 'CLASSE DI RIPARTIZIONE'] + sorted([c for c in full.columns if c.startswith('MATURATO')])].drop_duplicates()
	# remove ', ' at the beginning of the string of CLASSE DI RIPARTIZIONE, se presente
	full['CLASSE DI RIPARTIZIONE'] = full['CLASSE DI RIPARTIZIONE'].apply(lambda x: x[2:] if x.startswith(', ') else x)
	full[[c for c in full.columns if c.startswith('MATURATO')]] = full[[c for c in full.columns if c.startswith('MATURATO')]].round(2)

	st.write('Scarica il file')
	st.download_button('Download', key='dl', data=pd.DataFrame.to_csv(full, encoding='utf-8'), file_name='SIAEE.csv', mime='text/csv')
