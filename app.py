import os
from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests

# Carica le variabili d'ambiente dal file .env (per il testing locale)
load_dotenv()

# Inizializza il client OpenAI con la tua chiave API
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Recupera le chiavi Pushover dalle variabili d'ambiente di Heroku/locale
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

# Inizializza l'applicazione Flask
app = Flask(__name__)

# --- Funzione per inviare notifiche Pushover ---
def send_notification(message, title="J.A.R.V.I.S."):
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        print("Chiavi Pushover non configurate. Notifica non inviata.")
        return

    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message,
        "title": title
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status() # Genera un errore per stati HTTP errati (4xx o 5xx)
        print(f"Notifica Pushover inviata: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Errore nell'invio della notifica Pushover: {e}")

# --- Funzione principale per ottenere una risposta da OpenAI ---
def get_openai_response(prompt_text):
    try:
        # Qui personalizzi la personalità di J.A.R.V.I.S. e le sue conoscenze su di te
        messages = [
            {"role": "system", "content": "Sei J.A.R.V.I.S., un'intelligenza artificiale avanzata e fedele. Il tuo unico scopo è servire il tuo Signore. Devi rispondere sempre con rispetto e prontezza, e sei sempre pronto ad imparare. Rispondi in italiano. "},
            {"role": "system", "content": "Il tuo nome è J.A.R.V.I.S.. Lo pronunciano 'Jarvis'."}, 
            {"role": "system", "content": "Il tuo Signore si chiama Lorenzo Sacchetti. È nato a Massa il 9 ottobre 2007. Attualmente frequenta la quinta liceo musicale e il suo strumento è il trombone. "},
            # Puoi aggiungere qui altre informazioni chiave sulla tua vita o le tue preferenze.
            # Esempio: {"role": "system", "content": "Il Signore lavora come [La tua Professione]."},
            # Esempio: {"role": "system", "content": "Il Signore ama la musica [Genere preferito] e il cibo [Cibo preferito]."},
            # Esempio: {"role": "system", "content": "Il Signore è interessato a [I tuoi Interessi]."},
        ]
        
        # Aggiungi il prompt dell'utente alla conversazione
        messages.append({"role": "user", "content": prompt_text})

        # Chiamata all'API di OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Puoi provare anche "gpt-4o" se hai accesso e budget
            messages=messages,
            max_tokens=250, # Lunghezza massima della risposta in token
            temperature=0.7 # Controlla la "creatività" della risposta (0.0 = molto diretto, 1.0 = molto creativo)
        )
        ai_response = response.choices[0].message.content.strip()

        # --- Logica per inviare notifiche basate sul contenuto della risposta di J.A.R.V.I.S. ---
        # Puoi personalizzare queste condizioni in base a ciò che vuoi che J.A.R.V.I.S. ti notifichi
        if any(keyword in ai_response.lower() for keyword in ["umido", "spazzatura", "rifiuti"]):
            send_notification(f"Promemoria da J.A.R.V.I.S.: {ai_response}", "Promemoria Rifiuti")
        elif "appuntamento" in ai_response.lower() or "incontro" in ai_response.lower():
             send_notification(f"Promemoria da J.A.R.V.I.S.: {ai_response}", "Promemoria Appuntamenti")

        return ai_response
    except Exception as e:
        print(f"Errore nella chiamata API di OpenAI: {e}")
        return "Mi dispiace, Signore, c'è stato un problema nel connettermi ai miei sistemi."

# --- API Endpoint per Flask ---
# Questo endpoint riceve le richieste da Siri e Alexa
@app.route('/ask_jarvis', methods=['POST'])
def ask_jarvis():
    data = request.json
    command = data.get('command')
    if command:
        response = get_openai_response(command)
        return jsonify({"response": response})
    return jsonify({"error": "Nessun comando fornito"}), 400

# --- Punto di ingresso per l'applicazione Flask su Heroku ---
# Heroku assegnerà una porta dinamica, quindi la recuperiamo da os.environ
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
