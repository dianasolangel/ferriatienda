from ferriatienda.utils import send_conversation_email

msgs = [
    {"role": "user", "content": "¿Tienen destornilladores inalámbricos?"},
    {"role": "bot", "content": "Sí, tenemos modelos de Truper disponibles."}
]

# Change this to your real test email
recipient = "dianasolangelitofh@gmail.com"

success = send_conversation_email(recipient, "Resumen Ferritienda", msgs)

if success:
    print("Email enviado con éxito.")
else:
    print("Falló el envío del email.")