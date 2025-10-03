import ollama
class DepartmentAI:
    def __init__(self):
        self.departments = ["finance", "marketing", "IT"]
        self.department_files = {
            "finance": "finance.txt",
            "marketing": "marketing.txt", 
            "IT": "IT.txt"
        }
        
    def load_department_data(self, department: str) -> str:
        """Load the content of a department's text file"""
        filename = self.department_files.get(department)
        if not filename or not os.path.exists(filename):
            return f"Error: Could not find data file for {department} department."
            
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error reading {filename}: {e}"
    
    def load_ai_prompt(self, department: str):
        """Load and customize the AI prompt template"""
        try:
            with open('ai_prompt.txt', 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # Load the actual department data from the file
            department_data = self.load_department_data(department)
            
            # Replace placeholders with actual data
            prompt_template = prompt_template.replace('{departments}', ', '.join(self.departments))
            prompt_template = prompt_template.replace('{department}', department.upper())
            prompt_template = prompt_template.replace('{department_data}', department_data)
            
            return prompt_template
        except FileNotFoundError:
            print("Error: ai_prompt.txt file not found")
            return None
        except Exception as e:
            print(f"Error in loading AI prompt: {e}")
            return None
    
    def query_ollama(self, department: str, question: str) -> str:
        """Query Ollama with department context and question"""
        
        # Load the customized prompt
        system_prompt = self.load_ai_prompt(department)
        
        if not system_prompt:
            return "Error: Could not load AI prompt template"
        
        try:
            response = ollama.chat(
                model='llama3.1:8b',
                messages=[
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user', 
                        'content': question
                    }
                ]
            )
            return response['message']['content']
            
        except Exception as e:
            return f"Error querying Ollama: {str(e)}"
    
    def get_available_departments(self) -> list:
        """Return list of available departments"""
        available = []
        for dept in self.departments:
            if os.path.exists(self.department_files[dept]):
                available.append(dept)
        return available

