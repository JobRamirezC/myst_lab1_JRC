"""
# -- --------------------------------------------------------------------------------------------------- -- #
# -- project: A SHORT DESCRIPTION OF THE PROJECT                                                         -- #
# -- script: functions.py : python script with general functions                                         -- #
# -- author: YOUR GITHUB USER NAME                                                                       -- #
# -- license: GPL-3.0 License                                                                            -- #
# -- repository: YOUR REPOSITORY URL                                                                     -- #
# -- --------------------------------------------------------------------------------------------------- -- #
"""

import numpy as np
import yfinance as yf
from data import *


def f_fechas(archivos):
    """


    """
    t_fechas = [i.strftime('%Y-%m-%d') for i in sorted([pd.to_datetime(i[8:]).date() for i in archivos])]
    return t_fechas


def f_yftickers(archivos):
    """

    """
    tickers = []
    for i in archivos:
        pathfiles = f_dictionary(archivos)
        l_tickers = list(pathfiles[i]['Ticker'])
        [tickers.append(i + '.MX') for i in l_tickers]
    global_tickers = np.unique(tickers).tolist()
    global_tickers = [i.replace('GFREGIOO.MX', 'RA.MX') for i in global_tickers]
    global_tickers = [i.replace('LIVEPOLC.1.MX', 'LIVEPOLC-1.MX') for i in global_tickers]
    global_tickers = [i.replace('MEXCHEM.MX', 'ORBIA.MX') for i in global_tickers]
    [global_tickers.remove(i) for i in ['MXN.MX', 'USD.MX', 'KOFL.MX', 'KOFUBL.MX', 'BSMXB.MX']]
    return global_tickers


def f_yfprices(archivos):
    """

    """
    data = yf.download(f_yftickers(archivos), start="2018-01-30", end="2020-08-22", actions=False, group_by="close",
                       interval='1d', auto_adjust=False, prepost=False, threads=True)
    data_close = pd.DataFrame({i: data[i]['Close'] for i in f_yftickers(archivos)})
    data_open = pd.DataFrame({i: data[i]['Open'] for i in f_yftickers(archivos)})
    return data_close, data_open


def f_mprices(data_close, archivos):
    """


    """
    ic_fechas = sorted(list(set(data_close.index.astype(str).tolist()) & set(f_fechas(archivos))))
    precios = data_close.iloc[[int(np.where(data_close.index.astype(str) == i)[0]) for i in ic_fechas]]
    precios = precios.reindex(sorted(precios.columns), axis=1)
    return precios


def f_dprices(data_close, archivos):
    """

    """
    intdates = pd.date_range(start=f_fechas(archivos)[0], end=f_fechas(archivos)[-1])
    intdates = intdates.strftime('%Y-%m-%d')
    ic_fechas = sorted(list(set(data_close.index.astype(str).tolist()) & set(intdates)))
    precios = data_close.iloc[[int(np.where(data_close.index.astype(str) == i)[0]) for i in ic_fechas]]
    precios = precios.reindex(sorted(precios.columns), axis=1)
    return precios


def f_pasiva(capital, monthlyprices, commission, dictionary, data):
    cash_activos = ['KOFL', 'KOFUBL', 'BSMXB', 'MXN', 'USD']
    vcommision = [0]
    pos_datos = f_dictionary(data)[data[0]].copy().sort_values('Ticker')[['Ticker', 'Peso (%)']]
    i_activos = list(pos_datos[pos_datos['Ticker'].isin(cash_activos)].index)
    pos_datos.drop(i_activos, inplace=True)
    pos_datos.reset_index(inplace=True, drop=True)
    pos_datos.reset_index(inplace=True, drop=True)

    pos_datos['Ticker'] = pos_datos['Ticker'] + '.MX'
    pos_datos['Ticker'] = pos_datos['Ticker'].replace('GFREGIOO.MX', 'RA.MX')
    pos_datos['Ticker'] = pos_datos['Ticker'].replace('LIVEPOLC.1.MX', 'LIVEPOLC-1.MX')
    pos_datos['Ticker'] = pos_datos['Ticker'].replace('MEXCHEM.MX', 'ORBIA.MX')

    pos_datos['Precio'] = (
        np.array([monthlyprices.iloc[0, monthlyprices.columns.to_list().index(i)] for i in pos_datos['Ticker']]))

    pos_datos['Capital'] = pos_datos['Peso (%)'] * capital - (pos_datos['Peso (%)'] * capital * commission)
    pos_datos['Titulos'] = pos_datos['Capital'] // pos_datos['Precio']  # floor division
    pos_datos['Postura'] = pos_datos['Titulos'] * pos_datos['Precio']
    pos_datos['Comision'] = pos_datos['Titulos'] * pos_datos['Precio'] * commission

    cash = capital - pos_datos['Postura'].sum() - pos_datos['Comision'].sum()
    dictionary['timestamp'].append(f_fechas(data)[0])
    dictionary['capital'].append(capital - pos_datos['Comision'].sum())
    vcommision.append(pos_datos['Comision'].sum())

    for n in range(1, len(monthlyprices)):
        pos_datos['Precio'] = np.array(
            [monthlyprices.iloc[n, monthlyprices.columns.to_list().index(i)] for i in pos_datos['Ticker']])
        pos_datos['Postura'] = pos_datos['Titulos'] * pos_datos['Precio']
        pos_datos['Comision'] = 0
        postura = sum(pos_datos['Postura'])
        dictionary['capital'].append(postura + cash)
        fechas = f_fechas(data)
        dictionary['timestamp'].append(fechas[n])


