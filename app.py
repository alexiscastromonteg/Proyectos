from shiny import App, ui, render, reactive
import pandas as pd
from pypdf import PdfReader
import re
import io

app_ui = ui.page_fluid(
    ui.panel_title("Sistema de Recibos - El Mirador"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_file("file_pdf", "1. Sube el PDF", accept=[".pdf"]),
            ui.input_file("file_excel", "2. Sube el Excel", accept=[".xlsx"]),
            ui.input_action_button("procesar", "Procesar Archivos", class_="btn-primary"),
        ),
        ui.card(
            ui.card_header("Resultado"),
            ui.output_text_verbatim("resultado"),
        )
    )
)

def server(input, output, session):
    @render.text
    @reactive.event(input.procesar)
    def resultado():
        if not input.file_pdf() or not input.file_excel():
            return "Sube los archivos primero."
        return "Archivos listos para procesar."

app = App(app_ui, server)