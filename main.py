from dotenv import load_dotenv
import os
import imaplib
import email
from datetime import datetime

# this programs reads amail threads and lets them analyse by openAI
def main():
    # load secrets from .env file
    load_dotenv()
    secret = os.environ.get('MAIL_PASSWORD')
    user = os.environ.get('MAIL_USER')
    server = os.environ.get('MAIL_SERVER')
    print(f'User: {user}')
    print(f'Server: {server}')

    # connect to mail server
    mail = check_login(user, secret, server)

def check_login(username, password, server):
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(server)
        
        # Try to login
        mail.login(username, password)
        
        # If successful, print a message and return the mail object
        print(f"Login successful for {username}")
        return mail

    except imaplib.IMAP4.error as e:
        # If login fails, print a message and return None
        print(f"Login failed for {username}: {str(e)}")
        return None
    

if __name__ == "__main__":
    main()