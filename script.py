import imaplib
import email
from email.header import decode_header
import pymysql
import re
from datetime import datetime

def connect_to_mail(username, app_password):
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(username, app_password)

    print("Conectado al correo")

    return mail

def connect_to_sql(user_sql, password_sql):
    conn = pymysql.connect(
        host='localhost',
        user=user_sql,
        password=password_sql,
        db="yapes"
    )
    print("Conectado a la base de datos")
    return conn

def extract_information_from_body(body):

    nombre_beneficiario_pattern = re.compile(r'Nombre del Beneficiario\s+([A-Z\s.]+)(?:\n)?([A-Z\s.]+)?')
    monto_yape_pattern = re.compile(r'Monto de Yapeo\s+S/ ([\d.]+)')
    fecha_pattern = re.compile(r'Fecha y Hora de la operación\s+(\d+\s+[a-zA-Z]+\s+\d{4}\s+-\s+\d{2}:\d{2}\s+[ap]\.\sm\.)')

    nombre_beneficiario = re.search(nombre_beneficiario_pattern, body)
    monto_yape = re.search(monto_yape_pattern, body)
    fecha = re.search(fecha_pattern, body)

    return (
        nombre_beneficiario.group(1) if nombre_beneficiario else None,
        monto_yape.group(1) if monto_yape else None,
        fecha.group(1) if fecha else None
    )

def add_yape_to_table(conexion, monto_yape, nombre_beneficiario, fecha):
    cursor = conexion.cursor()
    sql = '''INSERT INTO yapes (Cantidad, Destinatario, Fecha) VALUES (%s, %s, %s)'''
    cursor.execute(sql, (monto_yape, nombre_beneficiario, fecha))
    conexion.commit()
    print("yape agregado correctamente a la tabla")
    cursor.close()

def read_mails(mail, conexion):
    mail.select("INBOX")
    status, response = mail.search(None, '(UNSEEN)')

    if (status == "OK"):
        unread_msg_nums = response[0].split()
        print(f"Tienes {len(unread_msg_nums)} correos sin leer")

        for num in  unread_msg_nums:
            _, data = mail.fetch(num, '(RFC822)')
            _, bytes_data = data[0]

            # Convertir los bytes a mensajes de mail
            email_message = email.message_from_bytes(bytes_data)

            print(email_message["Delivered-To"])

            # Datos del mensaje
            subject = decode_header(email_message["subject"])[0][0]

            if isinstance(subject, bytes):
                subject = subject.decode('utf-8')

            sender = email.utils.parseaddr(email_message['From'])[1]

            print(f"Subject: {subject}")
            print(f"Sender: {sender}")

            print("-----------------------------------------")
            if(sender == "notificaciones@yape.pe"):
                print("Realizaste un yapeo")


                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        nombre_beneficiario, monto_yape, fecha = extract_information_from_body(body)

                        add_yape_to_table(conexion, monto_yape, nombre_beneficiario, fecha)
                        print(f"Nombre del beneficiario: {nombre_beneficiario}")
                        print(f"Monto de yape: {monto_yape}")
                        print(f"Fecha: {fecha}")

if __name__ == "__main__":
    print("comenzando la aplicación")

    # Variables para mail y sql
    username = ""
    app_password = ""
    user_sql = "root"
    password_sql = "toor"

    # función para conectar con email
    mail = connect_to_mail(username, app_password)

    # función para conectar con sql
    conexion = connect_to_sql(user_sql, password_sql)

    # Lectura de mails
    read_mails(mail, conexion)

    # Cerrar conexiones
    mail.logout()
    conexion.close()

