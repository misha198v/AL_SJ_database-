import streamlit as st
from utils.db import db_message


class FormError(Exception):
    """A problem with what the user typed. Shown in red, nothing is saved."""


def need(**fields):
    """need(destination=destination) raises FormError if the value is empty."""
    for label, value in fields.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            raise FormError(f"Please fill in: {label.replace('_', ' ')}.")


def gkey(name):
    """Grid key that changes after every write, so a stale selection can't hit the wrong row."""
    return f"{name}_{st.session_state.get('grid_ver', 0)}"


def attempt(fn, success="Done."):
    """Run a write. Success: flash + rerun. Failure: show the DATABASE's own message."""
    try:
        fn()
    except FormError as e:
        st.error(str(e))
        return
    except Exception as e:
        st.error(f"The database refused this: {db_message(e)}")
        return
    st.session_state["grid_ver"] = st.session_state.get("grid_ver", 0) + 1
    st.session_state["flash"] = f"✅ {success}"
    st.rerun()


def show_flash():
    if msg := st.session_state.pop("flash", None):
        st.success(msg)


def stepper(stages, current_order):
    """Visual pipeline tracker: done = teal tick, current = amber, upcoming = grey."""
    cells = []
    for s in stages:
        o = s["stage_order"]
        state = "done" if o < current_order else "now" if o == current_order else "todo"
        mark = "✓" if state == "done" else o
        cells.append(f"<div class='st {state}'><div class='dot'>{mark}</div>"
                     f"<div class='lbl'>{s['stage_name']}</div></div>")
    css = """<style>
    .track{display:flex;gap:6px;margin:10px 0 18px}.st{flex:1;text-align:center}
    .dot{margin:0 auto 6px;width:36px;height:36px;border-radius:50%;line-height:36px;
         font-weight:700;color:#fff;background:#B8C4CC}
    .st.done .dot{background:#0E7C86}
    .st.now .dot{background:#F2A541;box-shadow:0 0 0 6px rgba(242,165,65,.30)}
    .lbl{font-size:12px}.st.todo .lbl{opacity:.55}.st.now .lbl{font-weight:700}</style>"""
    st.markdown(css + f"<div class='track'>{''.join(cells)}</div>", unsafe_allow_html=True)