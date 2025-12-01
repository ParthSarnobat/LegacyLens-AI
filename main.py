import os
import google.generativeai as genai
from dotenv import load_dotenv
from ingest_code import get_codebase_context
from agents import AnalystAgent, TechLeadAgent, WriterAgent, DiagramAgent

# 1. Load Environment Variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
# 2. Configure Gemini (The "Brain")
genai.configure(api_key=api_key)

# We use 'gemini-2.5-pro' because it has the huge context window we need
model = genai.GenerativeModel('gemini-2.5-pro')

def run_agent_pipeline(repo_path):
    print(f"Starting analysis pipeline on: {repo_path}")

    #Ingestion
    raw_code = get_codebase_context(repo_path)
    if not raw_code:
        print("ERROR, no code found")
        return
    print(f"Ingested {len(raw_code)} chars")

    #Agents 
    analyst = AnalystAgent(model)
    analysis_result = analyst.work(raw_code)
    print("\n✅ Analyst Finished.")
    
    # 2. Tech Lead reviews the code + analysis
    # We pass the raw code AND the analysis so the lead has full context
    tech_lead = TechLeadAgent(model)
    critique_result = tech_lead.work(f"RAW CODE:\n{raw_code}\n\nANALYSIS:\n{analysis_result}")
    print("\n✅ Tech Lead Finished.")

    # 3. Writer puts it all together
    writer = WriterAgent(model)
    final_docs = writer.work(f"ANALYSIS:\n{analysis_result}\n\nCRITIQUE:\n{critique_result}")
    print("\n✅ Writer Finished.")

   # 4. (NEW) Architect draws the diagram
    architect = DiagramAgent(model)
    diagram_code = architect.work(f"ANALYSIS_SUMMARY:\n{analysis_result}")
    print("\n✅ Architect Finished.")

    # --- Stage 3: Output ---
    
    # We combine the docs and the diagram into one file
    final_output = f"{final_docs}\n\n## Architecture Diagram\n\n```mermaid\n{diagram_code}\n```"

    output_filename = "GENERATED_README.md"
    with open(output_filename, "w", encoding='utf-8') as f:
        f.write(final_output)
    
    print(f"\n🎉 Success! Documentation + Diagram saved to {output_filename}")

# def analyze_codebase(path_to_repo):
#     print(f"📂 Scanning repository at: {path_to_repo}...")
    
#     # Use your custom ingester from Step 3
#     code_context = get_codebase_context(path_to_repo)
    
#     if not code_context:
#         print("⚠️ No code found! Are you pointing to the right folder?")
#         return

#     # Calculate token count roughly (1 token ~= 4 chars) to ensure we are safe
#     estimated_tokens = len(code_context) / 4
#     print(f"📊 Ingested {len(code_context)} characters (~{int(estimated_tokens)} tokens).")
    
#     print("🤖 Agent is analyzing...")

#     # This prompt proves you are using "Context Engineering" (Category 2 requirement)
#     prompt = f"""
#     SYSTEM ROLE:
#     You are a Principal Software Architect. You are analyzing a legacy codebase to create documentation for a new hire.

#     TASK:
#     1. Identify the core programming languages used.
#     2. Explain the purpose of this application in one clear paragraph.
#     3. List the top 3 files that seem most critical to the logic.

#     CONTEXT (Source Code):
#     {code_context}
#     """

#     try:
#         response = model.generate_content(prompt)
#         print("\n" + "="*30)
#         print("✨ AGENT REPORT ✨")
#         print("="*30)
#         print(response.text)
#         print("="*30)
#     except Exception as e:
#         print(f"❌ Error communicating with Gemini: {e}")

if __name__ == "__main__":
    # Test on the current directory first
    run_agent_pipeline(".")