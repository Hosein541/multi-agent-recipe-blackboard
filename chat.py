import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate


class ChatIntent(BaseModel):
    intent: str = Field(
        description="""Choose one of the following intents:
        - update_profile: When user wants to change the  information
        - ask_explanation: When user asks for explanation about current recipe 
        - general_question: For casual conversation or other questions"""
    )
    key: Optional[str] = Field(
        description="Only used when intent is 'update_profile'. Valid keys: 'ingredients', 'people', 'time available', 'constraints', 'extra info', 'goal'",
        examples=["people", "extra info"]
    )
    value: Optional[Any] = Field(
        description="Only used when intent is 'update_profile'. The new value for the specified key."
    )

def handle_chat_message(
    user_message: str,
    current_state: Dict,
    finance_advisor,      # compiled LangGraph
    llm,

) -> tuple:
    

    prompt = ChatPromptTemplate.from_template(
    """You are an intelligent intent classifier for a AI Recipe Generator.

    Your job is to analyze the user's message and return the correct intent with high accuracy.

    ### Available Intents and When to Use Them:

    1. **update_profile** → Use when user wants to change their  information.
       - Examples: "my new goal is to eat healthy Quick & Easy", "set people to 5", "change time available to 1:30 hour", "constraints: No red meat"

    2. **ask_explanation** → Use when user asks why, how, or explanation about current recipe.
       - Examples: "why did you choose this recipe?", "explain more about your decision", "what does this mean?"

    3. **general_question** → Use for everything else (casual talk, greetings, general palnning questions).


    User Message: {message}

    Respond with the correct structured intent.
    """
    )
    chain = prompt | llm.with_structured_output(ChatIntent)
    intent = chain.invoke({"message": user_message})

    response = ""
    output_type = False
    print(f"intent:\t\t\t{intent.intent}")
    print(f"intent key:\t\t\t{intent.key}")
    print(f"intent value:\t\t\t{intent.value}\t\t{type(intent.value)}")

    if intent.intent == "update_profile" and intent.key:
        intent.key = intent.key.replace(" ", "_")
        if intent.key in current_state["user_request"]:
            old = current_state["user_request"][intent.key]
            if type(old) == int:
                current_state["user_request"][intent.key] = int(intent.value)
            else :
                current_state["user_request"][intent.key] = intent.value
            response = f"✅ Updated **{intent.key}** from {old} → {intent.value}\n"
            
            # Auto Re-run
            response += "🔄 Re-running full analysis with updated profile..."
            response += "\nYou can continue chatting or request further changes."

            current_state = rerun_full_analysis(current_state, finance_advisor)
            output_type = True
        else:
            response = f"❌ Unknown input field: {intent.key}"

    elif intent.intent == "ask_explanation":
        response = explain_current_recommendation(current_state, llm, user_message)
        output_type = False

    else:
        # General chat
        general_prompt = ChatPromptTemplate.from_template(
            "You are a professional and friendly Personal recipe generator. Answer the user naturally.\n\nUser: {message}"
        )
        response = (general_prompt | llm).invoke({"message": user_message}).content[0]["text"]
        output_type = False
    
    print(f"output type:\t\t\t{output_type}")
    return response, current_state, output_type


def rerun_full_analysis(state: Dict, finance_advisor):
    """Re-run the entire advisor graph"""
    # Reset temporary fields
    state["blackboard"] = ["hi"]
    
    result = finance_advisor.invoke(state)
    return result


def explain_current_recommendation(state: Dict, llm, question: str):
    prompt = ChatPromptTemplate.from_template(
        """Explain based on current Plan.

        User Question: {question}
        Current Plan: {rec}
        """
    )
    chain = prompt | llm
    return chain.invoke({
        "question": question,
        "rec": json.dumps(state.get("blackboard", {}), indent=2)
    }).content[0]["text"]