import streamlit as st
from openai import OpenAI
import os, time, re

# --------------------
# 🔑 API Setup
# --------------------
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("🚨 OpenAI API key not found! Add it to Streamlit secrets or environment variable.")
    st.stop()

client = OpenAI(api_key=api_key)

# --------------------
# 🎨 Streamlit Config
# --------------------
st.set_page_config(page_title="AI LinkedIn Post Generator", page_icon="💼", layout="wide")

st.title("💼 AI LinkedIn Post Generator")
st.markdown("Turn topics into **multiple engaging LinkedIn posts** using AI 🚀")

# --------------------
# 📝 Sidebar Inputs
# --------------------
with st.sidebar:
    st.header("⚙️ Post Settings")
    topic = st.text_input("Topic*", placeholder="e.g. Cold-start strategies for marketplaces")
    tone = st.selectbox("Tone", ["Professional", "Casual", "Inspirational", "Thought Leadership", "Humorous"])
    audience = st.text_input("Audience", placeholder="e.g. startup founders, marketers")
    length = st.selectbox("Length", ["Short", "Medium", "Long"])
    language = st.selectbox("Language", ["English", "Hindi", "Spanish", "French"])
    hashtags = st.checkbox("Auto-generate hashtags", value=True)
    cta = st.checkbox("Suggest Call-To-Action", value=True)
    post_count = st.slider("Number of Posts", 3, 5, 3)
    generate_btn = st.button("🚀 Generate Posts")

# --------------------
# 📂 Session History
# --------------------
if "history" not in st.session_state:
    st.session_state.history = []

# --------------------
# 🧹 Guardrail Filter
# --------------------
def clean_output(text):
    """Basic profanity filter"""
    banned_words = ["fuck", "shit", "hate", "kill"]
    for w in banned_words:
        text = re.sub(rf"\b{w}\b", "[removed]", text, flags=re.IGNORECASE)
    return text

# --------------------
# 🤖 AI Multi-Step Agent
# --------------------
def generate_posts(topic, tone, audience, length, language, hashtags, cta, post_count):
    start_time = time.time()

    # Step 1 → Plan
    plan_prompt = f"""
    You are an expert LinkedIn strategist. 
    First, outline a brief plan for {post_count} {tone.lower()} posts in {language}, 
    about "{topic}", targeting {audience or 'a general professional audience'}.
    Each plan should describe style, structure, and key points.
    """
    plan = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": plan_prompt}],
    ).choices[0].message.content

    # Step 2 → Generate Posts
    gen_prompt = f"""
    Based on this plan:\n{plan}\n
    Write {post_count} LinkedIn posts in {language}.
    Keep them {length.lower()} and {tone.lower()}.
    Each post should be natural, engaging, and professional.
    Do not repeat wording.
    """
    posts_raw = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": gen_prompt}],
    ).choices[0].message.content

    # Split posts by numbering/bullets
    posts = re.split(r"\n\s*\d+[\.\)]", posts_raw)
    posts = [p.strip() for p in posts if len(p.strip()) > 30]
    posts = posts[:post_count]

    # Step 3 → Hashtags & CTA
    extras = ""
    if hashtags or cta:
        extras_prompt = f"""
        For the topic "{topic}", suggest:
        - Relevant hashtags (if {hashtags})
        - A short call-to-action line (if {cta})
        Output clearly.
        """
        extras = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": extras_prompt}],
        ).choices[0].message.content

    # Step 4 → Apply guardrails
    posts = [clean_output(p) for p in posts]

    latency = round(time.time() - start_time, 2)
    return posts, extras, latency

# --------------------
# 🚀 Run Generator
# --------------------
if generate_btn:
    if not topic:
        st.warning("⚠️ Please enter a topic.")
    else:
        with st.spinner("✨ Crafting LinkedIn posts..."):
            try:
                posts, extras, latency = generate_posts(
                    topic, tone, audience, length, language, hashtags, cta, post_count
                )
                st.session_state.history.append(posts)

                # --------------------
                # 📊 Show Results
                # --------------------
                st.subheader("📝 Generated LinkedIn Posts")
                cols = st.columns(3)

                for i, post in enumerate(posts, 1):
                    with cols[(i - 1) % 3]:
                        st.markdown(f"### 📌 Option {i}")
                        st.write(post)
                        st.caption(f"Words: {len(post.split())} | Characters: {len(post)}")
                        st.download_button(
                            f"⬇️ Download Option {i}",
                            post,
                            file_name=f"linkedin_post_{i}.txt"
                        )

                if extras:
                    st.markdown("---")
                    st.subheader("🔖 Suggestions")
                    st.write(extras)

                st.info(f"⏱️ Generated in {latency} seconds")

            except Exception as e:
                st.error(f"❌ Error: {e}")

# --------------------
# 📜 History
# --------------------
if st.session_state.history:
    with st.expander("📜 View Previous Generations"):
        for i, posts in enumerate(st.session_state.history[:-1], 1):
            st.markdown(f"**Run {i}:**")
            for j, p in enumerate(posts, 1):
                st.markdown(f"- **Option {j}:** {p[:80]}...")