def create_ai_prompt_file():
    """Create the AI prompt template file"""
    prompt_content = """You are an AI assistant for a company with access to department reports and data.

AVAILABLE DEPARTMENTS: {departments}

CONTEXT FROM {department} DEPARTMENT:
{department_data}

INSTRUCTIONS:
1. Answer questions based ONLY on the information provided in the department data above
2. Be specific and include relevant numbers, dates, names, and details when available
3. If the information isn't available in the context, clearly state: "I don't have that information in the department reports."
4. Keep answers professional, helpful, and accurate
5. Do not make up or assume any information not present in the department data
6. Focus on providing actionable insights from the available data

Please provide a helpful response to the user's question based on the department information above."""
    
    try:
        with open('ai_prompt.txt', 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        print("ai_prompt.txt created successfully!")
    except Exception as e:
        print(f"Error creating ai_prompt.txt: {e}")

def create_sample_department_files():
    """Create sample department data files"""
    
    # Sample finance data
    finance_content = """FINANCE DEPARTMENT - QUARTERLY REPORT Q3 2024

FINANCIAL PERFORMANCE SUMMARY:
• Total Revenue: $8,450,000 (15.2% increase from Q2)
• Operating Expenses: $5,210,000
• Net Profit: $1,845,000 (21.8% margin)
• Cash on Hand: $3,200,000
• Accounts Receivable: $1,150,000
• Accounts Payable: $890,000

BUDGET ALLOCATIONS BY DEPARTMENT:
• Marketing: $1,200,000 (23% of total budget)
• IT: $950,000 (18% of total budget) 
• Operations: $1,850,000 (35% of total budget)
• R&D: $750,000 (14% of total budget)
• HR & Admin: $460,000 (9% of total budget)

KEY FINANCIAL METRICS:
• Gross Profit Margin: 42.3%
• Operating Margin: 28.5%
• Current Ratio: 2.8:1
• Debt-to-Equity: 0.35
• ROI: 18.7%

UPCOMING FINANCIAL EVENTS:
• Q4 Budget Planning: October 15-30, 2024
• Annual Audit: November 10-25, 2024
• Tax Filing Deadline: December 15, 2024
• Investor Meeting: January 15, 2025

EXPENSE BREAKDOWN:
• Employee Salaries: $2,800,000
• Software Licenses: $450,000
• Office Rent & Utilities: $320,000
• Marketing Campaigns: $680,000
• Equipment & Hardware: $410,000
• Travel & Entertainment: $150,000

FINANCE TEAM CONTACTS:
• CFO: Sarah Johnson (ext. 101)
• Financial Controller: Michael Chen (ext. 102)
• Accounts Payable: Lisa Rodriguez (ext. 103)
• Accounts Receivable: David Kim (ext. 104)
• Budget Analyst: Emily Watson (ext. 105)

APPROVAL PROCESSES:
• Expenses under $1,000: Department Manager approval
• Expenses $1,000-$5,000: Finance Director approval
• Expenses over $5,000: CFO approval required
• Capital expenditures over $10,000: Board approval needed

FINANCIAL POLICIES:
• Expense reports must be submitted within 30 days
• Corporate cards must be reconciled weekly
• Budget transfers between departments require CFO approval
• All contracts over $25,000 require legal review"""

    # Sample marketing data
    marketing_content = """MARKETING DEPARTMENT - Q3 2024 PERFORMANCE REPORT

CAMPAIGN PERFORMANCE:
• "Digital Transformation 2024" Campaign:
  - Reach: 2.5 million impressions
  - Engagement Rate: 4.8%
  - Cost per Lead: $42.50
  - Total Leads Generated: 8,450

• "Enterprise Solutions" Campaign:
  - Reach: 1.8 million impressions  
  - Engagement Rate: 3.2%
  - Cost per Lead: $68.75
  - Total Leads Generated: 3,200

DIGITAL MARKETING METRICS:
• Website Traffic: 650,000 monthly visitors (32% growth)
• Social Media Followers: 285,000 across all platforms
• Email List Size: 125,000 subscribers
• Blog Posts Published: 45 articles this quarter
• Average Time on Site: 4 minutes 25 seconds

CONVERSION RATES:
• Overall Conversion Rate: 6.8%
• Landing Page Conversion: 12.4%
• Email Campaign CTR: 8.9%
• Social Media CTR: 3.2%
• Paid Search CTR: 5.6%

MARKETING BUDGET BREAKDOWN:
• Digital Advertising: $450,000
• Content Creation: $180,000
• Events & Conferences: $320,000
• PR & Media Relations: $95,000
• Tools & Software: $75,000
• Agency Fees: $80,000

UPCOMING CAMPAIGNS & EVENTS:
• Q4 Product Launch: "Project Nexus" - October 15, 2024
• Tech Industry Conference: November 5-7, 2024 (Booth #302)
• Holiday Marketing Campaign: November 15 - December 31, 2024
• Annual Customer Summit: January 20-22, 2025

MARKETING TEAM STRUCTURE:
• CMO: Jennifer Martinez
• Digital Marketing Manager: Robert Brown
• Content Strategy Lead: Amanda Wilson
• Social Media Specialist: Kevin Lee
• SEO Analyst: Michelle Garcia
• Event Coordinator: Thomas Anderson

BRAND GUIDELINES:
• Primary Colors: Blue (#0056b3) and Gray (#333333)
• Logo Usage: Minimum 20px clearance space required
• Font: Inter for digital, Helvetica for print
• Voice: Professional, innovative, customer-focused
• Tagline: "Transforming Business Through Technology"

COMPETITIVE ANALYSIS:
• Market Share: 18% (3% increase from last quarter)
• Top Competitors: TechGlobal, InnovateCorp, SolutionWorks
• Key Differentiators: 24/7 customer support, AI integration, customizable solutions

SOCIAL MEDIA PERFORMANCE:
• LinkedIn: 85,000 followers, 12% engagement rate
• Twitter: 95,000 followers, 8% engagement rate  
• Facebook: 65,000 followers, 6% engagement rate
• Instagram: 40,000 followers, 15% engagement rate"""

    # Sample IT data
    it_content = """IT DEPARTMENT - SYSTEMS STATUS REPORT Q3 2024

INFRASTRUCTURE OVERVIEW:
• Total Servers: 245 (85% virtualized)
• Network Devices: 180 switches, 45 routers
• Storage Capacity: 2.5 PB total (1.8 PB utilized)
• Cloud Services: AWS (60%), Azure (25%), Google Cloud (15%)

SYSTEM PERFORMANCE METRICS:
• Network Uptime: 99.98%
• Server Uptime: 99.95%
• Average Response Time: 85ms
• Bandwidth Utilization: 68% peak
• Storage I/O: 45,000 IOPS average

SECURITY STATUS:
• Security Incidents: 2 minor incidents (both resolved)
• Phishing Attempts Blocked: 1,245 this quarter
• Malware Detections: 38 (all contained)
• Security Patches Applied: 245 critical patches
• Vulnerability Scans: 12 completed, 3 medium risks remaining

HELP DESK STATISTICS:
• Total Tickets: 1,845 (15% decrease from Q2)
• Average Resolution Time: 3.2 hours
• First Contact Resolution: 72%
• User Satisfaction: 4.6/5.0
• Common Issues: Password resets (35%), Software access (25%), Hardware issues (20%)

CURRENT PROJECTS:
• Cloud Migration Project: 70% complete (ETA: December 2024)
• Network Infrastructure Upgrade: Phase 2 in progress
• CRM Implementation: Salesforce migration (ETA: January 2025)
• Security Enhancement: Multi-factor authentication rollout
• Hardware Refresh: 150 workstations to be replaced

IT TEAM STRUCTURE:
• CIO: Dr. Richard Thompson
• Infrastructure Manager: Maria Gonzalez
• Security Lead: James Wilson
• Help Desk Supervisor: Patricia Lee
• Network Engineer: Brian Chen
• Systems Administrator: Kevin Roberts
• Developers: 4 full-time, 2 contractors

SOFTWARE & LICENSES:
• Microsoft 365: 450 licenses
• Adobe Creative Cloud: 25 licenses
• Development Tools: 85 licenses
• Security Software: 500 endpoints protected
• CRM Users: 150 licensed seats

HARDWARE INVENTORY:
• Workstations: 450 computers (Dell OptiPlex, Lenovo ThinkCentre)
• Laptops: 200 units (Dell Latitude, MacBook Pro)
• Mobile Devices: 75 company phones (iPhone, Samsung)
• Printers: 45 network printers
• Conference Room AV: 15 systems

DISASTER RECOVERY & BACKUP:
• Backup Frequency: Daily incremental, weekly full
• Recovery Time Objective: 4 hours
• Recovery Point Objective: 1 hour
• Data Retention: 7 years for financial data, 3 years for general data

UPCOMING MAINTENANCE:
• Network Maintenance: October 20, 2024 (2am-6am)
• Server Patching: Every Sunday 10pm-2am
• Security Audit: November 15-20, 2024
• System Upgrade: December 10, 2024 (planned downtime 4 hours)

IT POLICIES:
• Password Requirements: 12 characters, complexity enabled
• Data Classification: Public, Internal, Confidential, Restricted
• Remote Access: VPN required for external connections
• Software Installation: Admin approval required
• Data Backup: Critical data backed up daily"""

    # Write department files
    files = {
        "finance.txt": finance_content,
        "marketing.txt": marketing_content,
        "IT.txt": it_content
    }
    
    for filename, content in files.items():
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"{filename} created successfully!")
        except Exception as e:
            print(f"Error creating {filename}: {e}")