def f_dfpasiva(pasive_data):
    df_pasiva = pd.DataFrame()
    df_pasiva['timestamp'] = pasive_data['timestamp']
    df_pasiva['capital'] = pasive_data['capital']
    df_pasiva['rend'] = 0
    df_pasiva['rend_acum'] = 0

    for i in range(1, len(df_pasiva)):
        df_pasiva.loc[i, 'rend'] = np.log(df_pasiva.loc[i, 'capital'] / (df_pasiva.loc[i - 1, 'capital']))
        df_pasiva.loc[i, 'rend_acum'] = (df_pasiva.loc[i - 1, 'rend_acum']) + df_pasiva.loc[i, 'rend']

    return df_pasiva


def f_activa(openprice, closeprice, capital, commission, data, dictionary, invact, pricerend, percentage):
    pos_datos_act = f_dictionary(data)[data[0]].copy().sort_values('Ticker')[['Ticker', 'Peso (%)']]
    #l = len(pos_datos_act['Ticker'])

    cash_activos = ['KOFL', 'KOFUBL', 'BSMXB', 'MXN', 'USD']
    vcommision = [0]
    i_activos = list(pos_datos_act[pos_datos_act['Ticker'].isin(cash_activos)].index)
    pos_datos_act.drop(i_activos, inplace=True)
    pos_datos_act.reset_index(inplace=True, drop=True)

    pos_datos_act['Ticker'] = pos_datos_act['Ticker'] + '.MX'
    pos_datos_act['Ticker'] = pos_datos_act['Ticker'].replace('GFREGIOO.MX', 'RA.MX')
    pos_datos_act['Ticker'] = pos_datos_act['Ticker'].replace('LIVEPOLC.1.MX', 'LIVEPOLC-1.MX')
    pos_datos_act['Ticker'] = pos_datos_act['Ticker'].replace('MEXCHEM.MX', 'ORBIA.MX')
    max_pond = pos_datos_act['Peso (%)'].idxmax()

    pos_datos_act['Precio'] = np.array([closeprice.iloc[0, closeprice.columns.to_list().index(i)] for i in pos_datos_act['Ticker']])
    pos_datos_act['Open'] = np.array([openprice.iloc[0, openprice.columns.to_list().index(i)] for i in pos_datos_act['Ticker']])

    pos_datos_act['Capital'] = pos_datos_act['Peso (%)'] * capital - pos_datos_act['Peso (%)'] * capital * commission
    pos_datos_act.loc[max_pond, 'Capital'] = (pos_datos_act.loc[max_pond, 'Capital']) * 0.5

    pos_datos_act['Titulos'] = pos_datos_act['Capital'] // pos_datos_act['Precio']
    pos_datos_act['Comision'] = pos_datos_act['Precio'] * pos_datos_act['Titulos'] * commission
    pos_datos_act['Postura'] = pos_datos_act['Titulos'] * pos_datos_act['Precio']
    pos_datos_act['Yesterday'] = pos_datos_act['Precio']

    cash_act = capital - pos_datos_act['Postura'].sum() - pos_datos_act['Comision'].sum()
    #print(cash_act)

    invact['capital'].append(capital - pos_datos_act['Comision'].sum())
    invact['timestamp'].append(str(closeprice.index[0].strftime('%Y-%m-%d')))
    vcommision.append(sum(pos_datos_act['Comision']))

    dictionary['comision'].append(pos_datos_act.loc[max_pond, 'Comision'])
    dictionary['precio'].append(pos_datos_act.loc[max_pond, 'Precio'])
    dictionary['timestamp'].append(str(closeprice.index[0].strftime('%Y-%m-%d')))

    dictionary['titulos_totales'].append(pos_datos_act.loc[max_pond, 'Titulos'])
    dictionary['titulos_compra'].append(pos_datos_act.loc[max_pond, 'Titulos'])
    # print(pos_datos_act)

    for n in range(1, len(openprice)):
        pos_datos_act['Precio'] = np.array(
            [closeprice.iloc[n, closeprice.columns.to_list().index(i)] for i in pos_datos_act['Ticker']])
        pos_datos_act['Comision'] = 0
        titulos_compra = pos_datos_act.loc[max_pond, 'Titulos']
        pos_datos_act.loc[max_pond, 'Open'] = np.array(
            openprice.iloc[n, openprice.columns.to_list().index(pos_datos_act.loc[max_pond, 'Ticker'])])

        price_rend = (pos_datos_act.loc[max_pond, 'Precio'] / pos_datos_act.loc[max_pond, 'Open']) - 1

        if price_rend < pricerend:
            xcashperc = cash_act * percentage
            xcommperc = commission * percentage
            cond = (xcashperc - cash_act * xcommperc) // pos_datos_act.loc[max_pond, 'Precio']
            pos_datos_act.loc[max_pond, 'Precio_c'] = np.array(
                openprice.iloc[n + 1, openprice.columns.to_list().index(pos_datos_act.loc[max_pond, 'Ticker'])])

            if cond > 0:
                pos_datos_act.loc[max_pond, 'Capital'] = pos_datos_act.loc[max_pond, 'Capital'] + (xcashperc - cash_act * xcommperc)

                titulos_pos = pos_datos_act.loc[max_pond, 'Titulos']
                titulos_compra = (xcashperc - cash_act * xcommperc) // pos_datos_act.loc[max_pond, 'Precio_c']
                cash_act = cash_act - (xcashperc - cash_act * xcommperc)
                # cash_act = cash_act - xcashperc - xcommperc
                titulos_totales = titulos_compra + titulos_pos

                pos_datos_act.loc[max_pond, 'Titulos'] = titulos_totales
                pos_datos_act.loc[max_pond, 'Comision'] = pos_datos_act.loc[max_pond, 'Precio_c'] * (commission) * (titulos_compra)

                dictionary['timestamp'].append(str(closeprice.index[n + 1].strftime('%Y-%m-%d')))
                dictionary['titulos_totales'].append(titulos_totales)
                dictionary['titulos_compra'].append(titulos_compra)
                dictionary['precio'].append(pos_datos_act.loc[max_pond, 'Precio_c'])
                dictionary['comision'].append(pos_datos_act.loc[max_pond, 'Comision'])

        pos_datos_act['Yesterday'] = pos_datos_act['Precio']
        pos_datos_act['Postura'] = pos_datos_act['Titulos'] * pos_datos_act['Precio']

        #invact['capital'].append(sum(pos_datos_act['Postura']) + cash_act)
        pos_datos_act['Yesterday'] = pos_datos_act['Precio']
        pos_datos_act['Postura'] = pos_datos_act['Titulos'] * pos_datos_act['Precio']
        invact['capital'].append(sum(pos_datos_act['Postura'])+ cash_act)
        vcommision.append(sum(pos_datos_act['Comision']))
        invact['timestamp'].append(str(closeprice.index[n].strftime('%Y-%m-%d')))


