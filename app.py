from shiny import App, ui, render, reactive
import pandas as pd
from pypdf import PdfReader, PdfWriter
import re
import io

# INTERFAZ
app_ui = ui.page_fluid(
    ui.panel_title("Sistema de Recibos - El Mirador"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_file("file_pdf", "1. Sube el PDF con todos los recibos", accept=[".pdf"]),
            ui.input_file("file_excel", "2. Sube el Excel de propietarios", accept=[".xlsx"]),
            ui.input_action_button("procesar", "Procesar Archivos", class_="btn-primary"),
        ),
        ui.card(
            ui.card_header("Resultado del proceso"),
            ui.output_text_verbatim("resultado"),
        )
    )
)

# LÓGICA
def server(input, output, session):
    @render.text
    @reactive.event(input.procesar)
    def resultado():
        if not input.file_pdf() or not input.file_excel():
            return "Esperando archivos... Por favor sube el PDF y el Excel."
        
        try:
            # Leer el PDF desde la memoria (ya no usamos Drive)
            reader = PdfReader(input.file_pdf()[0]["datapath"])
            df = pd.read_excel(input.file_excel()[0]["datapath"])
            
            num_paginas = len(reader.pages)
            return f"✅ ¡Éxito! Se detectaron {num_paginas} recibos en el PDF y {len(df)} filas en el Excel."
        except Exception as e:
            return f"❌ Error: {str(e)}"

app = App(app_ui, server)