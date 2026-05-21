import os
import webbrowser
import subprocess
from spotify_handler import spotify_manager

def execute_command(command: dict):
    """
    Esegue l'azione richiesta sulla base del JSON ricevuto.
    Esempio command: {"azione": "cerca_youtube", "parametro": "canzone rock"}
    """
    azione = command.get("azione")
    parametro = command.get("parametro", "")

    if azione == "apri_browser":
        # Gestione specifica per Brave o ricerca generica
        if "brave" in parametro.lower() or parametro == "":
            os.system("start brave")
            return "Apro Brave."
        url = parametro if parametro.startswith("http") else f"https://www.google.com/search?q={parametro}"
        webbrowser.open(url)
        
        if parametro.startswith("http"):
            import urllib.parse
            domain = urllib.parse.urlparse(parametro).netloc.replace("www.", "")
            if not domain:
                domain = parametro.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "")
            
            # Rimuove il TLD (.com, .it, ecc.) per rendere la pronuncia più naturale
            readable_name = domain.split('.')[0] if '.' in domain else domain
            return f"Apro {readable_name}."
        else:
            return f"Cerco {parametro} sul browser."

    elif azione == "cerca_youtube":
        url = f"https://www.youtube.com/results?search_query={parametro}"
        webbrowser.open(url)
        return f"Sto cercando {parametro} su YouTube."

    elif azione == "riproduci_spotify":
        return spotify_manager.play(parametro)

    elif azione == "apri_app":
        # Mappa di reindirizzamento per servizi comuni che l'utente chiama "app" ma sono web
        web_fallbacks = {
            "youtube": "https://www.youtube.com",
            "spotify": "https://www.spotify.com",
            "google": "https://www.google.com",
            "chatgpt": "https://chat.openai.com",
            "netflix": "https://www.netflix.com"
        }
        
        app_name = parametro.lower().strip()
        if app_name in web_fallbacks:
            webbrowser.open(web_fallbacks[app_name])
            return f"Apro {parametro} nel browser, signore."

        # Tenta di aprire un'app comune o via comando shell
        try:
            os.system(f"start {parametro}")
            return f"Tentativo di apertura di {parametro} avviato."
        except:
            return f"Non sono riuscito ad aprire l'app {parametro}."

    elif azione == "mostra_testo":
        # Crea un file Markdown temporaneo nel vault e lo apre
        try:
            convo_vault = os.getenv("CONVO_VAULT_PATH")
            if not convo_vault:
                return "Errore: Percorso vault non configurato."
            
            from datetime import datetime
            filename = f"Nota_Jarvis_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.md"
            filepath = os.path.join(convo_vault, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# Documento richiesto a Jarvis\n\n{parametro}")
            
            os.system(f"start {filepath}")
            return f"Le ho inviato il documento testuale sullo schermo, signore."
        except Exception as e:
            print(f"⚠️ Errore apertura testo: {e}")
            return "Non sono riuscito a generare il documento testuale."

    elif azione == "messaggio":
        # Semplice risposta testuale
        return parametro

    else:
        return "Comando non riconosciuto dal modulo di esecuzione."

if __name__ == "__main__":
    # Test
    print(execute_command({"azione": "cerca_youtube", "parametro": "Eminem"}))
