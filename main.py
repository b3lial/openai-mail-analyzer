from dotenv import load_dotenv
import os
import imaplib
import email
from datetime import datetime
import openai
import re

#mail_subject = "Update zum neuen Büro Interior"
mail_subject = "Update zum neuen"

# this programs reads amail threads and lets them analyse by openAI
def main():
    # load secrets from .env file
    load_dotenv()
    secret = os.environ.get('MAIL_PASSWORD')
    user = os.environ.get('MAIL_USER')
    server = os.environ.get('MAIL_SERVER')
    openai_token = os.environ.get('OPENAI_TOKEN')
    print(f'User: {user}')
    print(f'Server: {server}')

    # connect to mail server
    mail = check_login(user, secret, server)
    if mail is None:
        return
    
    # Use the list method to get the mailboxes
    print("Mailboxes:")
    status, mailbox_list = mail.list()
    if status == 'OK':
        for mailbox in mailbox_list:
            print(mailbox)

    # select inbox
    mail.select("INBOX")

    # search for mails
    status, email_ids = mail.search(None, f'(SUBJECT "{mail_subject}")')
    email_ids = email_ids[0].split()
    print(f"Found {len(email_ids)} emails with subject '{mail_subject}'")

    # parse mails
    emails = parse_mails(mail, email_ids)
    emails.sort(key=lambda email: email['date'])

    # Now, emails are sorted by date in ascending order.
    # You can access the email data like this:
    for email_data in emails:
        print(f"Email ID: {email_data['email_id']}, Date: {email_data['date']}, Subject: {email_data['sender']}")

    # close connection
    mail.close()
    mail.logout()

    # process mails
    for email in emails:
        openai_query = process_mail(email)
        openai_query += "\n\nSummarize the mail:\n\n"
    
        # send query to openAI and ask for a summary
        openai.api_key = openai_token
        # Sending the entire conversation as the prompt
        response = openai.Completion.create(
            engine="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    f"content": "[{openai_query}]"
                },
                {
                    "role": "user",
                    "content": "Summarize the mail."
                }
            ]
        )

        # Output the AI's response
        print(response.choices[0].text.strip())

# parse emails to get sender, content, etc and return result as list
def parse_mails(mail, email_ids):
    emails = []  # List to store email data

    # Fetch each email's data
    for e_id in email_ids:
        status, email_data = mail.fetch(e_id, '(RFC822)')
        raw_email = email_data[0][1]
        message = email.message_from_bytes(raw_email)

        # Extract email date, subject, sender, and content
        date = message.get('date')
        date_parsed = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
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
                    try:
                        content_str = content.decode('utf-8')
                    except UnicodeDecodeError:
                        content_str = ""
                    break
        else:
            # If not multipart, directly get the payload
            content = message.get_payload(decode=True)
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                content_str = ""

        # Append to the emails list
        emails.append({
            'subject': subject,
            'date': date_parsed,
            'email_id': e_id,
            'sender': sender,
            'content': content_str,
        })

    return emails

# Strip a mail to make it shorter
def process_mail(mail):
    skip_after = "________________________________"
    content = mail['content']
    # remove everything after skip_after
    content = content.split(skip_after)[0]
    # remove escaped line breaks
    content = content.replace("\r\n", "")

    query = f"On {mail['date']}, {mail['sender']} wrote:"
    query += content + "\n\n"

    return query

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