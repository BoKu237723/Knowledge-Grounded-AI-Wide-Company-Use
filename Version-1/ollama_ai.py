import ollama

class DepartmentAI:
    def __init__(self):
        self.departments = ['finance','marketing','IT']
        self.department_files = {
            'finance' : 'finance.txt',
            'marketing' : 'marketing.txt',
            'IT' : 'IT.txt',
        }

    def load_department_data(self, department):
        filename = self.department_files.get(department)
        if not filename:
            return f"Cound not find data file for {department} department"
        
        try:
            with open(filename,'r',encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error in loading {filename} department data: {e}"
    
    def load_ai_prompt(self, department):
        try:
            with open('ai_prompt.txt','r',encoding='utf-8') as f:
                prompt_template = f.read()
            
            department_data = self.load_department_data(department)
            prompt_template = prompt_template.replace('{departments}',', '.join(self.departments))
            prompt_template = prompt_template.replace('{department}',department.upper())
            prompt_template = prompt_template.replace('{department_data}',department_data)

            return prompt_template
        except Exception as e:
            return f"Error in loading AI prompt: {e}"
    
    def query_ollama(self, department, question):
        system_prompt = self.load_ai_prompt(department)
        if not system_prompt:
            return "Error: Could not load AI prompt template"
        try:
            response = ollama.chat(model='llama3.1:8b', messages=[
                {
                    'role' : 'system',
                    'content' : system_prompt
                },
                {
                    'role' : 'user',
                    'content' : question
                }
            ])
            return response['message'] ['content']
        except Exception as e:
            return f"Error in query_ollama: {e}"
    
    def get_available_departments(self):
        available = []
        for department in self.departments:
            try:
                with open(self.department_files[department],'r',encoding='utf-8') as f:
                    available.append(department)
            except Exception as e:
                print(f"Null in getting available departments: {e}")
                continue
        return available
    
def main():
    ai = DepartmentAI()
    print("=== Company Department AI Assistant ===")
    print("Available Departments: ",", ".join(ai.get_available_departments()))
    print("Type 'quit' to exit\n")

    while True:
        department = input("Which department do you want to ask about?\nYou: ").lower()
        if department == 'quit':
            break
        if department not in ai.departments:
            print("Invalid department, Could not find in department List")
            continue

        question = input(f"What is your question for the {department} department?\nYou: ")

        if question.lower() == 'quit':
            break

        print("\nThinking...")
        answer = ai.query_ollama(department, question)
        print(f"\n=== {department.upper()} DEPARTMENT ANSWER ===")
        print(answer)
        print("=" *50 + "\n")
    
if __name__ == "__main__":
    main()