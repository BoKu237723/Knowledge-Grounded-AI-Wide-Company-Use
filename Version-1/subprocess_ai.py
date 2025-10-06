import os
import subprocess

# not working, some OS errors

class DepartmentAI:
    def __init__(self):
        self.departments = ["finance", "marketing", "IT"]
        self.department_files = {
            "finance": "finance.txt",
            "marketing": "marketing.txt", 
            "IT": "IT.txt"
        }
        
    def load_department_data(self, department: str):
        """Load the content of a department's text file"""
        filename = self.department_files.get(department)
        if not filename or not os.path.exists(filename):
            return None
            
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return None
    
    def query_ollama(self, department: str, question: str) -> str:
        """Query Ollama with department context and question"""
        
        # Load department data
        department_data = self.load_department_data(department)
        if not department_data:
            return f"Error: Could not load data for {department} department."
        
        # Create the prompt with context
        prompt = f"""You are an AI assistant for a company. You have access to department reports and data.

CONTEXT FROM {department.upper()} DEPARTMENT:
{department_data}

QUESTION: {question}

Please provide a helpful and accurate answer based on the department data above. If the information isn't available in the context, say so clearly."""

        try:
            # Prepare the Ollama command
            cmd = [
                "ollama", "run", "llama3.1:8b",
                prompt
            ]
            
            # Run Ollama and capture output
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error running Ollama: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Error: Ollama query timed out."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_available_departments(self) -> list:
        """Return list of available departments"""
        available = []
        for dept in self.departments:
            if os.path.exists(self.department_files[dept]):
                available.append(dept)
        return available

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
    # Check if required files exist
    required_files = ["finance.txt", "marketing.txt", "IT.txt"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("Warning: The following department files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPlease make sure all department files are in the same folder as this script.")
    
    # Check if Ollama is installed and model is available
    try:
        subprocess.run(["ollama", "list"], capture_output=True, check=True)
        print("Ollama is available.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Ollama is not installed or not in PATH.")
        print("Please install Ollama from: https://ollama.ai/")
        print("And pull the model with: ollama pull llama3.1:8b")
        exit(1)
    
    main()