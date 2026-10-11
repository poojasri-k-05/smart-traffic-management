
import streamlit as st
import pandas as pd
import plotly.express as px
import random

st.set_page_config(
    page_title="Smart Traffic Management",
    page_icon="🚦",
    layout="wide"
)

st.title("🚦 Smart Traffic Management Simulation")
st.write("A cloud-based traffic simulation using vehicle density.")

if "traffic" not in st.session_state:
    st.session_state.traffic = {
        "North": 35,
        "South": 15,
        "East": 25,
        "West": 10
    }

if st.button("Generate New Traffic"):
    st.session_state.traffic = {
        road: random.randint(5, 50)
        for road in ["North", "South", "East", "West"]
    }

traffic = st.session_state.traffic
priority = max(traffic, key=traffic.get)

st.subheader("Traffic Monitoring")

columns = st.columns(4)

for col, (road, vehicles) in zip(columns, traffic.items()):
    with col:
        st.metric(f"{road} Road", vehicles, "vehicles")
        if vehicles >= 30:
            st.error("High congestion")
        elif vehicles >= 15:
            st.warning("Medium congestion")
        else:
            st.success("Low congestion")

st.divider()
st.subheader("🚥 Smart Signal Allocation")

for road, vehicles in traffic.items():
    green_time = min(60, max(15, 15 + vehicles))

    if road == priority:
        st.success(
            f"🟢 {road}: GREEN — {green_time} seconds"
        )
    else:
        st.error(f"🔴 {road}: RED")

st.info(f"Priority road: {priority}")

df = pd.DataFrame({
    "Road": list(traffic.keys()),
    "Vehicles": list(traffic.values())
})

st.subheader("Vehicle Density Chart")

fig = px.bar(
    df,
    x="Road",
    y="Vehicles",
    color="Vehicles",
    text="Vehicles",
    title="Traffic by Road"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Traffic Statistics")

a, b, c = st.columns(3)
a.metric("Total Vehicles", sum(traffic.values()))
b.metric("Busiest Road", priority)
c.metric("Average Vehicles", round(sum(traffic.values()) / 4, 1))

st.caption(
    "Educational simulation using generated vehicle data. "
    "It does not control real traffic signals."
)
