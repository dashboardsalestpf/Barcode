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

generate_photos = st.Page(
    page='generate_photos.py',
    title='Generate Photos',
    icon='📸',
)

maintenance = st.Page(
    page='error.py',
    title='Maintenance',
    icon='⚙️',)


pg = st.navigation({
    'Generate Code': [maintenance]
})


pg.run()