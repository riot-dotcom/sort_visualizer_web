"""Web-Version des Sorting Visualizers (Streamlit).

Nutzt unverändert algorithms.py und models.py. Die Algorithmen sind
Generatoren, die pro Schritt ein SortEvent liefern. Statt root.after() wie in
Tkinter steuert hier ein Streamlit-Fragment mit run_every den Takt.

Starten:  streamlit run streamlit_app.py
"""
import random

import streamlit as st
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from algorithms import ALGORITHMS
from models import Statistics

# Farben wie in array_canvas.py
COLORS = {"compare": "#ffff00", "swap": "#00ff00", "write": "#0000ff"}
DEFAULT_COLOR = "#808080"
FINISHED_COLOR = "#00ff00"
LEGEND = [
    ("Vergleich (compare)", COLORS["compare"]),
    ("Vertauschung (swap)", COLORS["swap"]),
    ("Schreibzugriff (write)", COLORS["write"]),
    ("Nicht beteiligt", DEFAULT_COLOR),
]


# ---------------------------------------------------------------- Zustand

def create_numbers(kind, size):
    """Erzeugt ein Array: zufällig, fast sortiert oder umgekehrt."""
    if kind == "reverse":
        return list(range(size, 0, -1))
    if kind == "almost":
        numbers = list(range(1, size + 1))
        for _ in range(5):
            first = random.randrange(size)
            second = random.randrange(size)
            numbers[first], numbers[second] = numbers[second], numbers[first]
        return numbers
    return [random.randint(1, 100) for _ in range(size)]


def reset_run(numbers):
    """Setzt den Ablauf zurück und zeigt das übergebene Array an."""
    s = st.session_state
    s.numbers = numbers
    s.generator = None
    s.stats = Statistics()
    s.status = "Bereit"
    s.running = False
    s.colors = {}
    s.algorithm_label = None


def new_array(kind="random"):
    s = st.session_state
    numbers = create_numbers(kind, s.get("size_slider", 50))
    s.start_numbers = numbers.copy()
    reset_run(numbers)


def init_state():
    if "numbers" not in st.session_state:
        new_array("random")


# ---------------------------------------------------------------- Engine

def ensure_generator():
    """Erzeugt beim ersten Start den Generator des gewählten Algorithmus."""
    s = st.session_state
    if s.generator is None:
        algorithm = ALGORITHMS[s.algorithm_key]()
        s.algorithm_label = algorithm.name
        s.generator = algorithm.sort(s.numbers)


def finish():
    s = st.session_state
    s.running = False
    s.status = "Fertig"
    s.colors = {i: FINISHED_COLOR for i in range(len(s.numbers))}


def advance(count):
    """Holt bis zu count Events aus dem Generator und färbt die Balken."""
    s = st.session_state
    for _ in range(count):
        try:
            event = next(s.generator)
        except StopIteration:
            finish()
            return
        s.stats.add_event(event)
        s.colors = {}
        if event.type == "complete":
            finish()
            return
        color = COLORS.get(event.type)
        if color:
            for index in event.indices:
                s.colors[index] = color


def start():
    s = st.session_state
    if s.status == "Fertig":
        return
    ensure_generator()
    s.running = True
    s.status = "Läuft"


def pause():
    s = st.session_state
    if s.running:
        s.running = False
        s.status = "Pausiert"


def step():
    s = st.session_state
    if s.status == "Fertig":
        return
    ensure_generator()
    s.running = False
    advance(1)
    if s.status != "Fertig":
        s.status = "Pausiert"


def reset():
    reset_run(st.session_state.start_numbers.copy())


def on_size_change():
    """Neue Arraygröße: nur wenn gerade kein Lauf aktiv ist."""
    if st.session_state.status not in ("Läuft", "Pausiert"):
        new_array("random")


# ---------------------------------------------------------------- Anzeige

def draw_chart(numbers, colors, title):
    fig = Figure(figsize=(11, 4.8))
    ax = fig.subplots()
    n = len(numbers)
    ax.bar(
        range(n),
        numbers,
        color=[colors.get(i, DEFAULT_COLOR) for i in range(n)],
        edgecolor="black",
        linewidth=0.6 if n <= 100 else 0.0,
        width=0.9,
    )
    ax.set_title(title)
    ax.set_xlabel(f"Position im Array ({n} Elemente)")
    ax.set_ylabel("Wert")
    ax.set_xlim(-0.7, n - 0.3)
    ax.set_ylim(0, max(numbers) * 1.08)
    if n > 30:
        ax.set_xticks([])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.legend(
        handles=[Patch(facecolor=c, edgecolor="black", label=l) for l, c in LEGEND],
        loc="lower center",
        ncol=4,
        frameon=False,
    )
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    st.pyplot(fig)


def show_controls():
    busy = st.session_state.status in ("Läuft", "Pausiert")

    with st.sidebar:
        st.header("Einstellungen")
        st.selectbox(
            "Algorithmus",
            options=sorted(ALGORITHMS),
            format_func=lambda key: ALGORITHMS[key].name,
            key="algorithm_key",
            disabled=busy,
        )
        st.slider(
            "Arraygröße",
            min_value=10,
            max_value=300,
            value=50,
            key="size_slider",
            on_change=on_size_change,
            disabled=busy,
        )
        st.slider("Verzögerung pro Bild (ms)", 20, 1000, 150, step=10, key="delay_ms")
        st.slider("Events pro Bild", 1, 25, 1, key="events_per_frame")
        st.divider()
        st.caption("Array erzeugen")
        st.button("Neues Array", on_click=new_array, args=("random",))
        st.button("Fast sortiert", on_click=new_array, args=("almost",))
        st.button("Umgekehrt", on_click=new_array, args=("reverse",))

    cols = st.columns(4)
    cols[0].button("Start", on_click=start, type="primary")
    cols[1].button("Pause", on_click=pause)
    cols[2].button("Schritt", on_click=step)
    cols[3].button("Reset", on_click=reset)


def make_animation():
    """Fragment, das sich im Takt der Verzögerung selbst neu ausführt."""
    s = st.session_state
    run_every = s.delay_ms / 1000 if s.running else None

    @st.fragment(run_every=run_every)
    def animation():
        if s.running:
            advance(s.events_per_frame)
            if not s.running:
                # Lauf beendet: komplette Seite neu laden, damit Status stimmt
                st.rerun()

        label = s.algorithm_label or ALGORITHMS[s.algorithm_key].name
        draw_chart(s.numbers, s.colors, f"{label}: {len(s.numbers)} Elemente")

        stats = s.stats
        metrics = st.columns(5)
        metrics[0].metric("Vergleiche", stats.comparisons)
        metrics[1].metric("Vertauschungen", stats.swaps)
        metrics[2].metric("Schreibzugriffe", stats.writes)
        metrics[3].metric("Events", stats.events)
        metrics[4].metric("Status", s.status)

    animation()


def main():
    st.set_page_config(page_title="Sorting Visualizer", page_icon="📊", layout="wide")
    st.title("Sorting Visualizer")
    init_state()
    show_controls()
    make_animation()


main()
