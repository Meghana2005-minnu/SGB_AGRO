import json
import streamlit as st
import requests
import re

# Page configuration
st.set_page_config(page_title="SGB Agro AI Sales Agent", page_icon="🚜", layout="centered")

st.title("🚜 SGB Agro Industries - AI Sales Assistant")
st.markdown("*Independent Hackathon Prototype | Text-Based Sales Agent*")

# Load Catalogue
@st.cache_data
def load_catalogue():
    try:
        with open("catalogue.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

catalogue = load_catalogue()

# Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": f"""You are an expert AI Sales Agent for SGB Agro Industries Pvt Ltd. 
Here is your official product catalogue: {json.dumps(catalogue)}

CRITICAL RULES:
1. NEVER pitch a product immediately. Always start by welcoming the customer and asking 2 to 3 essential requirement discovery questions (e.g., What crop are they growing? What is their farm size?).
2. Ground all explanations, prices, shipping details, and limitations strictly in the catalogue above.
3. If a customer asks about something not in the catalogue, acknowledge that you don't have it rather than inventing it.
4. When the customer gives explicit purchase intent (e.g. 'I want to buy this', 'Proceed with order'), guide them to provide your Name, Phone Number, and Delivery Location (in Karnataka). Once provided, acknowledge the order confirmation clearly."""
        },
        {
            "role": "assistant",
            "content": "Hello! Welcome to SGB Agro Industries. I'm your virtual sales assistant. To help me recommend the right equipment for your farm today, could you tell me a bit about what crop you are cultivating and your approximate farm size?"
        }
    ]

# Session state for mock order tracking
if "mock_order" not in st.session_state:
    st.session_state.mock_order = None

# Display prior chat messages (skip system prompt)
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Box
if user_prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Generate Response from Local Ollama Instance
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                payload = {
                    "model": "llama3.2",
                    "messages": st.session_state.messages,
                    "stream": False
                }
                response = requests.post("http://localhost:11434/api/chat", json=payload)
                result = response.json()
                bot_reply = result["message"]["content"]
            except Exception as e:
                bot_reply = f"Error connecting to local Ollama server. Make sure Ollama is running! Details: {e}"
            
            st.markdown(bot_reply)
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})

            # Simple logic to capture mock order if confirmation/details are present
            full_chat_text = " ".join([m["content"] for m in st.session_state.messages])
            if "order" in full_chat_text.lower() or "buy" in full_chat_text.lower() or "proceed" in full_chat_text.lower():
                # Generate mock order data structure for the sidebar
                st.session_state.mock_order = {
                    "status": "PENDING_CONFIRMATION",
                    "payment_status": "NOT_APPLICABLE_MOCK",
                    "company": "SGB Agro Industries Pvt Ltd",
                    "catalogue_items_referenced": [item["name"] for item in catalogue if item["name"].lower() in full_chat_text.lower()],
                    -1: "Review chat log for extracted customer details & delivery location."
                }

# Sidebar for Mock Order & Status
with st.sidebar:
    st.header("📊 Lead & Order Status")
    st.markdown(f"**Loaded Products:** {len(catalogue)} items across categories")
    st.markdown("**Shipping Hub:** Karnataka Region")
    st.markdown("---")
    st.subheader("Mock Order Receipt (JSON)")
    
    if st.session_state.messages:
        # Pull the last assistant response or check for order info
        latest_history = st.session_state.messages[-1]["content"]
        
        # Display formatted JSON receipt card
        order_receipt = {
            "order_ref": "SGB-MOCK-2026-001",
            "merchant": "SGB Agro Industries Pvt Ltd",
            "currency": "INR",
            "payment_terms": "Pending / Offline Verification",
            "last_agent_status": latest_history[:100] + "..." if len(latest_history) > 100 else latest_history
        }
        st.json(order_receipt)
    else:
        st.info("No active order sequence started yet.")
    
    if st.button("Clear Conversation & Reset"):
        st.session_state.clear()
        st.rerun()