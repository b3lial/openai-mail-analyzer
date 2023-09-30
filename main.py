from dotenv import load_dotenv
import os

def main():
    load_dotenv()
    secret = os.environ.get('MAIL_PASSWORD')
    user = os.environ.get('MAIL_USER')
    print(secret)
    print(user)

if __name__ == "__main__":
    main()