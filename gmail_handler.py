import os
import base64
import json
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from utils import log_action, extract_email_address

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def list_messages(service, query=''):
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    return messages

def get_message(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id).execute()
    headers = msg['payload']['headers']
    sender = next((h['value'] for h in headers if h['name']=='From'), None)
    subject = next((h['value'] for h in headers if h['name']=='Subject'), None)
    sender_email = extract_email_address(sender)
    return {'id': msg_id, 'from': sender_email, 'subject': subject}

def apply_rules(service, rules, dry_run=True, log_file="logs/actions.log"):
    """Apply rules to emails. If dry_run=True, only simulate actions."""
    messages = list_messages(service, query='in:inbox')
    for m in messages:
        msg = get_message(service, m['id'])
        action_taken = None
        for rule in rules['rules']:
            if rule['match_type'] == 'exact' and msg['from'] == rule['pattern']:
                action_taken = rule['action']
            elif rule['match_type'] == 'domain' and msg['from'].endswith(rule['pattern']):
                action_taken = rule['action']
            elif rule['match_type'] == 'regex' and re.match(rule['pattern'], msg['from']):
                action_taken = rule['action']
            if action_taken:
                break
        if not action_taken:
            action_taken = rules.get('default_action', 'keep')

        if dry_run:
            log_action(f"DRY-RUN: Would {action_taken} email from {msg['from']} subject: {msg['subject']}", log_file)
        else:
            if action_taken == 'delete':
                service.users().messages().trash(userId='me', id=msg['id']).execute()
            elif action_taken == 'move_to_spam':
                service.users().messages().modify(
                    userId='me', id=msg['id'], body={'addLabelIds': ['SPAM']}
                ).execute()
            elif action_taken == 'archive':
                service.users().messages().modify(
                    userId='me', id=msg['id'], body={'removeLabelIds': ['INBOX']}
                ).execute()
            log_action(f"ACTION: {action_taken} email from {msg['from']} subject: {msg['subject']}", log_file)
