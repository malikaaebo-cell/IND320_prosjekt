import streamlit as st
import matplotlib.pyplot as plt
from modules.data_loader import load_data

st.title("Plot")
st.write("Her er et plot med selectbox for kolonnevalg og select_slider for månedsutvalg.")

df = load_data()
numeric_cols = df.select_dtypes(include='number').columns.tolist()

# Dropdown: én kolonne eller alle sammen
valgt_kolonne = st.selectbox("Velg kolonne", ["Alle kolonner"] + numeric_cols)

# Bygg liste over tilgjengelige måneder for slideren
df['year_month'] = df['date'].dt.to_period('M').astype(str)
maaneder = sorted(df['year_month'].unique())

valgt_periode = st.select_slider(
    "Velg måneder",
    options=maaneder,
    value=(maaneder[0], maaneder[0])  # Standard: bare første måned
)

start, slutt = valgt_periode
filtered = df[(df['year_month'] >= start) & (df['year_month'] <= slutt)]

fig, ax = plt.subplots(figsize=(10, 5))

if valgt_kolonne == "Alle kolonner":
    normalized = (filtered[numeric_cols] - df[numeric_cols].min()) / (df[numeric_cols].max() - df[numeric_cols].min())
    for col in numeric_cols:
        ax.plot(filtered['date'], normalized[col], label=col, alpha=0.7)
    ax.legend(fontsize='small', loc='upper right')
    ax.set_ylabel("Normalisert verdi")
    ax.set_title("Alle kolonner (normalisert)")
else:
    ax.plot(filtered['date'], filtered[valgt_kolonne])
    ax.set_ylabel(valgt_kolonne)
    ax.set_title(valgt_kolonne)

ax.set_xlabel("Dato")
st.pyplot(fig)