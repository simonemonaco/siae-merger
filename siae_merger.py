import streamlit as st
import pandas as pd
import warnings
import re

st.header('SIAE Merger [NEW]')
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
		with open(rep, 'r') as f:
			column_index = 0
			while (column_index := column_index + 1):
				if 'CODICE OPERA' in f.readline(): break
		report = pd.read_csv(rep, sep=';', skiprows=column_index-1, decimal=',', thousands='.')
	elif rep.name.lower().endswith('xlsx'):
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			column_index = pd.read_excel(rep, header=None).iloc[:, 0].tolist().index('CLASSE')
			report = pd.read_excel(rep, skiprows=column_index)
	
	report = report.dropna(subset=['CODICE OPERA'])
	report = report[~report['CODICE OPERA'].eq('TOTALE')]
	report['CODICE OPERA'] = report['CODICE OPERA'].astype(int).astype(str)

	anno, semestre = re.findall(r'(\d{4})[-_](\d)', rep.name)[0][:2]	
	report = report.drop_duplicates().rename(columns={
									'TITOLO OPERA': 'TITOLO OPERE', 
								    'CLASSE': 'CLASSE DI RIPARTIZIONE', 
									'MATURATO': f'MATURATO {anno} - {semestre}'})
	report = report[report['CODICE OPERA'].notna() & ~report['CODICE OPERA'].eq('TOTALE') & ~report['CLASSE DI RIPARTIZIONE'].eq('TOTALE')]
	report = report.groupby(['CODICE OPERA', 'CLASSE DI RIPARTIZIONE']).agg({
		'TITOLO OPERE': 'first',
		# merge le classi di ripartizione disponibili, separate da virgola
		f'MATURATO {anno} - {semestre}': 'sum'
	})
	
	if full is None:
		full = report
	else:
		if f"MATURATO {anno} - {semestre}" not in full.columns:
			full = full.join(report, how='outer', rsuffix='_new', on=['CODICE OPERA', 'CLASSE DI RIPARTIZIONE'])
			full['TITOLO OPERE'] = full[['TITOLO OPERE', 'TITOLO OPERE_new']].apply(lambda x: x[0] if not isinstance(x[0], float) else x[1], axis=1)
			full = full.drop(columns=['TITOLO OPERE_new'])

if full is not None:
	full = full.reset_index()[['TITOLO OPERE', 'CLASSE DI RIPARTIZIONE'] + sorted([c for c in full.columns if c.startswith('MATURATO')])].drop_duplicates()
	full[[c for c in full.columns if c.startswith('MATURATO')]] = full[[c for c in full.columns if c.startswith('MATURATO')]].round(2)

	st.write('Scarica il file')
	st.download_button('Download', key='dl', data=pd.DataFrame.to_csv(full, encoding='utf-8'), file_name='SIAEE.csv', mime='text/csv')