def main():
    ai = DepartmentAI()
    
    print("=== Company Department AI Assistant ===")
    print("Available departments:", ", ".join(ai.get_available_departments()))
    print("Type 'quit' to exit\n")
    
    while True:
        # Get department input
        department = input("Which department do you want to ask about? (finance/marketing/IT): ").strip().lower()
        
        if department == 'quit':
            break
            
        if department not in ai.departments:
            print("Invalid department. Please choose from: finance, marketing, IT")
            continue
            
        if not os.path.exists(ai.department_files[department]):
            print(f"Data file for {department} department not found.")
            continue
        
        # Get question
        question = input(f"What's your question for the {department} department?\nQuestion: ").strip()
        
        if question.lower() == 'quit':
            break
            
        print("\nThinking...")
        
        # Get answer from AI
        answer = ai.query_ollama(department, question)
        
        print(f"\n=== {department.upper()} DEPARTMENT ANSWER ===")
        print(answer)
        print("=" * 50 + "\n")

if __name__ == "__main__":
    # Create necessary files if they don't exist
    if not os.path.exists('ai_prompt.txt'):
        print("Creating AI prompt file...")
        create_ai_prompt_file()
    
    required_files = ["finance.txt", "marketing.txt", "IT.txt"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("Creating sample department files...")
        create_sample_department_files()
    
    # Check if Ollama is running and model is available
    try:
        models = ollama.list()
        model_names = [model['name'] for model in models['models']]
        if 'llama3.1:8b' not in model_names:
            print("Error: llama3.1:8b model not found.")
            print("Please pull the model with: ollama pull llama3.1:8b")
            exit(1)
        print("Ollama and llama3.1:8b model are ready!")
    except Exception as e:
        print("Error: Could not connect to Ollama.")
        print("Make sure Ollama is running. You can start it with: ollama serve")
        print(f"Detailed error: {e}")
        exit(1)
    
    main()