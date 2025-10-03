# requirements.txt
# ollama
# google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

import ollama
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import pickle
import re

class DepartmentAI:
    def __init__(self):
        self.departments = ['finance', 'marketing', 'IT']
        self.service = self.authenticate_google_docs()
        self.drive_service = self.authenticate_google_drive()
        
    def authenticate_google_docs(self):
        """Authenticate and create Google Docs API service"""
        SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
        creds = None
        
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return build('docs', 'v1', credentials=creds)
    
    def authenticate_google_drive(self):
        """Authenticate and create Google Drive API service"""
        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        creds = None
        
        if os.path.exists('drive_token.pickle'):
            with open('drive_token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('drive_token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return build('drive', 'v3', credentials=creds)
    
    def find_department_folders(self):
        """Find department folders in Google Drive"""
        department_folders = {}
        
        try:
            # Search for the main "Company Reports" folder
            query = "name='Company Reports' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            company_reports_folder = results.get('files', [])
            
            if not company_reports_folder:
                print("Warning: 'Company Reports' folder not found in Google Drive")
                return department_folders
            
            company_reports_id = company_reports_folder[0]['id']
            
            # Find department folders inside Company Reports
            for department in self.departments:
                query = f"'{company_reports_id}' in parents and name='{department}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                results = self.drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                dept_folders = results.get('files', [])
                
                if dept_folders:
                    department_folders[department] = dept_folders[0]['id']
                else:
                    print(f"Warning: '{department}' folder not found in Company Reports")
            
            return department_folders
            
        except HttpError as error:
            print(f"Error finding department folders: {error}")
            return {}
    
    def discover_weekly_reports(self, department_folder_id):
        """Discover all weekly reports in a department folder"""
        weekly_reports = {}
        
        try:
            # Find all Google Docs in the department folder
            query = f"'{department_folder_id}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false"
            results = self.drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            docs = results.get('files', [])
            
            # Pattern to match Week-XX format
            week_pattern = re.compile(r'Week[-\s]*(\d+)', re.IGNORECASE)
            
            for doc in docs:
                doc_name = doc['name']
                match = week_pattern.search(doc_name)
                
                if match:
                    week_number = match.group(1)
                    weekly_reports[f'week{week_number}'] = doc['id']
                else:
                    # Also include documents that don't follow Week-XX pattern but are in the folder
                    weekly_reports[doc_name.lower().replace(' ', '_')] = doc['id']
            
            return weekly_reports
            
        except HttpError as error:
            print(f"Error discovering weekly reports: {error}")
            return {}
    
    def get_document_content(self, document_id):
        """Extract text content from a Google Doc"""
        try:
            document = self.service.documents().get(documentId=document_id).execute()
            content = []
            
            def extract_text(element):
                if 'paragraph' in element:
                    for elem in element['paragraph'].get('elements', []):
                        if 'textRun' in elem:
                            content.append(elem['textRun']['content'])
                elif 'table' in element:
                    for row in element['table']['tableRows']:
                        for cell in row.get('tableCells', []):
                            for elem in cell.get('content', []):
                                extract_text(elem)
            
            for element in document.get('body', {}).get('content', []):
                extract_text(element)
            
            return ''.join(content)
            
        except HttpError as error:
            return f"Error reading document: {error}"
    
    def load_department_data(self, department):
        """Load all data for a specific department"""
        try:
            # Find department folders
            department_folders = self.find_department_folders()
            
            if department not in department_folders:
                return f"Could not find folder for {department} department"
            
            department_folder_id = department_folders[department]
            
            # Discover all weekly reports
            weekly_reports = self.discover_weekly_reports(department_folder_id)
            
            if not weekly_reports:
                return f"No weekly reports found for {department} department"
            
            # Load content from all reports
            all_content = []
            for report_name, doc_id in weekly_reports.items():
                content = self.get_document_content(doc_id)
                all_content.append(f"\n--- {report_name.upper()} ---\n{content}")
            
            return '\n'.join(all_content)
            
        except Exception as e:
            return f"Error loading {department} department data: {e}"
    
    def load_ai_prompt(self, department):
        """Load and format the AI prompt with department data"""
        try:
            with open('ai_prompt.txt', 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            department_data = self.load_department_data(department)
            
            prompt_template = prompt_template.replace('{departments}', ', '.join(self.departments))
            prompt_template = prompt_template.replace('{department}', department.upper())
            prompt_template = prompt_template.replace('{department_data}', department_data)

            return prompt_template
            
        except Exception as e:
            return f"Error loading AI prompt: {e}"
    
    def query_ollama(self, department, question):
        """Query Ollama with the department-specific context"""
        system_prompt = self.load_ai_prompt(department)
        if not system_prompt or system_prompt.startswith("Error"):
            return f"Error: Could not load AI prompt - {system_prompt}"
        
        try:
            response = ollama.chat(model='llama3.1:8b', messages=[
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': question
                }
            ])
            return response['message']['content']
        except Exception as e:
            return f"Error in query_ollama: {e}"
    
    def get_available_departments(self):
        """Get list of departments that have data available"""
        available = []
        for department in self.departments:
            try:
                department_folders = self.find_department_folders()
                if department in department_folders:
                    weekly_reports = self.discover_weekly_reports(department_folders[department])
                    if weekly_reports:
                        available.append(department)
            except Exception as e:
                print(f"Error checking {department} department: {e}")
                continue
        return available
    
    def list_available_reports(self, department):
        """List all available reports for a department"""
        try:
            department_folders = self.find_department_folders()
            if department in department_folders:
                weekly_reports = self.discover_weekly_reports(department_folders[department])
                return list(weekly_reports.keys())
            return []
        except Exception as e:
            print(f"Error listing reports for {department}: {e}")
            return []

def main():
    ai = DepartmentAI()
    print("=== Company Department AI Assistant ===")
    
    available_departments = ai.get_available_departments()
    print("Available Departments:", ", ".join(available_departments))
    
    # Show available reports for each department
    for dept in available_departments:
        reports = ai.list_available_reports(dept)
        print(f"  {dept.upper()} reports: {', '.join(reports)}")
    
    print("\nType 'quit' to exit\n")

    while True:
        department = input("Which department do you want to ask about?\nYou: ").lower()
        if department == 'quit':
            break
        if department not in ai.departments:
            print("Invalid department. Please choose from:", ", ".join(ai.departments))
            continue

        question = input(f"What is your question for the {department} department?\nYou: ")

        if question.lower() == 'quit':
            break

        print("\nThinking...")
        answer = ai.query_ollama(department, question)
        print(f"\n=== {department.upper()} DEPARTMENT ANSWER ===")
        print(answer)
        print("=" * 50 + "\n")

if __name__ == "__main__":
    main()