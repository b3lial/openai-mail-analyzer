# openai-mail-analyzer
Uses OpenAI to summarize long mail threads or ask questions regarding its content

## Configuration
Run `pip install -r requirements.txt` to fetch dependencies. Afterwards, create a `.env` which contains your credentials:
```
MAIL_PASSWORD=<your imap password>
MAIL_USER=<your imap user>
MAIL_SERVER=<imap server dns record>
OPENAI_TOKEN=<your chatgpt token>
```

## Usage
Run `python main.py`. Afterwards, the tool asks for the topic of a mail thread and your question. Example:
```
16:01 $ python main.py 
What is the subject of the email thread?
You're Invited! Birthday Party on November 2nd
Found 2 emails with subject 'You're Invited! Birthday Party on November 2nd'
What do you want to know?
Write a very short summary of the mail thread 

-----------
AI Response
-----------

Christian invites Peter to his birthday party on November 2nd at 19:00 in Cologne. Peter accepts the invitation and expresses his excitement to celebrate with Christian. Both are looking forward to a fun-filled evening and creating lasting memories.
```
In case of problems or bug, take a look at the `analyzer.log` file

## ToDos
At the moment, `process_mail()` tries to strip each mail in a thread with a very primitive algorithm. We should use OpenAI for this task
