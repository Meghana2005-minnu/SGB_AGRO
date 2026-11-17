import json
import streamlit as st
import requests
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Page configuration
st.set_page_config(page_title="SGB Agro AI Sales Agent", page_icon="🚜", layout="centered")

st.title("🚜 SGB Agro Industries - AI Sales Assistant")
st.markdown("*Independent Hackathon Prototype | Text-Based Sales Agent with PDF Export*")

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
4. When the customer gives explicit purchase intent (e.g. 'I want to buy this', 'Proceed with order'), guide them to provide their Name, Phone Number, and Delivery Location (in Karnataka). Once provided, summarize the order details clearly."""
        },
        {
            "role": "assistant",
            "content": "Hello! Welcome to SGB Agro Industries. I'm your virtual sales assistant. To help me recommend the right equipment for your farm today, could you tell me a bit about what crop you are cultivating and your approximate farm size?"
        }
    ]

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

# Function to generate PDF Mock Order Receipt using ReportLab
def generate_pdf_invoice():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#2e7d32"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#666666"),
        spaceAfter=15
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor("#333333"),
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#444444"),
        spaceAfter=6
    )

    # Header details
    story.append(Paragraph("SGB AGRO INDUSTRIES PVT LTD", title_style))
    story.append(Paragraph("Simulated Sales Order Receipt (Hackathon Prototype)", subtitle_style))
    story.append(Spacer(1, 10))

    # Order Meta Table
    meta_data = [
        [Paragraph("<b>Order Ref:</b> SGB-MOCK-2026-001", body_style), Paragraph("<b>Date:</b> Live Session", body_style)],
        [Paragraph("<b>Status:</b> Pending Verification", body_style), Paragraph("<b>Payment:</b> Not Applicable (Mock)", body_style)]
    ]
    t_meta = Table(meta_data, colWidths=[250, 250])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f8e9")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))

    # Extracted Summary from Chat
    story.append(Paragraph("Conversation & Transaction Summary", heading_style))
    full_chat_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages[1:]])
    
    # We can truncate or pull summary block
    summary_paragraph = Paragraph(f"<i>This mock order was generated dynamically from an AI sales agent session. Review conversation notes below:</i><br/><br/>{full_chat_text[-1000:]}", body_style)
    story.append(summary_paragraph)
    story.append(Spacer(1, 20))

    # Footer note
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Italic'],
        fontSize=8,
        textColor=colors.HexColor("#888888")
    )
    story.append(Paragraph("Note: This document is a simulated mock receipt generated for hackathon demonstration purposes. No real monetary transaction has occurred.", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# Sidebar for Mock Order & PDF Download
with st.sidebar:
    st.header("📊 Lead & Order Status")
    st.markdown(f"**Loaded Products:** {len(catalogue)} items")
    st.markdown("**Region Hub:** Karnataka")
    st.markdown("---")
    st.subheader("Mock Order Checkout")
    
    # Check if conversation reflects order intent
    full_text_check = " ".join([m["content"] for m in st.session_state.messages]).lower()
    if "order" in full_text_check or "buy" in full_text_check or "proceed" in full_text_check:
        st.success("Purchase intent captured in chat stream!")
        
        pdf_file = generate_pdf_invoice()
        st.download_button(
            label="📄 Download Mock Order PDF",
            data=pdf_file,
            file_name="SGB_Mock_Order_Receipt.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Complete requirement discovery and confirm purchase in chat to unlock the PDF download.")
    
    if st.button("Clear Conversation & Reset"):
        st.session_state.clear()
        st.rerun()