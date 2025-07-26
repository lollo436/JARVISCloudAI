import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai # Sì, usiamo ancora la libreria 'openai' ma la configureremo per DeepSeek
import requests # Necessario per Pushover

# Carica le variabili d'ambiente da un file .env in locale (utile per i test sul tuo computer)
# Su Render, le variabili verranno caricate automaticamente dall'ambiente.
load_dotenv()

app = Flask(__name__)

# --- CONFIGURAZIONE API DEEPSEEK ---
# Recupera la chiave API dalla variabile d'ambiente.
# È FONDAMENTALE che su Render la tua variabile sia stata rinominata in DEEPSEEK_API_KEY
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    # Questa stampa apparirà nei log di Render se la variabile non è configurata correttamente.
    print("ERRORE: La variabile DEEPSEEK_API_KEY non è impostata nelle variabili d'ambiente di Render.")
    # Puoi decidere come gestire questo errore se l'applicazione non può funzionare senza la chiave.

# Imposta l'endpoint base dell'API per DeepSeek. Questo è CRUCIALE per indirizzare le richieste a DeepSeek.
openai.api_base = "https://api.deepseek.com/v1"
# Assegna la tua chiave DeepSeek alla variabile API key della libreria openai.
openai.api_key = DEEPSEEK_API_KEY

# --- CONFIGURAZIONE PUSHOVER ---
# Recupera le chiavi Pushover dalle variabili d'ambiente.
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

def send_pushover_notification(title, message):
    """
    Invia una notifica tramite Pushover.
    """
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
    """
    Endpoint per ricevere comandi e ottenere risposte da DeepSeek AI.
    """
    try:
        data = request.json
        command = data.get('command') # Ottieni il comando dal JSON in ingresso

        if not command:
            # Se il campo 'command' non è presente nel JSON, restituisci un errore.
            return jsonify({"response": "Comando mancante nel JSON."}), 400

        print(f"Comando ricevuto: {command}") # Stampa il comando nei log di Render per debugging

        # Qui definiamo la "personalità" di J.A.R.V.I.S. (il prompt di sistema)
        messages = [
            {"role": "system", "content": "Sei un assistente AI chiamato J.A.R.V.I.S. Rispondi in italiano. Sii conciso e diretto, ma sempre educato e disponibile. Se non hai informazioni, chiedi maggiori dettagli o ammetti di non sapere. Parli in modo leggermente formale ma amichevole."},
            {"role": "user", "content": command} # Il comando dell'utente
        ]

        # Fai la chiamata all'API di DeepSeek AI
        # Il modello da usare per DeepSeek dovrebbe essere "deepseek-chat" o un altro nome
        # specificato nella loro documentazione (es. "deepseek-coder").
        chat_completion = openai.ChatCompletion.create(
            model="deepseek-chat", # <-- VERIFICA QUESTO NOME SULLA DOCUMENTAZIONE UFFICIALE DI DEEPSEEK!
            messages=messages,
            stream=False # Imposta a False per ricevere la risposta completa in una volta
        )

        # Estrai il contenuto della risposta dal modello AI
        jarvis_response = chat_completion.choices[0].message.content

        # Invia una notifica Pushover con la risposta di J.A.R.V.I.S.
        send_pushover_notification("J.A.R.V.I.S. ha risposto", jarvis_response)

        # Restituisci la risposta di J.A.R.V.I.S. come JSON
        return jsonify({"response": jarvis_response})

    # --- GESTIONE DEGLI ERRORI ---
    # Questi blocchi catturano errori specifici dalla libreria openai/DeepSeek.
    except openai.error.AuthenticationError as e:
        print(f"Errore di autenticazione API (DeepSeek): {e}")
        send_pushover_notification("Errore J.A.R.V.I.S.", "Problema di autenticazione con l'API di DeepSeek. Controlla la chiave.")
        return jsonify({"response": "Mi dispiace, c'è un problema di autenticazione con i miei sistemi. Controlla la chiave API DeepSeek."}), 500
    except openai.error.APIError as e:
        print(f"Errore API (DeepSeek): {e}")
        send_pushover_notification("Errore J.A.R.V.I.S.", f"Errore dall'API di DeepSeek: {e}")
        return jsonify({"response": f"Mi dispiace, c'è stato un errore dall'API di DeepSeek: {e}"}), 500
    except Exception as e:
        # Questo blocco cattura qualsiasi altro errore imprevisto.
        print(f"Errore generale nella funzione ask_jarvis: {e}")
        send_pushover_notification("Errore J.
