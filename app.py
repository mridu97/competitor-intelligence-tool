import streamlit as st
import anthropic
import requests
import os

st.set_page_config(page_title="Competitor Intelligence Tool", page_icon="🔍", layout="centered")

st.markdown("""
<style>
    .main { background-color: #f0f4ff; }
    .block-container { max-width: 750px; padding-top: 2rem; }
    .badge {
        background: #fef3c7; color: #d97706; font-size: 12px; font-weight: 600;
        padding: 4px 12px; border-radius: 20px; display: inline-block; margin-bottom: 8px;
    }
    h1 { color: #1a1a2e; font-size: 28px; }
    .subtitle { color: #6b7280; font-size: 15px; margin-bottom: 24px; }
    .section-card {
        background: #fffbeb; border: 1.5px solid #fde68a; border-radius: 10px;
        padding: 16px 20px; margin-bottom: 14px;
    }
    .section-title { color: #d97706; font-weight: 700; font-size: 15px; margin-bottom: 6px; border-bottom: 1.5px solid #fde68a; padding-bottom: 4px; }
    .stButton>button {
        background-color: #d97706; color: white; border: none;
        padding: 12px 28px; border-radius: 8px; font-size: 15px; font-weight: 600; width: 100%;
    }
    .stButton>button:hover { background-color: #b45309; }
    .stTextInput>div>input, .stTextArea>div>textarea {
        border: 1.5px solid #e5e7eb; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="badge">COMPETITIVE INTEL</div>', unsafe_allow_html=True)
st.markdown("# Competitor Intelligence Tool")
st.markdown('<p class="subtitle">Scrape your competitors\' websites and get an AI-powered positioning brief instantly.</p>', unsafe_allow_html=True)

# API Keys
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Input: Your product
your_product = st.text_area("Your Product / Company", placeholder="e.g. AI-powered onboarding platform for HR teams at mid-size SaaS companies", height=80)

# Competitor inputs
st.markdown("**Competitors (Name + Website)**")

if "num_competitors" not in st.session_state:
    st.session_state.num_competitors = 1

competitors = []
for i in range(st.session_state.num_competitors):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input(f"Competitor name", placeholder="e.g. Freshworks", key=f"name_{i}", label_visibility="collapsed" if i > 0 else "visible")
    with col2:
        url = st.text_input(f"Website URL", placeholder="e.g. https://freshworks.com", key=f"url_{i}", label_visibility="collapsed" if i > 0 else "visible")
    if name and url:
        competitors.append({"name": name, "url": url})

st.caption(f"{st.session_state.num_competitors} competitor{'s' if st.session_state.num_competitors > 1 else ''} added")

if st.button("+ Add Competitor", key="add_btn"):
    st.session_state.num_competitors += 1
    st.rerun()

st.markdown("---")

def scrape_url(url):
    try:
        response = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
            json={"url": url, "formats": ["markdown"]},
            timeout=15
        )
        data = response.json()
        return data.get("data", {}).get("markdown", "")
    except:
        return ""

def analyze_competitors(competitors_data, your_product):
    combined = ""
    for name, content in competitors_data.items():
        combined += f"\n\n### {name}\n{content[:2000]}"

    prompt = f"""
    You are a senior competitive intelligence analyst.

    My product: {your_product}

    Here is scraped content from my competitors' websites:
    {combined}

    Write a competitive intelligence brief that includes:

    1. COMPETITOR SUMMARIES — For each competitor, write 2-3 sentences on what they do and how they position themselves

    2. KEY THEMES — What are all competitors focusing on? What words and messages keep appearing?

    3. GAPS & OPPORTUNITIES — What are competitors NOT talking about that could be an opportunity?

    4. MESSAGING RECOMMENDATIONS — Based on this landscape, how should my product differentiate its messaging?

    Be specific, use their actual language where relevant, and keep the whole brief under 500 words.
    """

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def render_brief(text):
    import re
    sections = re.split(r'\n(?=\d+\.|#{1,3} |[A-Z &]{4,}:)', text)
    if len(sections) <= 1:
        st.markdown(f'<div class="section-card"><div>{text}</div></div>', unsafe_allow_html=True)
        return
    for section in sections:
        lines = section.strip().split("\n")
        title = lines[0].strip().lstrip("#").lstrip("0123456789.").strip().rstrip(":")
        body = "\n".join(lines[1:]).strip()
        if not body:
            body = title
            title = ""
        if title:
            st.markdown(f'<div class="section-card"><div class="section-title">{title}</div><div>{body}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="section-card"><div>{body}</div></div>', unsafe_allow_html=True)

if st.button("Generate Intelligence Brief", key="analyze_btn"):
    if not competitors:
        st.warning("Please add at least one competitor with a name and URL.")
    elif not your_product:
        st.warning("Please describe your product.")
    else:
        loading_messages = [
            "Scraping competitor sites...",
            "Reading their positioning...",
            "Analyzing messaging patterns...",
            "Finding gaps and opportunities...",
            "Writing your brief..."
        ]
        with st.spinner(""):
            progress_placeholder = st.empty()
            competitors_data = {}
            for i, comp in enumerate(competitors):
                progress_placeholder.info(f"🔍 Scraping {comp['name']}...")
                scraped = scrape_url(comp["url"])
                competitors_data[comp["name"]] = scraped if scraped else "Could not scrape this website."

            progress_placeholder.info("✍️ Writing your intelligence brief...")
            brief = analyze_competitors(competitors_data, your_product)
            progress_placeholder.empty()

        st.markdown("### Intelligence Brief")
        render_brief(brief)

        st.download_button(
            label="📋 Copy / Download Brief",
            data=brief,
            file_name="competitor_intelligence_brief.txt",
            mime="text/plain"
        )
