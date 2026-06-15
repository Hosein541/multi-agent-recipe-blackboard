import os
from typing import List, Annotated, TypedDict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
# For pretty printing
from rich.console import Console
from rich.markdown import Markdown

# LangGraph components
from langgraph.graph import StateGraph, END
# from langchain_tavily import TavilySearch
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI


console = Console()

from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
# فرض بر اینه که llm و search_tool و console قبلاً تعریف شدن

# ====================== BLACKBOARD STATE ======================
class BlackboardState(TypedDict):
    user_request: dict           # ورودی ساختاریافته کاربر (به جای str)
    blackboard: List[str]        # تمام گزارش‌های agentها
    available_agents: List[str]
    next_agent: Optional[str]


# ====================== CONTROLLER DECISION ======================
class ControllerDecision(BaseModel):
    next_agent: str = Field(
        description="The name of the next agent to call. Must be one of : ['Inventory Agent', 'Nutrition Agent', 'Taste Agent', 'Creativity Agent', 'Recipe Generator', 'Critic Agent', 'FINISH']"
    )
    reasoning: str = Field(description="A brief reason for choosing the next agent.")


# ====================== SPECIALIST AGENT FACTORY (اصلاح شده) ======================
def create_blackboard_specialist(persona: str, agent_name: str, llm, search_tool):
    system_prompt = f"""You are an expert {persona}.
Your job is to contribute specifically and concisely to the meal planning goal.
Read the User Request and the current Blackboard carefully.
Provide a useful, structured markdown report.
Always sign your report with: **Report from {agent_name}**

Be proactive and add value even if information is limited."""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """User Request:
{user_request}

Current Blackboard:
{blackboard_str}
""")
    ])

    # بدون bind_tools برای شروع (بعداً اگر نیاز شد اضافه می‌کنیم)
    agent = prompt_template | llm.bind_tools([search_tool])

    def specialist_node(state: BlackboardState):
        console.print(f"--- [Blackboard] AGENT '{agent_name}' Is Activated ---")
        
        # فرمت کردن تمیز user_request
        if isinstance(state["user_request"], dict):
            user_req_str = "\n".join([f"- {k}: {v}" for k, v in state["user_request"].items()])
        else:
            user_req_str = str(state["user_request"])

        blackboard_str = "\n\n---\n\n".join(state["blackboard"]) if state["blackboard"] else "The blackboard is still empty."

        try:
            result = agent.invoke({
                "user_request": user_req_str,
                "blackboard_str": blackboard_str
            })

            print(f"result\t\t:{result}")
            
            # هندل کردن خروجی بهتر
            if hasattr(result, 'content'):
                content = result.content[0]["text"]
            else:
                content = str(result)
                
            report = f"**Report from {agent_name}:**\n{content.strip()}"
            
        except Exception as e:
            report = f"**Report from {agent_name}:**\nError while Proccessing: {str(e)}"

        console.print(f"✅ {agent_name} is reported.")
        return {"blackboard": state["blackboard"] + [report]}

    return specialist_node

# ====================== CONTROLLER NODE ======================
def create_controller_node(llm):

    def controller_node(state: BlackboardState):
        console.print("--- CONTROLLER: Analysing the Blackboard... ---")

        controller_llm = llm.with_structured_output(ControllerDecision)

        blackboard_content = "\n\n".join(state['blackboard']) if state['blackboard'] else "Blackboard is Empty."
        console.print(blackboard_content)
        prompt = f"""You are the Controller of a Blackboard Architecture for intelligent meal planning.

        **User Request:**
        {state['user_request']}

        **Current Blackboard Content:**
        ---
        {blackboard_content}
        ---

        **Available Agents:**
        {', '.join(state['available_agents'])}

        **Rules:**
        - Always start with Inventory Agent if ingredients are provided.
        - Then check Nutrition and constraints.
        - Use Creativity Agent if there are missing ingredients.
        - Generate recipe only when foundations are solid.
        - Use Critic Agent near the end to evaluate quality.
        - Only choose FINISH after Critic Agent has reviewed and the solution is good.

        Decide the single best next step."""

        decision_result = controller_llm.invoke(prompt)

        console.print(f"--- CONTROLLER: Decision = '{decision_result.next_agent}' | Reason: {decision_result.reasoning} ---")

        return {"next_agent": decision_result.next_agent}
    return controller_node


# ====================== ساخت گراف ======================
def build_blackboard_graph(llm, search_tool):
    bb_graph_builder = StateGraph(BlackboardState)

 
    # ====================== ایجاد agentها ======================
    inventory_agent = create_blackboard_specialist(
        "Inventory Analyst who checks available ingredients and identifies shortages", 
        "Inventory Agent", llm, search_tool
    )

    nutrition_agent = create_blackboard_specialist(
        "Nutrition Expert who ensures dietary balance, constraints and health goals", 
        "Nutrition Agent", llm, search_tool
    )

    taste_agent = create_blackboard_specialist(
        "Culinary Taste & Cultural Expert specialized in international cuisine", 
        "Taste Agent", llm, search_tool
    )

    creativity_agent = create_blackboard_specialist(
        "Creative Substitution & Innovation Agent who suggests alternatives and creative twists", 
        "Creativity Agent", llm, search_tool
    )

    recipe_generator = create_blackboard_specialist(
        "Professional Recipe Generator who creates complete step-by-step recipes", 
        "Recipe Generator", llm, search_tool
    )

    critic_agent = create_blackboard_specialist(
        "Critical Reviewer who evaluates recipes for feasibility, consistency, taste balance and improvements", 
        "Critic Agent", llm, search_tool
    )
    controller_node = create_controller_node(llm)
    # اضافه کردن نودها
    bb_graph_builder.add_node("Controller", controller_node)
    bb_graph_builder.add_node("Inventory Agent", inventory_agent)
    bb_graph_builder.add_node("Nutrition Agent", nutrition_agent)
    bb_graph_builder.add_node("Taste Agent", taste_agent)
    bb_graph_builder.add_node("Creativity Agent", creativity_agent)
    bb_graph_builder.add_node("Recipe Generator", recipe_generator)
    bb_graph_builder.add_node("Critic Agent", critic_agent)
    
    bb_graph_builder.set_entry_point("Controller")
    
    # Routing
    def route_to_agent(state: BlackboardState):
        return state["next_agent"]
    
    available_agents = [
        "Inventory Agent", "Nutrition Agent", "Taste Agent",
        "Creativity Agent", "Recipe Generator", "Critic Agent", "FINISH"
    ]
    
    bb_graph_builder.add_conditional_edges(
        "Controller",
        route_to_agent,
        {
            "Inventory Agent": "Inventory Agent",
            "Nutrition Agent": "Nutrition Agent",
            "Taste Agent": "Taste Agent",
            "Creativity Agent": "Creativity Agent",
            "Recipe Generator": "Recipe Generator",
            "Critic Agent": "Critic Agent",
            "FINISH": END
        }
    )
    # بعد از هر agent برمی‌گردد به Controller
    for agent in ["Inventory Agent", "Nutrition Agent", "Taste Agent", 
                  "Creativity Agent", "Recipe Generator", "Critic Agent"]:
        bb_graph_builder.add_edge(agent, "Controller")
    
    return bb_graph_builder.compile(), available_agents