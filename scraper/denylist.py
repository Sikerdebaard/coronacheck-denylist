import pandas as pd
import json
import base64
import seaborn as sns
import matplotlib.pyplot as plt
import pytz

from coronacheck_tools.verification.verifier import readconfig, cconfig
from pathlib import Path
from datetime import datetime

tz = pytz.timezone('Europe/Amsterdam')
today = str(datetime.now(tz).date())
outdir = Path('data/')

def decode_denylist(denylist):
    return {base64.b64decode(k).hex(): v for k, v in denylist.items()}


cconfig()  # clear mobilecore config - make sure we are not using cached results
config = readconfig()
domestic_denylist = config['mobilecore']['config']['domesticVerificationRules']['proofIdentifierDenylist']
ehc_denylist = config['mobilecore']['config']['europeanVerificationRules']['proofIdentifierDenylist']

denylist = {'international': decode_denylist(ehc_denylist), 'national': decode_denylist(domestic_denylist)}

with open(outdir / f'{today}-denylist.json', 'w') as fh:
    json.dump(denylist, fh)

denylist_file = outdir / 'latest-denylist.csv'
denylist_today_file = outdir / f'{today}-denylist.csv'

if denylist_file.exists():
    df_denylist = pd.read_csv(denylist_file, index_col=0)
    df_denylist.index = pd.to_datetime(df_denylist.index)
else:
    df_denylist = pd.DataFrame(index=pd.to_datetime([]))

ptoday = pd.to_datetime(today)
if ptoday in df_denylist.index:
    print('Today already in denylist, synchronizing...')
    
df_denylist.at[ptoday, 'num_international'] = len(denylist['international'])
df_denylist.at[ptoday, 'num_national'] = len(denylist['national'])
df_denylist.at[ptoday, 'num_total'] = df_denylist.at[ptoday, 'num_international'] + df_denylist.at[ptoday, 'num_national']

df_denylist.at[pd.to_datetime('2021-10-12'), 'num_international'] = 0
df_denylist.at[pd.to_datetime('2021-10-12'), 'num_national'] = 0
df_denylist.at[pd.to_datetime('2021-10-12'), 'num_total'] = 0

df_denylist.at[pd.to_datetime('2021-10-13'), 'num_international'] = 13
df_denylist.at[pd.to_datetime('2021-10-13'), 'num_national'] = 10
df_denylist.at[pd.to_datetime('2021-10-13'), 'num_total'] = 23

df_denylist.sort_index(inplace=True)
df_denylist = df_denylist.resample('D').last().ffill()

df_denylist = df_denylist.astype('int64')
df_denylist.index.rename('date', inplace=True)

df_denylist.to_csv(denylist_file)
df_denylist.to_csv(denylist_today_file)



# plot

sns.set_style("whitegrid")

ax = df_denylist.plot(grid=True, figsize=(8, 6), title='Absolute number of QR codes revoked by the Dutch government')
ax.legend(loc='upper left')

ax.set_ylim((0,df_denylist.max().max() * 1.1))

plt.tight_layout()

fig = ax.get_figure()
fig.savefig(outdir / 'denylist-chart.png', dpi=150)

