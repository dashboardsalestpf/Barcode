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

generate_photos2 = st.Page(
    page='generate_photos2.py',
    title='Generate Photos2',
    icon='📸',
)

generate_photos_ws = st.Page(
    page='generate_photos_ws.py',
    title='Generate Photos WS',
    icon='📸',
)

maintenance = st.Page(
    page='error.py',
    title='Maintenance',
    icon='⚙️',)


pg = st.navigation({
    'Generate Code': [dashboard,generate_code,generate_photos,generate_photos2,generate_photos_ws]
})


pg.run()
