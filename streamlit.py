import streamlit as st

generate_code = st.Page(
    page='generate_code.py',
    title='Generate Code',
    icon='📦',
)

dashboard = st.Page(
    page='dashboard.py',
    title='Dashboard',
    icon='📊',
)

pg = st.navigation({
    'Generate Code': [generate_code, dashboard]
})


pg.run()