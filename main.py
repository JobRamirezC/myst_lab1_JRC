"""
# -- --------------------------------------------------------------------------------------------------- -- #
# -- project: A SHORT DESCRIPTION OF THE PROJECT                                                         -- #
# -- script: main.py : python script with the main functionality                                         -- #
# -- author: YOUR GITHUB USER NAME                                                                       -- #
# -- license: GPL-3.0 License                                                                            -- #
# -- repository: YOUR REPOSITORY URL                                                                     -- #
# -- --------------------------------------------------------------------------------------------------- -- #
"""

import functions
from functions import *
from data import *
import pandas as pd

# Pasiva

abspath = path.abspath('files/NAFTRAC_holdings')  #

capital = 1000000
commission = 0.00125
inv_pasiva = {'timestamp': ['30-01-2018'], 'capital': [capital]}
path = f_pathnames(abspath)
tdates = f_fechas(path)
vdates = pd.date_range(start=f_fechas(path)[0], end=f_fechas(path)[-1])  #
vdates = vdates.strftime('%Y-%m-%d')  #
path = f_pathnames(abspath)
dictionary = f_dictionary(path)
price = f_yfprices(path)
price_close = price[0]
price_open = price[1]
m = f_mprices(price_close, path)

functions.f_pasiva(capital, m, commission, inv_pasiva, path)
df_pasiva = functions.f_dfpasiva(inv_pasiva)

# Activa

price_rend_c = -0.01
perc = 0.1
inv_activa_d = {'timestamp': [], 'titulos_totales': [], 'titulos_compra': [], 'precio': [], 'comision': []}
inv_activa = {'timestamp': ['30-01-2018'], 'capital': [capital]}
d_open = f_dprices(price_open, path)
d_close = f_dprices(price_close, path)

functions.f_activa(price_open, price_close, capital, commission, path, inv_activa_d, inv_activa, price_rend_c, perc)
df_activa = functions.f_dfactiva(inv_activa)

# Historico de operaciones
op_hist = functions.f_operations(inv_activa_d)

# Comparativo
PasivevsActive = pd.DataFrame()
PasivevsActive["timestamp"] = df_pasiva['timestamp']
PasivevsActive["Inversión Pasiva"] = df_pasiva['capital']
PasivevsActive["Inversión Activa"] = df_activa['capital']

# Medidas de Atribución al Desempeño
rf = 0.0770
rf_m = rf / 12

perf = functions.f_sharpe(df_pasiva, df_activa, rf_m)
