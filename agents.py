import google.generativeai as genai

class BaseAgent:
    def __init__(self, model, name, persona):
        self.model = model
        self.name = name
        self.persona = persona

    def work(self, input_data):
        print(f"{self.name} is thinking..")
        
        # --- SAFETY FEATURE: CONTEXT TRUNCATION GUARD ---
        # If the input is massive (e.g., a huge repo), we cut it to a safe, fast size.
        # 800,000 characters is roughly 200,000 tokens, which is fast and reliable.
        MAX_CHARS = 800000 
        if len(input_data) > MAX_CHARS:
            print(f"Warning: Input context length is {len(input_data)} chars. Truncating to {MAX_CHARS}...")
            input_data = input_data[:MAX_CHARS] + "\n...[CONTEXT TRUNCATED DUE TO SIZE]..."
        # --------------------------------------------------
        
        prompt = f"""
        SYSTEM_IDENTITY:
        {self.persona}

        INPUT_DATA :
        { input_data}
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            # Added better error handling feedback
            print(f"ERROR!! Agent failed to generate content: {e}")
            return f"Error: Agent '{self.name}' failed to process data. Reason: {e}"
    
# Code Analyzing Agent
class AnalystAgent(BaseAgent):
    def __init__(self, model):
        super().__init__(model, "Analyst","""
            You are a Senior Code Analyst. Your job is NOT to write documentation, but to READ raw code and extract facts.
            Output a structured summary containing:
            1. List of all languages used.
            2. The probable entry point of the app (eg., main.py, index.js).
            3. A list of external libraries/dependencies imported.
            4. A high level description of the data flow.              
            
            Be concise and factual.
            """)
        
# Code reviewing agent(Tech lead)
class TechLeadAgent(BaseAgent):
    def __init__(self, model):
        super().__init__(model, "Tech Lead","""
            You are a cynical Technical Lead. You are reviewing a codebase analysis.

            Identify 3 potential "red flags" or areas of concern, such as:
            Security risks(hardcodes keys).
            Deprecated libraries.
            Lack of error handling.
            Poor variable naming.
            
            If the code looks perfect admit it, but try to find improvements
             """ )

# technical writing agent
class WriterAgent(BaseAgent):
    def __init__(self, model):
        super().__init__(model, "Writer","""
            You are a Technical Writer specializing in documentation for legacy systems.
            
            You will receive:
            1. a code analysis.
            2. A tech Leads critique.
            
            Your goal: Write a professtional README.md file.
            Structure: 
            #[Project Name]
            ## Overview
            ## Tech stack
            ## Key Features
            ## Maintainace Warning(Include the tech leads red flags here)
            ## Getting started
            """)
        
class DiagramAgent(BaseAgent):
    def __init__(self, model):
        super().__init__(model, "Architect", """
            You are a Senior Software Architect. 
            Your goal is to map the dependencies of a legacy codebase using Mermaid.js.
            
            STRICT RULES:
            1. Use ONLY the actual filenames found in the codebase. DO NOT invent files like "AI_Pipeline" or "Core" if they don't exist.
            2. If 'app.py' imports 'agents.py', draw: app.py --> agents.py
            3. Use the 'graph TD' layout.
            4. Style the nodes:
                - Use [Square Brackets] for Python/Code files.
                - Use (Round Brackets) for External Libraries (like streamlit, google-genai).
                
            Output ONLY the Mermaid code. No markdown backticks.
        """)