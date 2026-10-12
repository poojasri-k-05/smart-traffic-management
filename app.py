import streamlit as st
import pandas as pd
import plotly.express as px
import random
import time

st.set_page_config(
    page_title="Smart Traffic Management",
    page_icon="🚦",
    layout="wide"
)

ROADS = ["North", "South", "East", "West"]

# Simulation settings
MIN_GREEN_TIME = 15
MAX_GREEN_TIME = 60
VEHICLES_PER_SECOND = 0.8

# Average arrival rates in vehicles per second
ARRIVAL_RATES = {
    "North": 0.20,
    "South": 0.15,
    "East": 0.25,
    "West": 0.18
}


# ---------------- INITIALIZE SESSION ----------------

if "traffic" not in st.session_state:
    st.session_state.traffic = {
        "North": 35,
        "South": 15,
        "East": 25,
        "West": 10
    }

if "signal_order" not in st.session_state:
    st.session_state.signal_order = sorted(
        ROADS,
        key=lambda road: st.session_state.traffic[road],
        reverse=True
    )

if "phase_index" not in st.session_state:
    st.session_state.phase_index = 0

if "phase_start" not in st.session_state:
    st.session_state.phase_start = time.time()

if "last_update" not in st.session_state:
    st.session_state.last_update = time.time()

if "phase_duration" not in st.session_state:
    road = st.session_state.signal_order[0]
    st.session_state.phase_duration = min(
        MAX_GREEN_TIME,
        max(MIN_GREEN_TIME, 15 + st.session_state.traffic[road])
    )

if "arrival_fraction" not in st.session_state:
    st.session_state.arrival_fraction = {
        road: 0.0 for road in ROADS
    }

if "departure_fraction" not in st.session_state:
    st.session_state.departure_fraction = 0.0


# ---------------- TRAFFIC GENERATION ----------------

def generate_traffic():
    st.session_state.traffic = {
        road: random.randint(5, 50)
        for road in ROADS
    }

    # Start a new cycle with the busiest road first
    st.session_state.signal_order = sorted(
        ROADS,
        key=lambda road: st.session_state.traffic[road],
        reverse=True
    )

    st.session_state.phase_index = 0
    st.session_state.phase_start = time.time()
    st.session_state.last_update = time.time()

    road = st.session_state.signal_order[0]
    st.session_state.phase_duration = min(
        MAX_GREEN_TIME,
        max(MIN_GREEN_TIME, 15 + st.session_state.traffic[road])
    )

    st.session_state.arrival_fraction = {
        road: 0.0 for road in ROADS
    }
    st.session_state.departure_fraction = 0.0


# ---------------- LIVE SIMULATION ----------------

