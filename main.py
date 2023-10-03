from dotenv import load_dotenv
import os
import imaplib
import email
from datetime import datetime
import openai
import logging
from dateutil import parser

# set logging level
logging.basicConfig(filename='analyzer.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# this programs reads amail threads and lets them analyse by openAI
def main():
    # load secrets from .env file
    load_dotenv()
    secret = os.environ.get('MAIL_PASSWORD')
    user = os.environ.get('MAIL_USER')
    server = os.environ.get('MAIL_SERVER')
    openai_token = os.environ.get('OPENAI_TOKEN')
    logging.info(f'User: {user}')
    logging.info(f'Server: {server}')

    # connect to mail server
    mail = check_login(user, secret, server)
    if mail is None:
        return
    
    # Use the list method to get the mailboxes
    logging.info("Mailboxes:")
    status, mailbox_list = mail.list()
    if status == 'OK':
        for mailbox in mailbox_list:
            logging.info(mailbox)

    # select inbox
    mail.select("INBOX", readonly=True)

    # ask user for email subject
    print("What is the subject of the email thread?")
    #mail_subject = "Update zum neuen"
    mail_subject = input()

    # search for mails
    mail.literal  = mail_subject.encode('utf-8')
    status, email_ids = mail.uid('SEARCH', 'CHARSET', 'UTF-8', 'SUBJECT')
    email_ids = email_ids[0].decode('utf-8').split()
    print(f"Found {len(email_ids)} emails with subject '{mail_subject}'")

    # parse mails
    emails = parse_mails(mail, email_ids)
    emails.sort(key=lambda email: email['date'])

    # Now, emails are sorted by date in ascending order.
    # You can access the email data like this:
    for email_data in emails:
        logging.info(f"Email ID: {email_data['email_id']}, Date: {email_data['date']}, From: {email_data['sender']}")

    # close connection
    mail.close()
    mail.logout()

    # process mails
    openai_query = ""
    for email in emails:
        openai_query += process_mail(email)
        openai_query += "\n\n"

    # ask user for input and read from stdin
    print("What do you want to know?")
    user_query = input()

    # send query to openAI 
    openai.api_key = openai_token
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {
                    "role": "user",
                    'content': f'Dies ist ein Email-Verkauf. {user_query}: \n\n {openai_query}'
                }
        ]
    )

    # Output the AI's response
    print("\n-----------\nAI Response\n-----------\n")
    print(response["choices"][0]["message"]["content"])

# parse emails to get sender, content, etc and return result as list
def parse_mails(mail, email_ids):
    emails = []  # List to store email data

    # Fetch each email's data
    for e_id in email_ids:
        status, email_data = mail.uid('fetch', e_id, '(RFC822)')
        raw_email = email_data[0][1]
        message = email.message_from_bytes(raw_email)

        # Extract email date, subject, sender, and content
        date = message.get('date')
        date_parsed = None
        try:
            date_parsed = parser.parse(date)
        except ValueError:
            logging.error(f"Failed to parse date {date}")
            date_parsed = ''
        subject = message.get('subject')
        sender = message.get('from')
        
        # Getting the content
        content_str = ""
        # If the email message is multipart
        if message.is_multipart():
            # Iterating through each part
            for part in message.walk():
                # If text/plain or text/html, get the payload
                if part.get_content_type() == 'text/plain' or part.get_content_type() == 'text/html':
                    content = part.get_payload(decode=True)
                    content_str = decode_string(content)
                    break
        else:
            # If not multipart, directly get the payload
            content_str = decode_string(message.get_payload(decode=True))

        # Append to the emails list
        emails.append({
            'subject': subject,
            'date': date_parsed,
            'email_id': e_id,
            'sender': sender,
            'content': content_str,
        })

    return emails

# Try to decode a byte string using different encodings
def decode_string(content):
    encoding_types = ['utf-8', 'ascii', 'latin-1']  # list of possible encodings
    for encoding in encoding_types:
        try:
            decoded_text = content.decode(encoding)
            logging.info(f"Successfully decoded using {encoding}")
            return decoded_text
        except UnicodeDecodeError:
            logging.info(f"Failed to decode using {encoding}")
            continue
    return ""


# Strip a mail to make it shorter
def process_mail(mail):
    content = mail['content']
    
    # remove everything after skip_after
    skip_after = "Von:"
    content = content.split(skip_after)[0]

    # search for first line which starts with > and remove everything after and first 3 lines above
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(">"):
            lines = lines[:i-3]
            break
    content = "\n".join(lines)

    query = f"Am {mail['date']}, schrieb {mail['sender']}: "
    query += content + "\n\n"
    logging.info(f'Process mail result: {query}')

    return query

def check_login(username, password, server):
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(server)
        
        # Try to login
        mail.login(username, password)
        
        # If successful, print a message and return the mail object
        logging.info(f"Login successful for {username}")
        return mail

    except imaplib.IMAP4.error as e:
        # If login fails, print a message and return None
        logging.error(f"Login failed for {username}: {str(e)}")
        return None
    

if __name__ == "__main__":
    main()