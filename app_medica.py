import streamlit as st
import hashlib
import uuid
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA (MÓVIL) ---
st.set_page_config(
    page_title="BioSecure Mobile", 
    layout="centered", # 'Centered' se ve mejor en celulares
    page_icon="🧬",
    initial_sidebar_state="collapsed" # La barra lateral inicia cerrada en móviles
)

# --- CSS PARA QUE PAREZCA UNA APP NATIVA ---
st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
    }
    /* Botones más grandes para dedos en pantalla táctil */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        font-weight: bold;
        background-color: #0068c9;
        color: white;
        border: none;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    /* Estilo de tarjetas */
    .css-1r6slb0 {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS EN MEMORIA ---
if 'db_identidad' not in st.session_state:
    st.session_state['db_identidad'] = {}
if 'db_clinica' not in st.session_state:
    st.session_state['db_clinica'] = {}

# --- LÓGICA DE FONDO ---
def generar_hash_biometrico(datos_bytes):
    # Crea un hash único basado en los bytes de la foto o texto
    return hashlib.sha256(datos_bytes).hexdigest()

def registrar_paciente(nombre, bio_hash):
    if bio_hash in st.session_state['db_identidad']:
        return None, "Paciente ya registrado con esta biometría."
    
    anon_id = str(uuid.uuid4())
    st.session_state['db_identidad'][bio_hash] = {
        'nombre_real': nombre,
        'anon_id': anon_id
    }
    return anon_id, "Registro Exitoso"

def agregar_evento(anon_id, texto_evento):
    if anon_id not in st.session_state['db_clinica']:
        st.session_state['db_clinica'][anon_id] = []
    
    evento = {
        "Fecha": datetime.now().strftime("%d/%m %H:%M"),
        "Detalle": texto_evento
    }
    st.session_state['db_clinica'][anon_id].append(evento)

# --- INTERFAZ DE USUARIO MÓVIL ---

st.title("🧬 BioSecure Mobile")
st.caption("Sistema de Trazabilidad Biométrica")

# --- 1. SELECCIÓN DE MODO ---
modo = st.radio("Modo de Escaneo:", ["📸 Usar Cámara (Real)", "⌨️ Simulación Manual"], horizontal=True)

bio_hash_actual = None
img_file = None
texto_manual = None

# Lógica de captura según el modo
if "Cámara" in modo:
    st.info("Toma una foto de tu dedo o mano para generar tu llave única.")
    img_file = st.camera_input("Escaner Biométrico")
    if img_file is not None:
        bytes_data = img_file.getvalue()
        bio_hash_actual = generar_hash_biometrico(bytes_data)
else:
    texto_manual = st.text_input("Ingresa código simulado (PIN):", type="password")
    if texto_manual:
        bio_hash_actual = generar_hash_biometrico(texto_manual.encode())

st.markdown("---")

# --- 2. CONTENIDO PRINCIPAL ---

if bio_hash_actual:
    # Verificamos si existe en la base de datos
    record = st.session_state['db_identidad'].get(bio_hash_actual)

    if record:
        # PACIENTE ENCONTRADO
        anon_id = record['anon_id']
        nombre = record['nombre_real']
        
        st.success(f"✅ Identidad Verificada: {nombre}")
        st.caption(f"ID Anónimo (Encriptado): ...{anon_id[-8:]}")
        
        with st.expander("📂 Ver Historial Clínico", expanded=True):
            historial = st.session_state['db_clinica'].get(anon_id, [])
            if historial:
                df = pd.DataFrame(historial)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Ficha clínica nueva.")

        with st.form("nuevo_dato"):
            st.write("**Agregar registro médico:**")
            nuevo_dato = st.text_input("Diagnóstico / Procedimiento")
            if st.form_submit_button("Guardar en Ficha"):
                agregar_evento(anon_id, nuevo_dato)
                st.rerun()
                
    else:
        # PACIENTE NO ENCONTRADO -> REGISTRO
        st.warning("⚠️ Biometría no reconocida.")
        st.markdown("### 🆕 Registrar Nuevo Paciente")
        with st.form("registro_form"):
            nombre_nuevo = st.text_input("Nombre Completo")
            if st.form_submit_button("Crear Identidad Digital"):
                if nombre_nuevo:
                    aid, msg = registrar_paciente(nombre_nuevo, bio_hash_actual)
                    st.success(f"{msg}. ID: {aid}")
                    st.rerun()
                else:
                    st.error("Debes ingresar un nombre.")

else:
    st.info("👆 Esperando lectura biométrica para iniciar...")

# --- FOOTER DE AUDITORÍA ---
with st.expander("🛠️ Auditoría de Privacidad (Backend)"):
    st.write("Datos Clínicos (Sin nombres):")
    st.write(st.session_state['db_clinica'])
