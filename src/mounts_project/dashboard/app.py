"""Streamlit entry script for the MOUNTS dashboard.

Run with::

    uv run streamlit run src/mounts_project/dashboard/app.py

or via the CLI::

    uv run mounts dashboard
"""

from mounts_project.dashboard.detail import render_detail_page
from mounts_project.dashboard.compare import render_compare_page
from mounts_project.dashboard.overview import render_overview_page
from mounts_project.dashboard.components import render_sidebar_header

import streamlit as st


def main() -> None:
    st.set_page_config(page_title="MOUNTS Dashboard", layout="wide")
    st.markdown(
        '<style>[data-testid="stSidebar"] h1 { padding: 0; }</style>',
        unsafe_allow_html=True,
    )
    render_sidebar_header()
    pages = {
        "Overview": render_overview_page,
        "Volcano detail": render_detail_page,
        "Compare": render_compare_page,
    }
    choice = st.sidebar.radio(
        "Page", list(pages.keys()), label_visibility="collapsed"
    )
    st.sidebar.divider()
    pages[choice]()


if __name__ == "__main__":
    main()
