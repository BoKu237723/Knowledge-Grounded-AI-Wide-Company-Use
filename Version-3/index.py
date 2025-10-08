# department_ai_memory.py
import ollama
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import pickle
import re
import io
import zipfile
import xml.etree.ElementTree as ET

class DepartmentAI:
    def __init__(self):
        self.departments = ['finance', 'marketing', 'IT']
        self.service = None
        self.drive_service = None
        self.authenticate_services()
        
    def authenticate_services(self):
        """Authenticate Google Drive service"""
        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        
        self.drive_service = self.authenticate_service('drive', 'drive_token.pickle', SCOPES)
    
    def authenticate_service(self, service_name, token_file, scopes):
        """Authenticate a specific Google service"""
        creds = None
        
        # Load existing tokens
        try:
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
            print(f"✅ Loaded existing {service_name} credentials")
        except (FileNotFoundError, EOFError):
            print(f"🔄 New authentication required for {service_name}")
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print(f"✅ Refreshed {service_name} credentials")
                except Exception:
                    print(f"🔄 Refresh failed, getting new credentials for {service_name}")
                    creds = None
            
            if not creds:
                print(f"\n🎯 Setting up Google {service_name.upper()} access...")
                print("=" * 50)
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', 
                    scopes,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                )
                
                auth_url, _ = flow.authorization_url(
                    prompt='consent',
                    access_type='offline'
                )
                
                print("📋 PLEASE FOLLOW THESE STEPS:")
                print(f"1. Visit: {auth_url}")
                print("2. Authorize the application")
                print("3. Copy the authorization code")
                print("4. Paste it below\n")
                
                while True:
                    code = input("📥 Paste authorization code: ").strip()
                    if code:
                        break
                    print("❌ Please enter a valid code")
                
                try:
                    print("🔄 Exchanging code for access tokens...")
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    
                    with open(token_file, 'wb') as token:
                        pickle.dump(creds, token)
                    print(f"✅ {service_name.upper()} authentication successful!")
                    
                except Exception as e:
                    print(f"❌ Authentication failed: {e}")
                    return None
        
        # Build service
        try:
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"❌ Failed to build {service_name} service: {e}")
            return None

    def find_department_folders(self):
        """Find department folders in Google Drive"""
        if not self.drive_service:
            return {}
            
        department_folders = {}
        
        try:
            print("🔍 Searching for Company Reports folder...")
            
            query = "name='Company Reports' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(
                q=query, 
                spaces='drive', 
                fields='files(id, name)'
            ).execute()
            
            company_reports_folders = results.get('files', [])
            
            if not company_reports_folders:
                print("❌ 'Company Reports' folder not found")
                return {}
            
            company_reports_id = company_reports_folders[0]['id']
            print(f"✅ Found Company Reports folder")
            
            # Find department folders
            for department in self.departments:
                query = f"'{company_reports_id}' in parents and name='{department}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                results = self.drive_service.files().list(
                    q=query, 
                    spaces='drive', 
                    fields='files(id, name)'
                ).execute()
                
                dept_folders = results.get('files', [])
                
                if dept_folders:
                    department_folders[department] = dept_folders[0]['id']
                    print(f"✅ Found {department} folder")
                else:
                    print(f"⚠️ {department} folder not found")
            
            return department_folders
            
        except HttpError as error:
            print(f"❌ Error accessing Google Drive: {error}")
            return {}

    def discover_weekly_reports(self, department_folder_id, department_name):
        """Discover all weekly reports in a department folder"""
        if not self.drive_service:
            return {}
            
        weekly_reports = {}
        
        try:
            print(f"   🔍 Searching for documents in {department_name} folder...")
            
            # Find all files in the department folder
            query = f"'{department_folder_id}' in parents and trashed=false"
            results = self.drive_service.files().list(
                q=query,
                spaces='drive', 
                fields='files(id, name, mimeType)',
                pageSize=50
            ).execute()
            
            all_files = results.get('files', [])
            
            if not all_files:
                print(f"   ❌ No files found in {department_name} folder")
                return {}
            
            # Filter for supported file types
            supported_files = [
                f for f in all_files 
                if f['mimeType'] in [
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
                    'application/vnd.google-apps.document',  # Google Docs
                    'application/pdf',  # PDF files
                    'text/plain'  # Text files
                ]
            ]
            
            if not supported_files:
                print(f"   ❌ No supported files found in {department_name} folder")
                return {}
            
            print(f"   ✅ Found {len(supported_files)} supported files in {department_name} folder")
            
            # Pattern to match Week-XX format
            week_pattern = re.compile(r'Week[-\s]*(\d+)', re.IGNORECASE)
            
            for file in supported_files:
                file_name = file['name']
                match = week_pattern.search(file_name)
                
                if match:
                    week_number = match.group(1)
                    key = f'Week-{week_number}'
                else:
                    key = file_name
                
                weekly_reports[key] = {
                    'id': file['id'],
                    'name': file_name,
                    'mimeType': file['mimeType']
                }
                
                # Show file type icon
                file_type_icons = {
                    'application/vnd.google-apps.document': '📝',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '📄',
                    'application/pdf': '📕',
                    'text/plain': '📃'
                }
                icon = file_type_icons.get(file['mimeType'], '📎')
                print(f"      {icon} {key} ({file['mimeType'].split('/')[-1]})")
            
            return weekly_reports
            
        except HttpError as error:
            print(f"❌ Error discovering reports for {department_name}: {error}")
            return {}

    def extract_text_from_docx(self, file_content):
        """Extract text from .docx file content in memory"""
        try:
            # .docx is a zip file containing XML - process in memory
            with zipfile.ZipFile(io.BytesIO(file_content)) as docx:
                # Read the main document XML
                if 'word/document.xml' in docx.namelist():
                    document_xml = docx.read('word/document.xml')
                    
                    # Parse XML and extract text
                    root = ET.fromstring(document_xml)
                    
                    # Namespace for Word documents
                    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    
                    # Extract all text elements
                    text_elements = root.findall('.//w:t', ns)
                    text_content = ''.join(elem.text for elem in text_elements if elem.text)
                    
                    return text_content.strip()
                else:
                    return "Error: Could not find document content in .docx file"
                
        except Exception as e:
            return f"Error extracting text from .docx: {e}"

    def get_file_content_in_memory(self, file_id, file_name, mime_type):
        """Get file content directly in memory without saving to disk"""
        if not self.drive_service:
            return "Error: Drive service not available"
            
        try:
            print(f"      📖 Reading content from '{file_name}'...")
            
            # Choose the appropriate method based on file type
            if mime_type == 'application/vnd.google-apps.document':
                # Export Google Doc as plain text
                request = self.drive_service.files().export_media(
                    fileId=file_id,
                    mimeType='text/plain'
                )
            elif mime_type == 'application/pdf':
                # Export PDF as plain text
                request = self.drive_service.files().export_media(
                    fileId=file_id,
                    mimeType='text/plain'
                )
            elif mime_type == 'text/plain':
                # Download text file directly
                request = self.drive_service.files().get_media(fileId=file_id)
            else:
                # For .docx and other files, download the file content
                request = self.drive_service.files().get_media(fileId=file_id)
            
            # Download the file content to memory
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            content_bytes = file_content.read()
            
            # Process content based on file type
            if mime_type == 'application/vnd.google-apps.document':
                # Google Doc exported as text
                text_content = content_bytes.decode('utf-8')
            elif mime_type == 'application/pdf':
                # PDF exported as text
                text_content = content_bytes.decode('utf-8')
            elif mime_type == 'text/plain':
                # Text file
                text_content = content_bytes.decode('utf-8')
            elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                # .docx file - extract text
                text_content = self.extract_text_from_docx(content_bytes)
            else:
                text_content = f"Unsupported file type: {mime_type}"
            
            if text_content and not text_content.startswith("Error"):
                print(f"      ✅ Read {len(text_content)} characters from '{file_name}'")
            else:
                print(f"      ⚠️ Could not extract text from '{file_name}'")
                
            return text_content
            
        except HttpError as error:
            error_msg = f"Error reading file '{file_name}': {error}"
            print(f"      ❌ {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Error processing '{file_name}': {e}"
            print(f"      ❌ {error_msg}")
            return error_msg

    def load_department_data(self, department):
        """Load all data for a specific department"""
        try:
            print(f"\n📂 Loading data for {department} department...")
            
            # Find department folders
            department_folders = self.find_department_folders()
            
            if department not in department_folders:
                return f"Could not find folder for {department} department"
            
            department_folder_id = department_folders[department]
            
            # Discover all weekly reports
            weekly_reports = self.discover_weekly_reports(department_folder_id, department)
            
            if not weekly_reports:
                return f"No supported files found for {department} department"
            
            print(f"📄 Processing {len(weekly_reports)} files for {department}")
            
            # Load content from all reports
            all_content = []
            successful_reads = 0
            
            for report_name, report_info in weekly_reports.items():
                content = self.get_file_content_in_memory(
                    report_info['id'], 
                    report_info['name'], 
                    report_info['mimeType']
                )
                if content and not content.startswith("Error") and len(content.strip()) > 0:
                    all_content.append(f"\n--- {report_name} ---\n{content}")
                    successful_reads += 1
                else:
                    print(f"   ⚠️ Skipped {report_name} - no readable content")
            
            if not all_content:
                return f"No readable content found for {department} department"
            
            print(f"✅ Successfully loaded {successful_reads}/{len(weekly_reports)} files for {department}")
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
            print("🤔 Processing your question with AI...")
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
        print("\n🔍 Scanning for available department data...")
        available = []
        
        for department in self.departments:
            try:
                print(f"\n📊 Checking {department} department...")
                department_folders = self.find_department_folders()
                
                if department in department_folders:
                    weekly_reports = self.discover_weekly_reports(department_folders[department], department)
                    if weekly_reports:
                        available.append(department)
                        print(f"✅ {department} has data available")
                    else:
                        print(f"❌ {department} has no supported files")
                else:
                    print(f"❌ {department} folder not found")
                    
            except Exception as e:
                print(f"❌ Error checking {department} department: {e}")
                continue
                
        return available

def main():
    print("🔧 Company Department AI Assistant - Memory Only")
    print("=" * 55)
    print("✅ Reads files directly in memory - no downloads to disk")
    print("✅ Supports: Google Docs, Word (.docx), PDF, Text files")
    
    # Check prerequisites
    try:
        with open('credentials.json', 'r') as f:
            print("✅ credentials.json found")
    except FileNotFoundError:
        print("❌ Missing: credentials.json")
        return
    
    try:
        with open('ai_prompt.txt', 'r', encoding='utf-8') as f:
            print("✅ ai_prompt.txt found")
    except FileNotFoundError:
        print("❌ Missing: ai_prompt.txt")
        return
    
    # Initialize AI
    print("\n🔄 Initializing Google Drive connection...")
    ai = DepartmentAI()
    
    if not ai.drive_service:
        print("❌ Failed to initialize Google Drive service")
        return
    
    # Check available departments
    available_departments = ai.get_available_departments()
    
    if not available_departments:
        print("\n❌ No departments with data found!")
        return
    
    print(f"\n🎉 Ready! Available Departments: {', '.join(available_departments)}")
    print("Type 'quit' to exit\n")

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

        print("\n🤔 Thinking...")
        answer = ai.query_ollama(department, question)
        print(f"\n=== {department.upper()} DEPARTMENT ANSWER ===")
        print(answer)
        print("=" * 50 + "\n")

if __name__ == "__main__":
    main()