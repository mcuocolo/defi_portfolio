import streamlit as st
from datetime import datetime
import pandas as pd
import pandas_ta as ta
import numpy as np
import cufflinks as cf
import plotly.express as px
from utils.helper import token_candles_timed
cf.go_offline()

tokens = ["UNIUSDT", "LDOUSDT", "AAVEUSDT", "CRVUSDT", "MKRUSDT", 
          "SNXUSDT", "LRCUSDT", "DYDXUSDT", "1INCHUSDT", "KAVAUSDT",
          "COMPUSDT", "BALUSDT", "SUSHIUSDT", "YFIUSDT", "MDXUSDT", 
          "DEXEUSDT", "KNCUSDT", "NMRUSDT", "CAKEUSDT"]

st.sidebar.subheader("Define investment parameters")
amount = st.sidebar.slider("Investment amount", 1000, 10000, 1000, 1000)
selected_tokens = st.sidebar.multiselect("Choose component of portfolio", tokens)

# construction of portfolio dataframe

# compensate for timezone
hour = 60 * 60 * 1000
startDate = "2021-01-01"
start = datetime.strptime(startDate, "%Y-%m-%d")
end = datetime.today()

params = {
    "startTime" : int(start.timestamp() * 1000 + hour * 2),
    "endTime": int(end.timestamp() * 1000 + hour * 2)
}

interval = "1d"
# init portfolio with BTC benchmark
pf = token_candles_timed("BTCUSDT", interval, **params)
pf.rename(columns={"Close": "BTCUSDT"}, inplace=True)
pf.drop(["Open", "High", "Low", "Volume"], axis="columns", inplace=True)
BTC_units = amount / pf["BTCUSDT"].iloc[0]
pf["BTCUSDT"] = pf["BTCUSDT"] * BTC_units
pf["BTC_rtn"] = np.log(pf["BTCUSDT"]/pf["BTCUSDT"].shift(1))
pf["BTC_rtn_cum"] = (1 + pf["BTC_rtn"]).cumprod()





# compute portfolio 
def compute_portfolio(selected_tokens, weights, amount):
    # get units of each coins given weigths and initial price
    token_units = []
    for i, token in enumerate(selected_tokens):
        allocation = amount * weights[i] / 100
        data = token_candles_timed(token, interval, **params)
        token_units.append(allocation / data["Close"].iloc[0])
        # compute price * units
        pf[token] = data["Close"] * token_units[i]

    # compute PF current value and returns
    pf["PF_value"] = pf[selected_tokens].sum(axis="columns")
    pf["PF_rtn"] = np.log(pf["PF_value"]/pf["PF_value"].shift(1))
    pf["PF_rtn_cum"] = (1 + pf["PF_rtn"]).cumprod()

def calmar_ratio(return_series, max_drawdown):
    return return_series.mean()*365 / abs(max_drawdown)  


def compute_stats(returns, prices):
    """Given a returns series, function computes relevant statitics and return a dict"""
    days = len(returns)
    dict = {
        "Total return": prices.iloc[-1] / prices.iloc[0] - 1,
        "Annualized returns": (1 + returns).prod() ** (365/days) - 1,
        "Sharpe ratio": ta.sharpe_ratio(prices),
        "Sortino ratio": ta.sortino_ratio(prices),
        "Max drawdown": ta.max_drawdown(prices),
        "Calmar ratio": ta.calmar_ratio(prices)
    }
    return dict



st.title("Custom portofolio of DEFI cryptoassets")
# ask portfolio weigths
if selected_tokens != []:
    weights = []
    for token in selected_tokens:
        value = st.slider(token, 
                               min_value=0, 
                               max_value=100, 
                               value=int(np.floor(100 / len(selected_tokens))), 
                               step=1)
        weights.append(value)
    sum_weights = sum(weights)
    st.info(f"Sum of weights for this portfolio : {sum_weights}")

    if sum_weights == 100:
        go = st.button("Compute portfolio", on_click=compute_portfolio(selected_tokens, weights, amount))
        if go:

            with st.expander("Portfolio dataframe"):
                st.dataframe(pf[selected_tokens])


            fig = px.line(pf, x=pf.index, y=["PF_value", "BTCUSDT"])
            st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Portfolio statistics")
                dict = compute_stats(pf["PF_rtn"], pf["PF_value"])
                for key, value in dict.items():
                    st.write(f"{key} : {value:.2f}")

            with col2:
                st.subheader("BTC benchmark statistics")
                dict = compute_stats(pf["BTC_rtn"], pf["BTCUSDT"])
                for key, value in dict.items():
                    st.write(f"{key} : {value:.2f}")


    else:
        st.button("Compute portfolio", disabled=True)
        st.warning("Sum of weigths must = 100!")

else:
    st.write("Waiting for selection of cryptoassets ...")


