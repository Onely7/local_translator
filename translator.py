"""
A Streamlit-based translation app that uses OpenAI or Ollama models for text translation.
It supports a primary translation mode and a multi-engine comparison mode with configurable layout.

Usage:
    1. Place a YAML file (`avail_models.yaml`) under `configs/` directory.
       This YAML file maps user-facing engine names (keys) to actual model identifiers (values).

    2. Run the Streamlit app:
       streamlit run translator_app.py

    3. Select a main translation engine and target language, then enter the text to translate.
       - Click "Run Translation" for a single translation result.
       - Optionally, select multiple engines in "Compare Translations with Multiple Engines"
         and click "Compare" to see results in either horizontal or vertical layout.
"""

import os
import yaml
from typing import Dict, List
import streamlit as st

# Ollama and OpenAI are optional dependencies; only import them if needed
import ollama
from openai import OpenAI


# --- Load the model dictionary from a YAML file ---
with open("configs/avail_models.yaml", "r", encoding="utf-8") as f:
    MODEL_DICT: Dict[str, str] = yaml.safe_load(f)


def translate_text(text: str, engine: str, target_lang: str) -> str:
    """
    Translate the given text using a specified engine and target language.

    Args:
        text (str): The source text to be translated.
        engine (str): The name of the translation engine, as defined in MODEL_DICT keys.
                      Examples: "OpenAI/GPT-4o", "Ollama/gemma-3-27b-it-gguf"
        target_lang (str): The target language for the translation.
                           Examples: "Japanese", "English (United States)"

    Returns:
        str: The translated text, or an error message if an exception occurs.

    Examples:
        >>> # Example usage with an OpenAI engine
        >>> translate_text("Hello world", "OpenAI/GPT-4o", "Japanese")
        'こんにちは世界'

        >>> # Example usage with an Ollama engine
        >>> translate_text("This is a pen.", "Ollama/gemma-3-4b-it-gguf", "Japanese")
        'これはペンです。'
    """
    if not text.strip():
        return "Please enter or paste the text to be translated."

    # Determine whether engine is OpenAI-based or Ollama-based
    main_engine = engine.split("/")[0]

    try:
        if main_engine == "OpenAI":
            # Use OpenAI client
            client = OpenAI()
            client.api_key = os.getenv("OPENAI_API_KEY")
            model_id = MODEL_DICT[engine]

            # Create a chat completion request
            completion = client.chat.completions.create(
                model=model_id,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful translator. "
                            "However, only the translation result should be output. "
                            'Code blocks or phrases like "Here is the translation result:" '
                            "should not be included. "
                            f"Please translate into {target_lang}."
                        )
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ]
            )
            translation = completion.choices[0].message.content

        elif main_engine == "Ollama":
            # Use Ollama client
            model_id = MODEL_DICT[engine]
            prompt = (
                "You are a helpful translator. "
                "However, only the translation result should be output. "
                'Code blocks or phrases like "Here is the translation result:" '
                "should not be included. "
                f"Please translate into {target_lang}.\n\n"
                f"Source Sentence: {text}\n"
                "Target Sentence: "
            )
            response = ollama.chat(
                model=model_id,
                messages=[
                    {"role": "user", "content": prompt},
                ]
            )
            translation = response["message"]["content"]

        else:
            translation = "No translation engine selected."

        return translation

    except Exception as e:
        # Return a user-friendly error message
        return f"Error occurred during translation: {e}"


def main() -> None:
    """
    Main Streamlit app function. Sets up the UI for:
      - Single-engine translation (left column: input, right column: result).
      - Multi-engine comparison in either horizontal or vertical layout.

    No direct arguments are passed. The function reads from:
      - `MODEL_DICT` for available engines.
      - A predefined list of languages.

    It writes the UI elements to the Streamlit app and handles user interactions.
    """
    # Configure Streamlit page layout
    st.set_page_config(layout="wide")

    # Custom CSS for text areas and buttons
    st.markdown(
        """
        <style>
        /* Increase font size for text areas */
        div[data-testid="stTextArea"] textarea {
            font-size: 20px;
            width: 100% !important;
            max-width: 100% !important;
        }
        div[data-testid="stTextArea"] textarea::placeholder {
            font-size: 20px;
            color: #999999;
        }
        /* Increase padding for buttons */
        div.stButton > button {
            padding: 0.2rem 1.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 1. Select a single engine and language
    available_engines: List[str] = list(MODEL_DICT.keys())
    available_languages: List[str] = [
        "Japanese", "English (United States)", "Spanish", "Slovak", "Slovenian",
        "Czech", "Danish", "German", "Turkish", "Norwegian (Bokmål)", "Hungarian",
        "Finnish", "French", "Bulgarian", "Polish", "Portuguese", "Portuguese (Brazil)",
        "Latvian", "Lithuanian", "Romanian", "Russian", "English (United Kingdom)",
        "Korean", "Chinese (Simplified)", "Chinese (Traditional)", "Arabic", "Italian",
        "Indonesian", "Ukrainian", "Estonian", "Dutch", "Greek", "Swedish"
    ]

    sel_col1, sel_col2 = st.columns(2)
    with sel_col1:
        engine = st.selectbox("**Translation Engine**", available_engines)
    with sel_col2:
        tgt_lang = st.selectbox("**Target Language**", available_languages)

    # 2. Main translation (left: input, right: output)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Input Source Text")
        text_to_translate = st.text_area(
            label="",
            height=450,
            key="source_text",
            placeholder="Please enter or paste the text to be translated",
            label_visibility="collapsed"
        )

        if st.button("Run Translation"):
            st.session_state["translation"] = translate_text(text_to_translate, engine, tgt_lang)

    with col2:
        st.subheader("Translation Result")
        translation = st.session_state.get("translation", "")
        st.text_area("", translation, height=450, key="translated_text", label_visibility="collapsed")

    # 3. Comparison section
    st.markdown("---")
    st.subheader("Compare Translations with Multiple Engines")

    compare_engines = st.multiselect(
        "**Select multiple engines to compare**",
        available_engines,
        default=[],
        help="Choose one or more engines to compare the translation results."
    )

    # Let the user pick between horizontal or vertical layout for comparison
    layout_option = st.radio(
        "**Comparison Layout**",
        ("Horizontal", "Vertical"),
        index=0,
        horizontal=True
    )

    if st.button("Compare"):
        compare_results: Dict[str, str] = {}
        for e in compare_engines:
            compare_results[e] = translate_text(text_to_translate, e, tgt_lang)

        if layout_option == "Vertical":
            # Show results in expanders (vertical stacking)
            for eng_name, result in compare_results.items():
                with st.expander(f"**{eng_name}**", expanded=True):
                    st.text_area("", result, height=200, key=f"compare_{eng_name}", label_visibility="collapsed")
                    st.write("")  # spacing
        else:
            # Show results side-by-side (horizontal)
            if len(compare_results) == 0:
                st.warning("No engines selected for comparison.")
            else:
                cols = st.columns(len(compare_results))
                for (eng_name, result), col in zip(compare_results.items(), cols):
                    with col:
                        st.markdown(f"**{eng_name}**")
                        st.text_area("", result, height=300, key=f"compare_{eng_name}", label_visibility="collapsed")


if __name__ == "__main__":
    main()
