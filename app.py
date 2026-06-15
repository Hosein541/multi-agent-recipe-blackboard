import streamlit as st
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from board import build_blackboard_graph

st.set_page_config(page_title="Blackboard Chef", layout="wide")
st.title("🍳 Blackboard Chef")
st.markdown("**Blackboard Architecture + LangGraph**")
import re

def extract_between(text, start_phrase, end_phrase=None, include_phrases=True):
    """
    Extract text located between start_phrase and end_phrase.
    
    Args:
        text (str): The full text.
        start_phrase (str): The starting delimiter.
        end_phrase (str, optional): The ending delimiter. If None, extract from start to end of text.
        include_phrases (bool): If True, include the delimiters in the result.
    
    Returns:
        str: Extracted section, or empty string if start not found.
    """
    # Escape regex special characters in phrases
    start_esc = re.escape(start_phrase)
    if end_phrase:
        end_esc = re.escape(end_phrase)
        pattern = f"({start_esc})(.*?)({end_esc})" if include_phrases else f"{start_esc}(.*?){end_esc}"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            if include_phrases:
                return match.group(0)  # full match including delimiters
            else:
                return match.group(1).strip()  # content only
    else:
        # No end phrase: extract from start to the end
        start_idx = text.find(start_phrase)
        if start_idx == -1:
            return ""
        if include_phrases:
            return text[start_idx:]
        else:
            return text[start_idx + len(start_phrase):].strip()
    
    return ""
# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("Settings")
    gemini_key = st.text_input("Gemini API Key", type="password")
    tavily_key = st.text_input("Tavily Search API Key", type="password")

    st.header("Meal Information")
    ingredients = st.text_area("Available Ingredients (one per line)", 
                               placeholder="chicken\n tomato\n onion\n rice")
    
    people = st.number_input("Number of People", min_value=1, value=4)
    constraints = st.multiselect("Dietary Constraints", 
                                 ["vegan", "vegetarian", "keto", "gluten-free", "dairy-free", 
                                  "no red meat", "nut allergy", "Iranian traditional", "Indian traditional", "Italian traditional", "Japanese traditional"])
    
    time_available = st.selectbox("Available Cooking Time", 
                                  ["15 minutes", "30 minutes", "45 minutes", "1 hour", "More than 1 hour"])
    
    goal = st.selectbox("Goal", 
                        ["Quick & Easy", "Healthy & Diet", "Delicious Traditional", 
                         "Cheap & Economic", "Party & Special", "Keto / Low Carb"])
    
    extra_info = st.text_area("Extra Information (optional)", 
                              placeholder="No onion, make it spicy, we have guests...")

    start_button = st.button("🚀 Start Planning", type="primary", use_container_width=True)

# ====================== MAIN AREA ======================
recipe_report = st.container()
status_placeholder = st.empty()
blackboard_container = st.container()
final_recipe_placeholder = st.empty()

if start_button and gemini_key and tavily_key:
    # Create LLM and Tool
    if "llm" not in st.session_state:
        st.session_state.llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",   # Changed to more stable model
            google_api_key=gemini_key,
            temperature=0.5 ,
        )
        st.session_state.search_tool = TavilySearchResults(max_results=2, tavily_api_key=tavily_key)

    # Build Graph
    if "blackboard_app" not in st.session_state:
        with st.spinner("Building Blackboard Graph..."):
            app, agents = build_blackboard_graph(st.session_state.llm, st.session_state.search_tool)
            st.session_state.blackboard_app = app
            st.session_state.available_agents = agents

    # Prepare input
    user_input = {
        "ingredients": [item.strip() for item in ingredients.split("\n") if item.strip()],
        "people": int(people),
        "constraints": constraints,
        "time": time_available,
        "goal": goal,
        "extra_info": extra_info
    }

    initial_state = {
        "user_request": user_input,
        "blackboard": [],
        "available_agents": st.session_state.available_agents,
        "next_agent": None
    }

    # # Run the graph
    # with blackboard_container:
    #     st.subheader("📋 Blackboard Progress (Live)")
    #     bb_expander = st.expander("Show Full Blackboard", expanded=True)
    #     bb_placeholder = bb_expander.empty()

    # state = initial_state.copy()

    # try:
    #     for _ in range(25):   # safety limit
    #         output = st.session_state.blackboard_app.invoke(state)
    #         state = output

    #         # Live update
    #         with bb_placeholder:
    #             for report in state.get("blackboard", []):
    #                 print(f"live update report:\t\t\t{report}")
    #                 st.markdown(report)
    #                 st.divider()

    #         if state.get("next_agent") == "FINISH":
    #             break

    #         time.sleep(0.7)

    with blackboard_container:
        st.subheader("📋 Blackboard Progress")
        bb_expander = st.expander("Show Full Blackboard", expanded=True)
        bb_placeholder = bb_expander.empty()   # correct

    state = initial_state.copy()
    try:
        for _ in range(25):
            output = st.session_state.blackboard_app.invoke(state)
            state = output

            # Build the blackboard display
            reports = state.get("blackboard", [])
            # if "Report from Recipe Generator" in reports:
            with recipe_report:

                reports_text = "\n\n---\n\n".join(reports)
                # st.info(type(reports))
                recipe = extract_between(reports_text, "Report from Recipe Generator", "Report from Recipe Generator")
                if recipe:
                    st.markdown(recipe)
                else :
                    st.info("No report found starting with '**Report from Recipe Generator**'.")
            st.divider()

            if reports:
                display_text = "\n\n---\n\n".join(reports)
                bb_placeholder.markdown(display_text)
            else:
                bb_placeholder.markdown("*Waiting for blackboard updates...*")

            if state.get("next_agent") == "FINISH":
                break
            time.sleep(0.7)
    # except Exception as e:
    #     st.error(f"Error: {e}")

        # Final Result
        with final_recipe_placeholder:
            st.success("✅ Final Recipe Ready!")
            st.subheader("🍽 Final Recipe")

            final_text = "\n\n".join(state.get("blackboard", [])[-4:])  # last few reports
            st.markdown(final_text)

            # Download Button (Fixed)
            st.download_button(
                label="📥 Download Recipe",
                data=final_text,
                file_name="blackboard_chef_recipe.md",
                mime="text/markdown"
            )

    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("Please enter your API keys and meal information to start.")