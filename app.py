"""Tiny Streamlit browser: fetch a page, preview HTML, pick the next link."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
from requests import RequestException

from browser import Link, extract_links, fetch_html, normalize_url, partition_by_origin

st.set_page_config(page_title="Tiny Browser", page_icon="🧭", layout="wide")

DEFAULTS = {
    "url": "https://example.com",
    "loaded_url": "",
    "html": "",
    "error": "",
    "picker_nonce": 0,
    "pending_nav": "",
    "do_fetch": False,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def load_page(url: str) -> None:
    try:
        final_url, html = fetch_html(url)
        st.session_state.url = final_url
        st.session_state.loaded_url = final_url
        st.session_state.html = html
        st.session_state.error = ""
        st.session_state.picker_nonce += 1
    except (ValueError, RequestException) as exc:
        st.session_state.error = str(exc)
        st.session_state.html = ""
        st.session_state.loaded_url = ""


def queue_nav(url: str) -> None:
    cleaned = normalize_url(url)
    if cleaned:
        st.session_state.pending_nav = cleaned


def link_options(links: list[Link], *, use_text: bool) -> tuple[list[str], dict[str, str]]:
    """Build select labels → href map. Labels stay unique even when texts collide."""
    labels = ["—"]
    mapping: dict[str, str] = {"—": ""}
    seen: dict[str, int] = {}

    for link in links:
        base = link.label(use_text=use_text)
        count = seen.get(base, 0)
        seen[base] = count + 1
        label = base if count == 0 else f"{base} ({count + 1})"
        labels.append(label)
        mapping[label] = link.href

    return labels, mapping


# --- Loads must run before widgets that share session keys ---
if st.session_state.pending_nav:
    target = st.session_state.pending_nav
    st.session_state.pending_nav = ""
    load_page(target)
elif st.session_state.do_fetch:
    st.session_state.do_fetch = False
    load_page(st.session_state.url)
elif not st.session_state.loaded_url and not st.session_state.error and st.session_state.url:
    load_page(st.session_state.url)

# --- Sidebar ---
with st.sidebar:
    st.header("Preview")
    preview_height = st.slider(
        "Preview height (px)",
        min_value=200,
        max_value=1200,
        value=500,
        step=50,
    )
    use_link_text = st.checkbox("Show link text instead of URL", value=False)
    st.caption("When checked, options use each link’s anchor text (fallback: URL).")


# --- URL bar ---
st.title("Tiny Browser")

url_col, go_col = st.columns([8, 1], vertical_alignment="bottom")
with url_col:
    st.text_input(
        "URL",
        key="url",
        label_visibility="collapsed",
        placeholder="https://example.com",
    )
with go_col:
    if st.button("🔍", use_container_width=True, help="Fetch page"):
        st.session_state.do_fetch = True
        st.rerun()

if st.session_state.error:
    st.error(st.session_state.error)

# --- Preview + link pickers ---
if st.session_state.html:
    st.caption(f"Loaded: {st.session_state.loaded_url}")
    components.html(st.session_state.html, height=preview_height, scrolling=True)

    links = extract_links(st.session_state.html, st.session_state.loaded_url)
    _, cross_origin = partition_by_origin(links, st.session_state.loaded_url)

    all_labels, all_map = link_options(links, use_text=use_link_text)
    cross_labels, cross_map = link_options(cross_origin, use_text=use_link_text)
    nonce = st.session_state.picker_nonce

    st.subheader("Links")
    left, right = st.columns(2)

    with left:
        picked = st.selectbox(
            f"All links ({len(links)})",
            options=all_labels,
            key=f"link_pick_{nonce}",
        )
        if picked != "—" and all_map.get(picked):
            queue_nav(all_map[picked])
            st.rerun()

    with right:
        cross_picked = st.selectbox(
            f"Different origin ({len(cross_origin)})",
            options=cross_labels,
            key=f"cross_pick_{nonce}",
        )
        if cross_picked != "—" and cross_map.get(cross_picked):
            queue_nav(cross_map[cross_picked])
            st.rerun()
else:
    st.info("Enter a URL and press 🔍 to fetch a page.")