@st.fragment(run_every=1)
def live_dashboard():

    now = time.time()
    dt = min(now - st.session_state.last_update, 3.0)
    st.session_state.last_update = now

    traffic = st.session_state.traffic

    # Current green road
    current_road = st.session_state.signal_order[
        st.session_state.phase_index
    ]

    # 1. Vehicles arrive on every road.
    # 2. Vehicles depart only from the green road.
    for road in ROADS:
        st.session_state.arrival_fraction[road] += (
            ARRIVAL_RATES[road] * dt
        )

        arrivals = int(
            st.session_state.arrival_fraction[road]
        )

        if random.random() < (
            st.session_state.arrival_fraction[road] - arrivals
        ):
            arrivals += 1

        st.session_state.arrival_fraction[road] -= arrivals
        traffic[road] += arrivals

    # Vehicles pass through the intersection on green.
    st.session_state.departure_fraction += (
        VEHICLES_PER_SECOND * dt
    )

    departures = int(st.session_state.departure_fraction)

    if departures > 0:
        actual_departures = min(
            departures, traffic[current_road]
        )
        traffic[current_road] -= actual_departures
        st.session_state.departure_fraction -= departures

        # If the queue is empty, discard unused departure capacity.
        if traffic[current_road] == 0:
            st.session_state.departure_fraction = 0.0

    # Switch signals when the green duration expires.
    if now - st.session_state.phase_start >= (
        st.session_state.phase_duration
    ):
        st.session_state.phase_index += 1
        st.session_state.phase_start = now
        st.session_state.departure_fraction = 0.0

        # After all four roads have had a turn,
        # recalculate priorities using the latest traffic.
        if st.session_state.phase_index >= len(
            st.session_state.signal_order
        ):
            st.session_state.signal_order = sorted(
                ROADS,
                key=lambda road: traffic[road],
                reverse=True
            )
            st.session_state.phase_index = 0

        next_road = st.session_state.signal_order[
            st.session_state.phase_index
        ]

        # Green duration is based on the queue at the start
        # of this road's green phase.
        st.session_state.phase_duration = min(
            MAX_GREEN_TIME,
            max(MIN_GREEN_TIME, 15 + traffic[next_road])
        )

        current_road = next_road

    # Countdown
    elapsed = now - st.session_state.phase_start
    remaining = max(
        0,
        int(st.session_state.phase_duration - elapsed + 0.999)
    )

    # ---------------- HEADER ----------------

    st.title("🚦 Smart Traffic Management Simulation")
    st.write(
        "Live traffic simulation using vehicle density "
        "and automatic signal allocation."
    )

    st.caption(
        "Simulation only — does not control real traffic lights."
    )

    # ---------------- TRAFFIC MONITORING ----------------

    st.subheader("🚗 Traffic Monitoring")

    columns = st.columns(4)

    for col, road in zip(columns, ROADS):
        vehicles = traffic[road]

        with col:
            st.metric(
                f"{road} Road",
                vehicles,
                "vehicles"
            )

            if vehicles >= 30:
                st.error("High congestion")
            elif vehicles >= 15:
                st.warning("Medium congestion")
            else:
                st.success("Low congestion")

    # ---------------- SIGNAL ALLOCATION ----------------

    st.divider()
    st.subheader("🚥 Smart Signal Allocation")

    columns = st.columns(4)

    for col, road in zip(columns, ROADS):
        with col:
            if road == current_road:
                st.success(f"🟢 {road}: GREEN")
                st.metric("Time Remaining", f"{remaining} sec")
                st.caption("Vehicles are moving")
            else:
                st.error(f"🔴 {road}: RED")
                st.caption("Vehicles are waiting")

    st.info(
        f"Current Green Road: {current_road} | "
        f"Vehicles Waiting: {traffic[current_road]}"
    )

    st.caption(
        "Next priority order: "
        + " → ".join(st.session_state.signal_order)
    )

    # ---------------- VEHICLE DENSITY CHART ----------------

    st.divider()
    st.subheader("📊 Vehicle Density Chart")

    df = pd.DataFrame({
        "Road": ROADS,
        "Vehicles": [traffic[road] for road in ROADS]
    })

    fig = px.bar(
        df,
        x="Road",
        y="Vehicles",
        color="Vehicles",
        text="Vehicles",
        title="Live Vehicle Queue by Road",
        color_continuous_scale="RdYlGn_r"
    )

    fig.update_layout(
        yaxis_title="Vehicles Waiting",
        xaxis_title="Road",
        xaxis={"categoryorder": "array", "categoryarray": ROADS}
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------- STATISTICS ----------------

    st.subheader("📈 Traffic Statistics")

    a, b, c, d = st.columns(4)

    total = sum(traffic.values())
    busiest = max(traffic, key=traffic.get)
    average = round(total / len(ROADS), 1)

    a.metric("Total Vehicles", total)
    b.metric("Busiest Road", busiest)
    c.metric("Average Vehicles", average)
    d.metric("Active Signal", current_road)

    st.caption(
        "Vehicle counts change continuously. "
        "New vehicles arrive on all roads, while vehicles "
        "leave the road that currently has a green signal."
    )


# ---------------- APP CONTROLS ----------------

st.title("🚦 Smart Traffic Management Simulation")

if st.button("🔄 Generate New Traffic"):
    generate_traffic()
    st.rerun()

live_dashboard()
