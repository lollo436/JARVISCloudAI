import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai # Sì, usiamo ancora la libreria 'openai' ma la configureremo per DeepSeek
import requests # Necessario per Pushover

load_dotenv() # Per caricare le variabili d'ambiente in locale se le usi

app = Flask(__name__)

# --- CONFIGURAZIONE API DEEPSEEK ---
# Recupera la chiave API dalla variabile d'ambiente.
# Assicurati che su Render la tua variabile si chiami DEEPSEEK_API_KEY
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    # Se questa riga viene stampata nei log di Render, significa che la variabile non è stata trovata.
    print("ERRORE: La variabile DEEPSEEK_API_KEY non è impostata nelle variabili d'ambiente di Render.")
    # Puoi decidere come gestire questo errore se l'applicazione è in esecuzione senza la chiave.

# Imposta l'endpoint base dell'API per DeepSeek. Questo è FONDAMENTALE!
openai.api_base = "https://api.deepseek.com/v1"
openai.api_key = DEEPSEEK_API_KEY # Assegna la tua chiave DeepSeek alla variabile API key della libreria openai

# --- CONFIGURAZIONE PUSHOVER ---
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

def send_pushover_notification(title, message):
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        print("Le chiavi Pushover non sono configurate. Notifica non inviata.")
        return

    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "title": title,
        "message": message,
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status() # Solleva un'eccezione per errori HTTP (4xx o 5xx)
        print("Notifica Pushover inviata con successo.")
    except requests.exceptions.RequestException as e:
        print(f"Errore nell'invio della notifica Pushover: {e}")

@app.route('/ask_jarvis', methods=['POST'])
def ask_jarvis():
    try:
        data = request.json
        command = data.get('command') # Ottieni il comando dal JSON
        if not command:
            return jsonify({"response": "Comando mancante nel JSON."}), 400

        print(f"Comando ricevuto: {command}") # Per debugging nei log di Render

        # Qui stiamo riprendendo il tuo prompt di sistema
        messages = [
            {"role": "system", "content": "Sei un assistente AI chiamato J.A.R.V.I.S. Rispondi in italiano. Sii conciso e diretto, ma sempre educato e disponibile. Se non hai informazioni, chiedi maggiori dettagli o ammetti di non sapere. Parli in modo leggermente formale ma amichevole."},
            {"role": "user", "content": command}
        ]

        # Fai la chiamata all'API di DeepSeek
        # Il modello da usare per DeepSeek dovrebbe essere "deepseek-chat" o un altro nome specificato nella loro documentazione
        chat_completion = openai.ChatCompletion.create(
            model="deepseek-chat", # NOME DEL MODELLO DEEPSEEK (verifica nella doc di DeepSeek!)
            messages=messages,
            stream=False # Lascia stream=False per non fare lo streaming della risposta
        )

        jarvis_response = chat_completion.choices[0].message.content

        # Invia notifica Pushover con la risposta di J.A.R.V.I.S.
        send_pushover_notification("J.A.R.V.I.S. ha risposto", jarvis_response)

        return jsonify({"response": jarvis_response})

    except openai.error.AuthenticationError as e:
        print(f"Errore di autenticazione OpenAI (DeepSeek): {e}")
        send_pushover_notification("Errore J.A.R.V.I.S.", "Problema di autenticazione con l'API. Controlla la chiave DeepSeek.")
        return jsonify({"response": "Mi dispiace, c'è un problema di autenticazione con i miei sistemi. Controlla la chiave API."}), 500
    except openai.error.APIError as e:
        print(f"Errore API OpenAI (DeepSeek): {e}")
        send_pushover_notification("Errore J.A.R.V.I.S.", f"Errore dall'API: {e}")
        return jsonify({"response": f"Mi dispiace, c'è stato un errore dall'API: {e}"}), 500
    except Exception as e:
        print(f"Errore generale nella funzione ask_jarvis: {e}")
        send_pushover_notification("Errore J.A.R.V.I.S.", f"Errore imprevisto: {e}")
        return jsonify({"response": f"Mi dispiace, c'è stato un problema imprevisto nel connettermi ai miei sistemi! Dettaglio: {str(e)}"})

# Se hai un endpoint root ("/") nel tuo app.py, mantienilo, altrimenti non è essenziale
@app.route('/')
def home():
    return "J.A.R.V.I.S. AI service is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', 5000))
