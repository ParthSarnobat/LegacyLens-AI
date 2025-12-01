import streamlit as st
import os
import time
import base64
import google.generativeai as genai
from dotenv import load_dotenv
from ingest_code import get_codebase_context
from agents import AnalystAgent, TechLeadAgent, WriterAgent, DiagramAgent

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="LegacyLens AI",
    page_icon="LegacyLens_icon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #6A0DAD; font-weight: 700; margin-bottom: 0;}
    .sub-header {font-size: 1.2rem; color: #666; margin-bottom: 2rem;}
    .stButton>button {width: 100%; border-radius: 5px; height: 3em; font-weight: bold;}
    .success-box {padding: 1rem; background-color: #d4edda; border-radius: 5px; color: #155724;}
</style>
""", unsafe_allow_html=True)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# --- SIDEBAR ---
with st.sidebar:

    if os.path.exists("LegacyLens_logo.png"):
        st.image("LegacyLens_logo.png", width=250)
    else:
        st.warning("⚠️ 'logo.png' not found. Please upload it to your project folder.")
    
    st.caption("AI powered code Archeologist")
    st.markdown("---")

    # Input can be a local path OR a GitHub URL
    repo_path = st.text_input("Repository Path / URL:", value="", help="Enter a local folder path OR a GitHub URL (e.g. https://github.com/user/repo)")
    
    if not api_key:
        api_key = st.text_input("Enter Google API Key:", type="password")

    st.markdown("---")

    start_btn = st.button("Analyze Codebase", type="primary")

    st.info("💡 **How it works:**\n1. Ingests raw code (Local or GitHub)\n2. AI Analyst maps the logic\n3. Tech Lead finds bugs\n4. Architect draws diagrams")

# --- MAIN APP ---

st.markdown('<div class="main-header">Legacy Code Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Transform undocumented spaghetti code into clean documentation.</div>', unsafe_allow_html=True)

if start_btn:
    if not api_key:
        st.error("Error!! Google API key is missing.")
        st.stop()
    
    genai.configure(api_key=api_key)

    # Use the Flash model for speed/cost effectiveness
    model = genai.GenerativeModel('gemini-2.5-flash') 
    st.toast("Using Gemini 2.5 Flash")
    
    # --- PHASE 1: INGESTION ---
    with st.status("Phase 1: Ingesting Source Code", expanded=True) as status:
        
        # UI Feedback: Let the user know if we are Cloning or just Scanning
        if repo_path.startswith("http"):
            st.write(f"🌍 Detected GitHub URL. Cloning `{repo_path}`...")
        else:
            st.write(f"📂 Scanning local directory: `{repo_path}`")
            
        # Call the ingestion script
        raw_code = get_codebase_context(repo_path)
        
        if not raw_code:
            status.update(label="Error: No code found!", state="error")
            st.error("❌ No code files found! Please check if the path/URL is correct and contains .py, .js, or .java files.")
            st.stop() # <--- FIXED: Added parentheses here
        
        char_count = len(raw_code)
        status.update(label=f"✅ Ingestion Complete! Read {char_count} characters.", state="complete")

    # --- PHASE 2-4: AI AGENTS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Final Documentation", "🔧 Refactoring Plan", "📊 System Diagram", "🧠 Raw Analysis"])

    progress_bar = st.progress(0)
    
    try:
        # --- AGENT 1: ANALYST ---
        with st.spinner("Phase 2: Analyst is mapping system logic..."):
            analyst = AnalystAgent(model)
            analysis_result = analyst.work(raw_code)
            progress_bar.progress(33)
            with tab4:
                st.text_area("Analyst Output", analysis_result, height=300)

        # --- AGENT 2: TECH LEAD ---
        with st.spinner("Phase 3: Tech Lead is finding red flags..."):
            tech_lead = TechLeadAgent(model)
            critique_result = tech_lead.work(f"RAW CODE:\n{raw_code}\n\nANALYSIS:\n{analysis_result}")
            progress_bar.progress(66)
            with tab2:
                st.error("### 🚩 Critical Issues Found")
                st.markdown(critique_result)

        # --- AGENT 3 & 4: WRITER & ARCHITECT ---
        with st.spinner("Phase 4: Generating Documentation & Diagrams..."):
            # Writer
            writer = WriterAgent(model)
            final_docs = writer.work(f"ANALYSIS:\n{analysis_result}\n\nCRITIQUE:\n{critique_result}")
            
            # Architect (Diagrams)
            architect = DiagramAgent(model)
            diagram_code = architect.work(f"ANALYSIS_SUMMARY:\n{analysis_result}")
            
            progress_bar.progress(100)

        # --- FINAL DISPLAY ---
        
        with tab1:
            st.markdown(final_docs)
            st.download_button("⬇️ Download README.md", final_docs, file_name="README.md")

        with tab3:
            st.markdown("### 📊 Architecture Diagram")
            try:
                # Render Mermaid Diagram
                graphbytes = diagram_code.encode("utf8")
                base64_bytes = base64.b64encode(graphbytes)
                base64_string = base64_bytes.decode("ascii")
                image_url = "https://mermaid.ink/svg/" + base64_string

                st.image(image_url, caption="Auto-Generated System Map", use_container_width=True)
                
                with st.expander("View Raw Mermaid Code"):
                        st.code(diagram_code, language="mermaid")

            except Exception as e:
                st.warning("Could not render the visual diagram. Here is the raw code:")
                st.code(diagram_code, language="mermaid")

        st.success("✅ Full Analysis Pipeline Complete!")

    except Exception as e:
        st.error(f"An error occurred during the Agent pipeline: {e}")
        st.warning("Tip: If this is a 'Quota' error, try waiting 60 seconds and running again.")