def f_dfactiva(active_data):
    df_activa = pd.DataFrame()
    df_activa['timestamp'] = active_data['timestamp']
    df_activa['capital'] = active_data['capital']
    df_activa['rend'] = 0
    df_activa['rend_acum'] = 0

    df_activa = df_activa[df_activa['timestamp'].isin(active_data['timestamp'])]
    df_activa = df_activa.reset_index(drop=True)

    for i in range(1, len(df_activa)):
        df_activa.loc[i, 'rend'] = np.log(df_activa.loc[i, 'capital'] / df_activa.loc[i - 1, 'capital'])
        df_activa.loc[i, 'rend_acum'] = df_activa.loc[i - 1, 'rend_acum'] + df_activa.loc[i, 'rend']

    return df_activa

def f_operations(data):
    op_history = pd.DataFrame()
    op_history['timestamp'] = data['timestamp']
    op_history['titulos_totales'] = data['titulos_totales']
    op_history['titulos_compra'] = data['titulos_compra']
    op_history['precio'] = data['precio']
    op_history['comision'] = data['comision']
    return op_history

def f_sharpe(df_pasiva,df_activa,rf):

    performance = pd.DataFrame()
    performance['medida'] = ['rend_m', 'rend_c', 'sharpe']
    performance['descripcion'] = ['Rendimiento Promedio Mensual', 'Rendimiento Mensual Acumulado', 'Ratio de Sharpe']

    performance.loc[0, 'inv_pasiva'] = np.average(df_pasiva['rend'])
    performance.loc[1, 'inv_pasiva'] = df_pasiva.loc[len(df_pasiva) - 1, 'rend_acum']
    performance.loc[2, 'inv_pasiva'] = (np.average(df_pasiva['rend']) - rf) / np.std(df_pasiva['rend'])

    performance.loc[0, 'inv_activa'] = np.average(df_activa['rend'])
    performance.loc[1, 'inv_activa'] = df_activa.loc[len(df_activa) - 1, 'rend_acum']
    performance.loc[2, 'inv_activa'] = (np.average(df_activa['rend']) - rf / 12) / np.std(df_activa['rend'])
    return performance

