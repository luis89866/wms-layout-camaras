import streamlit as st
import layout

# Llama directamente a la función o ejecución del módulo layout
if hasattr(layout, "render_module"):
    layout.render_module()
