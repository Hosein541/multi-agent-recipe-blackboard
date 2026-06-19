# Blackboard Chef 👨‍🍳

**An intelligent multi-agent cooking and meal planning assistant** built with **Blackboard Architecture** and **LangGraph**.

This system helps users create personalized, realistic, and delicious meal plans by leveraging specialized agents that collaborate through a shared blackboard.

## Demo
[🎥 Watch Demo](https://github.com/user-attachments/assets/533f19cd-08eb-4a99-8101-4acf0a312dbe)

---

## ✨ Features

- **Blackboard Architecture**: Multiple expert agents collaborate via a shared knowledge space
- **Intelligent Controller**: Dynamically routes between agents based on current state
- **Specialized Agents**:
  - Inventory Agent
  - Nutrition & Constraint Agent
  - Taste & Cultural Expert
  - Creativity & Substitution Agent
  - Recipe Generator
  - Critic Agent
- **Interactive Chat**: Modify ingredients, constraints, or preferences and get instant re-generated recipes
- **Full Transparency**: Watch the complete reasoning process on the live blackboard
- **Report Export**: Download full cooking session with images

---

## 🛠 Tech Stack

- **Framework**: LangGraph + LangChain
- **LLM**: Google Gemini
- **UI**: Streamlit
- **Architecture**: Blackboard Pattern
- **Dependency Manager**: Poetry

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Hosein541/blackboard-chef.git
cd blackboard-chef
```

### 2. Install Dependencies
```bash
poetry install
```

### 3. Run the Application
```bash
poetry run streamlit run app.py
```

---

## Configuration

You need a **Google Gemini API Key**.


---

## Project Structure

```bash
blackboard-chef/
├── app.py           # Streamlit UI + Interactive Chat
├── board.py         # Blackboard Architecture + LangGraph
├── chat.py          # Chat intent detection and handling
├── pyproject.toml
├── poetry.lock
└── README.md
```

---

## How It Works

1. User inputs available ingredients, dietary constraints, time, and goals
2. Agents collaborate on the Blackboard:
   - Inventory Agent analyzes what you have
   - Nutrition Agent ensures balance and respects constraints
   - Taste Agent suggests culturally appropriate combinations
   - Creativity Agent handles substitutions and creative twists
   - Recipe Generator creates step-by-step instructions
   - Critic Agent evaluates and improves the final recipe
3. Controller intelligently manages the flow
4. User can chat to make changes (e.g., "Make it vegetarian", "Reduce time to 30 minutes", "Make it spicier") and get updated recipes instantly

---

## Example Use Cases

- Planning dinner with limited fridge ingredients
- Creating healthy meals for specific diets (keto, vegan, gluten-free)
- Traditional Iranian or international cuisine adaptation
- Quick weeknight meals or special occasion cooking

---

## Future Improvements

- Image recognition for fridge ingredients
- Voice input/output
- Weekly meal planning
- Nutritional macro calculation
- Integration with shopping list apps

---

## License

This project is open-sourced under the **MIT License**.
