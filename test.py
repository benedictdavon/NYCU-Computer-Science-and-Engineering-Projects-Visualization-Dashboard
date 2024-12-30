import streamlit as st
import altair as alt
from vega_datasets import data

stocks = data.stocks()  # This is a DataFrame
print(stocks.head())

brush = alt.selection_interval(encodings=['x'])

base = alt.Chart(stocks).mark_line().encode(
    x='date:T',
    y='price:Q'
)

lower = base.add_params(brush)
upper = base.transform_filter(brush)

chart = upper & lower
st.altair_chart(chart)
