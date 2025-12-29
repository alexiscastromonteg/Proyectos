from shiny import App, ui, render, reactive
import pandas as pd
from pypdf import PdfReader, PdfWriter
import re
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# 1. INTERFAZ DE USUARIO (UI)
app_ui = ui.page_fluid(
    ui.panel_title("Sistema de Envío Masivo de Recibos"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Configuración"),
            ui.input_text("mes", "Mes (ej: Septiembre)", value="Septiembre"),
            ui.input_text("anio", "Año (ej: 2025)", value="2025"),
            ui.hr(),
            ui.input_file("file_pdf", "1. Sube el PDF Maestro", accept=[".pdf"]),
            ui.input_file("file_excel", "2. Sube la Base de Datos (Excel)", accept=[".xlsx"]),
            ui.hr(),
            ui.input_action_button("procesar", "Procesar y Enviar", class_="btn-primary w-100"),
        ),
        ui.card(
            ui.card_header("Estado del Proceso"),
            ui.output_text_verbatim("log_estatus"),
        )
    )
)

# 2. LÓGICA DEL SERVIDOR
def server(input, output, session):
    
    @render.text
    @reactive.event(input.procesar)
    async def log_estatus():
        if not input.file_pdf() or not input.file_excel():
            return "⚠️ Por favor, sube ambos archivos (PDF y Excel) antes de comenzar."

        try:
            # Leer el Excel subido
            df = pd.read_excel(input.file_excel()[0]["datapath"])
            
            # Leer el PDF subido
            reader = PdfReader(input.file_pdf()[0]["datapath"])
            
            resultados = []
            resultados.append(f"✅ Archivos cargados. Procesando {len(reader.pages)} páginas...")

            # Aquí iría tu lógica de envío de correos (smtplib)
            # NOTA: En la web, esta sección dará error de conexión por seguridad del navegador.
            
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                # Tu lógica de búsqueda de departamento
                dpto_match = re.search(r'(\d+[AB])\s*$', text, re.MULTILINE)
                
                if dpto_match:
                    dpto = dpto_match.group(1)
                    resultados.append(f"📄 Recibo detectado: Depto {dpto}")
            
            return "\n".join(resultados) + "\n\n⚠️ Nota: El envío de correos vía SMTP está restringido en versiones web estáticas."

        except Exception as e:
            return f"❌ Error durante el proceso: {str(e)}"

app = App(app_ui, server)
