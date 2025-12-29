from shiny import App, render, ui, reactive
import pandas as pd
from pypdf import PdfReader, PdfWriter
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import re
import io
import time

# Interfaz de Usuario (UI)
app_ui = ui.page_fluid(
    ui.panel_title("🚀 Envío Masivo de Recibos - Condominio El Mirador I"),
    
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("1. Configuración de Envío"),
            ui.input_text("mes", "Mes del recibo:", placeholder="Ej: Septiembre"),
            ui.input_text("anio", "Año del recibo:", placeholder="Ej: 2025"),
            
            ui.hr(),
            ui.h4("2. Archivos"),
            ui.input_file("file_pdf", "Subir PDF Maestro", accept=[".pdf"]),
            ui.input_file("file_excel", "Subir Base de Datos (Excel)", accept=[".xlsx"]),
            
            ui.hr(),
            ui.h4("3. Credenciales SMTP"),
            ui.input_text("smtp_user", "Correo (Gmail):", placeholder="tu_correo@gmail.com"),
            ui.input_password("smtp_pass", "Contraseña de Aplicación:"),
            
            ui.hr(),
            ui.input_action_button("btn_procesar", "Iniciar Envío", class_="btn-primary w-100"),
        ),
        
        ui.column(12,
            ui.h3("Estado del Proceso"),
            ui.output_text_verbatim("log_status"),
        )
    )
)

# Lógica del Servidor
def server(input, output, session):
    status_log = reactive.Value("Esperando archivos...")

    @output
    @render.text
    def log_status():
        return status_log()

    @reactive.Effect
    @reactive.event(input.btn_procesar)
    def procesar_envio():
        # Validar entradas
        if not input.file_pdf() or not input.file_excel():
            status_log.set("❌ Error: Por favor sube ambos archivos (PDF y Excel).")
            return

        if not input.smtp_user() or not input.smtp_pass():
            status_log.set("❌ Error: Falta configurar el correo o contraseña.")
            return

        try:
            # 1. Leer Excel
            status_log.set("⏳ Leyendo base de datos...")
            file_info_excel = input.file_excel()[0]
            df = pd.read_excel(file_info_excel["datapath"])
            
            # Limpieza básica (ajustada a tus nombres de columnas)
            df = df.rename(columns={
                'DPTO': 'Departamento',
                'NOMBRES Y APELLIDOS': 'Propietario',
                'CORREO_1': 'Email'
            })

            # 2. Procesar PDF
            status_log.set("⏳ Dividiendo PDF maestro...")
            file_info_pdf = input.file_pdf()[0]
            reader = PdfReader(file_info_pdf["datapath"])
            
            pdf_divididos = {} # Guardar en memoria: { '101A': bytes_del_pdf }

            for page in reader.pages:
                text = page.extract_text()
                # Buscar el patrón de departamento al final de línea
                dpto_match = re.search(r'(\d+[AB])\s*$', text, re.MULTILINE)
                
                if dpto_match:
                    dpto = dpto_match.group(1)
                    writer = PdfWriter()
                    writer.add_page(page)
                    
                    # Guardar PDF en un objeto binario
                    pdf_buffer = io.BytesIO()
                    writer.write(pdf_buffer)
                    pdf_divididos[dpto] = pdf_buffer.getvalue()

            # 3. Iniciar Conexión SMTP
            status_log.set("⏳ Conectando con servidor de correo...")
            server_smtp = smtplib.SMTP("smtp.gmail.com", 587)
            server_smtp.starttls()
            server_smtp.login(input.smtp_user(), input.smtp_pass())

            enviados = 0
            # 4. Cruzar datos y enviar
            for _, row in df.iterrows():
                depto = str(row['Departamento']).strip()
                email = str(row['Email']).strip()

                if depto in pdf_divididos and "@" in email:
                    msg = MIMEMultipart()
                    msg['From'] = input.smtp_user()
                    msg['To'] = email
                    msg['Subject'] = f"Recibo de Mantenimiento {input.mes()} {input.anio()} - Dpto {depto}"

                    cuerpo = f"Estimado(a) {row['Propietario']},\n\nAdjuntamos el recibo de mantenimiento."
                    msg.attach(MIMEText(cuerpo, 'plain'))

                    # Adjuntar PDF desde la memoria
                    part = MIMEApplication(pdf_divididos[depto], Name=f"{depto}.pdf")
                    part['Content-Disposition'] = f'attachment; filename="{depto}.pdf"'
                    msg.attach(part)

                    server_smtp.send_message(msg)
                    enviados += 1
                    status_log.set(f"✅ Enviado: {depto} a {email} ({enviados}/{len(df)})")
                    time.sleep(1) # Pausa para evitar spam

            server_smtp.quit()
            status_log.set(f"🏁 ¡Proceso finalizado! Se enviaron {enviados} correos.")

        except Exception as e:
            status_log.set(f"❌ ERROR: {str(e)}")

app = App(app_ui, server)