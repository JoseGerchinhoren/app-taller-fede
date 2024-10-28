import streamlit as st
import boto3
import pandas as pd
from io import StringIO
from datetime import datetime
import pytz  # Asegúrate de tener pytz instalado
from config import cargar_configuracion

# Cargar configuración
aws_access_key, aws_secret_key, region_name, bucket_name, valid_user, valid_password = cargar_configuracion()

# Configuración de AWS S3
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region_name
)

# Funciones para cargar y actualizar datos desde y en S3
def load_csv_from_s3(filename):
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=filename)
        data = pd.read_csv(obj['Body'])
        return data
    except Exception as e:
        st.error(f"Error al cargar {filename}: {e}")
        return pd.DataFrame(columns=['id', 'fecha', 'hora', 'patente', 'modelo', 'km', 'trabajo_realizado', 'tipo_aceite', 'observaciones'])

def update_csv_in_s3(data, filename):
    csv_buffer = StringIO()
    data.to_csv(csv_buffer, index=False)
    s3.put_object(Bucket=bucket_name, Key=filename, Body=csv_buffer.getvalue())

# Formulario de Registro de Servicio
def service_form(service_data):
    st.header("Registrar Servicio")

    fecha = st.date_input("Fecha", value=datetime.now().date())
    fecha_formateada = fecha.strftime('%d-%m-%Y')  # Formato dd-mm-aaaa
    
    # Obtener la hora actual en la zona horaria de Argentina
    tz = pytz.timezone('America/Argentina/Buenos_Aires')
    hora_actual = datetime.now(tz).time()
    hora = st.time_input("Hora", value=hora_actual)  # Usa la hora actual de Argentina
    
    patente = st.text_input("Número de Patente")
    modelo = st.text_input("Modelo")
    km = st.number_input("Kilometraje", min_value=0)
    trabajo_realizado = st.text_input("Trabajo Realizado")
    tipo_aceite = st.text_input("Tipo de Aceite")
    observaciones = st.text_area("Observaciones")
    
    if st.button("Registrar Servicio"):
        # Obtener el nuevo id como el máximo id existente + 1
        if service_data.empty:
            new_id = 1
        else:
            new_id = service_data['id'].max() + 1
        
        new_entry = pd.DataFrame([{
            'id': new_id,
            'fecha': fecha_formateada,
            'hora': hora.strftime('%H:%M'),  # Formato de hora en HH:MM
            'patente': patente,
            'modelo': modelo,
            'km': km,
            'trabajo_realizado': trabajo_realizado,
            'tipo_aceite': tipo_aceite,
            'observaciones': observaciones
        }])
        
        # Agregar la nueva entrada al DataFrame
        service_data = pd.concat([service_data, new_entry], ignore_index=True)

        # Actualizar el archivo CSV en S3
        update_csv_in_s3(service_data, 'arreglos.csv')

        st.success("Servicio registrado correctamente.")

# Mostrar tabla de Servicios
def show_service_history(service_data):
    st.header("Historial de Servicios")
    service_data = load_csv_from_s3('arreglos.csv')
    # Ordenar los registros por 'id' en orden descendente
    service_data = service_data.sort_values(by='id', ascending=False)
    
    st.dataframe(service_data, hide_index=True)

# Función Principal
def main():
    # Cargar los datos
    service_data = load_csv_from_s3('arreglos.csv')

    # Llamar a las funciones que gestionan el formulario y la visualización
    service_form(service_data)
    show_service_history(service_data)

if __name__ == "__main__":
    main()
