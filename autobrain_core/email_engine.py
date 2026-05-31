import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv

load_dotenv()

def connect_imap():
    """Connette al server IMAP usando le credenziali nel .env"""
    host = os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com")
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    
    if not user or not password:
        return None, "❌ Credenziali email mancanti nel file .env (EMAIL_USER, EMAIL_PASSWORD)."
    
    try:
        mail = imaplib.IMAP4_SSL(host)
        mail.login(user, password)
        return mail, None
    except Exception as e:
        return None, f"❌ Errore di connessione email: {e}"

def cerca_email_importanti(query="esame"):
    """Cerca email importanti basate su una parola chiave e restituisce un riassunto."""
    mail, error = connect_imap()
    if error:
        return error
    
    try:
        mail.select("inbox")
        # Cerca email non lette o filtrate per query
        status, messages = mail.search(None, f'OR (UNSEEN) (BODY "{query}")')
        
        if status != "OK":
            return "❌ Errore durante la ricerca delle email."
        
        mail_ids = messages[0].split()
        if not mail_ids:
            return f"📭 Nessuna email importante trovata per '{query}'."
        
        # Prendi le ultime 5 email
        results = []
        for i in mail_ids[-5:]:
            res, msg_data = mail.fetch(i, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    sender = msg.get("From")
                    date = msg.get("Date")
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()
                    
                    results.append(f"📌 **Oggetto:** {subject}\n   **Da:** {sender}\n   **Data:** {date}\n   **Estratto:** {body[:200]}...")
        
        mail.logout()
        return "\n\n".join(results)
    except Exception as e:
        return f"❌ Errore durante la lettura delle email: {e}"

if __name__ == "__main__":
    # Test veloce
    # print(cerca_email_importanti("esame"))
    pass
