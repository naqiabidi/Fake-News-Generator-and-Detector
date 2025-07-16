import streamlit as st
from transformers import pipeline, GPT2Tokenizer, GPT2LMHeadModel
import torch
import json  # Import the json library to handle the file
import os    # Import the os library to build the file path

# --- SCRIPT TO AUTOMATICALLY FIX config.json ---
# This code runs first to ensure the config file is correct.
CONFIG_PATH = os.path.join("my_fake_news_detector", "config.json")

try:
    # Read the existing config file
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    # Add or update the 'model_type' key
    config_data["model_type"] = "distilbert"

    # Write the corrected data back to the file
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)

    # Use a temporary success message to confirm the fix was applied
    st.toast("Successfully fixed the configuration file!", icon="✅")

except Exception as e:
    st.error(f"A critical error occurred while trying to fix config.json: {e}")
    st.info("Please ensure the 'my_fake_news_detector' folder is in the same directory as 'app.py'.")
    st.stop()
# --- END OF FIXER SCRIPT ---


# --- PAGE CONFIGURATION (The rest of your app) ---
st.set_page_config(page_title="Fake News Project", layout="wide")


# --- APP TITLE AND DESCRIPTION ---
st.title("Fake News Generator and Detector ")

st.markdown("---")


# --- MODEL LOADING ---
@st.cache_resource
def load_detector_model():
    """Loads the custom fine-tuned fake news detector model."""
    return pipeline('text-classification', model='./my_fake_news_detector')

@st.cache_resource
def load_generator_model():
    """Loads the pre-trained GPT-2 model and tokenizer."""
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    model = GPT2LMHeadModel.from_pretrained('gpt2')

    # --- FIX TO SILENCE THE PADDING WARNINGS ---
    # Set the padding token to be the same as the end-of-sequence token
    tokenizer.pad_token = tokenizer.eos_token
    # Update the model's configuration with the new pad_token_id
    model.config.pad_token_id = tokenizer.eos_token_id
    # --- END OF FIX ---

    return tokenizer, model

with st.spinner("Loading AI models... This might take a moment."):
    detector = load_detector_model()
    generator_tokenizer, generator_model = load_generator_model()


# --- APP LAYOUT ---
col1, col2 = st.columns(2)


# --- COLUMN 1: FAKE NEWS GENERATOR ---
with col1:
    st.header("1. Fake News Generator")
    prompt_text = st.text_input(
        "Enter a prompt to start the headline:",
        "In a surprising turn of events,"
    )

    if st.button("Generate Headline"):
        if prompt_text:
            with st.spinner("🧠 Generating..."):
                inputs = generator_tokenizer.encode(prompt_text, return_tensors='pt')
                outputs = generator_model.generate(
                    inputs, max_length=35, num_return_sequences=1, do_sample=True, top_k=50
                )
                generated_text = generator_tokenizer.decode(outputs[0], skip_special_tokens=True)
                headline = generated_text.replace(prompt_text, "").split('\n')[0].strip()
                st.subheader("Generated Headline:")
                st.info(headline)
                st.session_state.headline_to_check = headline
        else:
            st.warning("Please enter a prompt first.")


# --- COLUMN 2: FAKE NEWS DETECTOR ---
with col2:
    st.header("2. Fake News Detector")

    if 'headline_to_check' not in st.session_state:
        st.session_state.headline_to_check = "The stock market closed with a 2% gain today."

    headline_to_check = st.text_area(
        "Enter a headline to analyze:",
        key="headline_to_check",
        height=70
    )

    if st.button("Analyze Headline"):
        if headline_to_check:
            with st.spinner("🔍 Analyzing..."):
                result = detector(headline_to_check)[0]
                label = result['label']
                score = result['score']
                st.subheader("Analysis Result:")
                if label == 'LABEL_0':
                    st.success(f"✅ Verdict: REAL News (Confidence: {score:.2f})")
                elif label == 'LABEL_1':
                    st.error(f"❌ Verdict: FAKE News (Confidence: {score:.2f})")
        else:
            st.warning("Please enter a headline to analyze.")