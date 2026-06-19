import re
import time
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from board import build_blackboard_graph
from chat import handle_chat_message

st.set_page_config(page_title="Blackboard Chef", layout="wide")
st.title("🍳 Blackboard Chef")
st.markdown("**Blackboard Architecture + LangGraph**")


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
    
    people = st.number_input("Number of People", min_value=1, value=4, max_value=15)
    constraints = st.multiselect("Dietary Constraints", 
                                 ["vegan", "vegetarian", "keto", "gluten-free", "dairy-free", "high-protein", 
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
            model="gemini-3.1-flash-lite",   
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
        "time_available": time_available,
        "goal": goal,
        "extra_info": extra_info
    }

    initial_state = {
        "user_request": user_input,
        "blackboard": [],
        "available_agents": st.session_state.available_agents,
        "next_agent": None
    }


    with blackboard_container:
        st.subheader("📋 Blackboard Progress")
        bb_expander = st.expander("Show Full Blackboard", expanded=True)
        bb_placeholder = bb_expander.empty()   # correct

    state = initial_state.copy()
    try:
        for _ in range(25):
            output = st.session_state.blackboard_app.invoke(state)
            state = output
            st.session_state.current_state = state

            # Build the blackboard display
            reports = state.get("blackboard", [])
            with recipe_report:

                reports_text = "\n\n---\n\n".join(reports)
                recipe = extract_between(reports_text, "Report from Recipe Generator", "Report from Recipe Generator")
                if recipe:
                    st.markdown(recipe)
                    st.session_state.final_text = recipe
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

        # Final Result
        with final_recipe_placeholder:
            st.success("✅ Final Recipe Ready!")
            st.subheader("🍽 Final Recipe")

            final_text = "\n\n".join(state.get("blackboard", [])[-4:])  # last few reports
            # st.markdown(final_text)

            # Download Button
            st.download_button(
                label="📥 Download Recipe",
                data=final_text,
                file_name="blackboard_chef_recipe.md",
                mime="text/markdown"
            )

        st.session_state.planner_ready = True
        st.session_state.counter = 0

    except Exception as e:
        st.error(f"Error: {str(e)}")

if st.session_state.get("planner_ready", False):
    if st.session_state.counter > 0:

        st.markdown(st.session_state.final_text)

        st.download_button(
            label="📥 Download Recipe",
            data=st.session_state.final_text,
            key=15,
            file_name="blackboard_chef_recipe.md",
            mime="text/markdown"
        )

    st.session_state.counter +=1
    st.subheader("💬 Chat with Your Recipe Generator Advisor")

    #chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            st.markdown(msg.get("agent_output", ""))

    # recieve user question
    question = st.chat_input("Ask something about your plan...")

    if question:
        # add user message to the chat history
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, state, output_type = handle_chat_message(
                    user_message=question,   # ← اصلاح مهم
                    current_state=st.session_state.current_state,
                    finance_advisor=st.session_state.blackboard_app,
                    llm=st.session_state.llm,
                )
                st.session_state.current_state = state
                st.markdown(response)

                if output_type:
                    st.subheader("📌 Final Recipe")
                    final_output_text = "\n\n".join(state.get("blackboard", [])[-4:])

                    recipe = extract_between(final_output_text, "Report from Recipe Generator", "Report from Recipe Generator")
                    
                    st.markdown(recipe)
                    # save file and download button
                    final_text = "# Blackboard Chef - Full Report\n\n" + final_output_text

                    st.download_button(
                        label="📥 Download Plan",
                        key=2,
                        data=final_text,
                        file_name="blackboard_chef_recipe.md",
                        mime="text/markdown"
                    )
        if output_type:
            st.session_state.chat_history.append({"role": "assistant", "content": response, "agent_output":final_output_text})
        else : 
            st.session_state.chat_history.append({"role": "assistant", "content": response})

else:
    st.info("Please enter your API keys and meal information to start.")