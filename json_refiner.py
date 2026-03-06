import gradio as gr
import json
import yaml
import xmltodict
import pandas as pd
import jmespath
import os
from flatten_json import flatten, unflatten
from io import StringIO

# --- Core Logic Functions ---

def load_json(text_input, file_input):
    """Parses JSON from either text input or file upload."""
    try:
        if file_input is not None:
            with open(file_input.name, 'r', encoding='utf-8') as f:
                content = f.read()
            return json.loads(content), "Success: File Loaded"
        elif text_input.strip():
            return json.loads(text_input), "Success: Text Parsed"
        else:
            return None, "Error: No input provided"
    except json.JSONDecodeError as e:
        return None, f"JSON Syntax Error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected Error: {str(e)}"

def save_to_temp_file(content, extension):
    """Saves output to a temporary file for downloading."""
    filename = f"output.{extension}"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

def process_data(text_input, file_input, action, query_str):
    data, msg = load_json(text_input, file_input)
    
    if data is None:
        return msg, None

    output_text = ""
    output_file = None
    
    try:
        # --- Actions ---
        
        if action == "Beautify (Pretty Print)":
            output_text = json.dumps(data, indent=4, sort_keys=True)
            output_file = save_to_temp_file(output_text, "json")

        elif action == "Minify (Compress)":
            output_text = json.dumps(data, separators=(',', ':'))
            output_file = save_to_temp_file(output_text, "json")

        elif action == "Validate":
            output_text = "✅ JSON is Valid and well-formed."
            # No file download needed for validation check

        elif action == "Flatten Structure":
            flat_data = flatten(data, separator='_')
            output_text = json.dumps(flat_data, indent=4)
            output_file = save_to_temp_file(output_text, "json")

        elif action == "Unflatten Structure":
            # Assumes input is a flat JSON
            unflat_data = unflatten(data, separator='_')
            output_text = json.dumps(unflat_data, indent=4)
            output_file = save_to_temp_file(output_text, "json")

        elif action == "Query (JMESPath)":
            if not query_str:
                return "Error: Please enter a JMESPath query.", None
            result = jmespath.search(query_str, data)
            output_text = json.dumps(result, indent=4)
            output_file = save_to_temp_file(output_text, "json")

        elif action == "Convert to YAML":
            output_text = yaml.dump(data, sort_keys=False)
            output_file = save_to_temp_file(output_text, "yaml")

        elif action == "Convert to XML":
            # XML requires a single root element
            if not isinstance(data, dict) or len(data.keys()) > 1:
                wrapped_data = {"root": data}
            else:
                wrapped_data = data
            output_text = xmltodict.unparse(wrapped_data, pretty=True)
            output_file = save_to_temp_file(output_text, "xml")

        elif action == "Convert to CSV":
            # Best effort CSV conversion
            if isinstance(data, list):
                df = pd.json_normalize(data)
            elif isinstance(data, dict):
                df = pd.json_normalize([data]) # Wrap dict in list
            else:
                return "Error: JSON must be a list of objects or an object to convert to CSV.", None
            
            output_text = df.to_csv(index=False)
            output_file = save_to_temp_file(output_text, "csv")

        return output_text, output_file

    except Exception as e:
        return f"Processing Error: {str(e)}", None

# --- Gradio UI Layout ---

theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
).set(
    button_primary_background_fill="*primary_500",
    button_primary_background_fill_hover="*primary_600",
)

with gr.Blocks(theme=theme, title="JSON Refiner Pro") as app:
    gr.Markdown(
        """
        # 💎 JSON Refiner Advanced Edition
        ### Professional JSON Processing, Validation, and Conversion Tool
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 1. Input Data")
            input_text = gr.Code(language="json", label="Paste JSON Here", lines=10)
            input_file = gr.File(label="Or Upload JSON File", file_types=[".json", ".txt"])
            
            gr.Markdown("### 2. Configuration")
            action_dropdown = gr.Dropdown(
                choices=[
                    "Beautify (Pretty Print)", 
                    "Minify (Compress)", 
                    "Validate", 
                    "Convert to YAML", 
                    "Convert to XML", 
                    "Convert to CSV",
                    "Flatten Structure",
                    "Unflatten Structure",
                    "Query (JMESPath)"
                ],
                value="Beautify (Pretty Print)",
                label="Select Action"
            )
            
            # Contextual input for JMESPath
            query_input = gr.Textbox(
                label="JMESPath Query String", 
                placeholder="e.g., people[?age > `20`].name",
                visible=False
            )
            
            process_btn = gr.Button("🚀 Process JSON", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("### 3. Output")
            output_text = gr.Code(language="json", label="Result", lines=20, interactive=False)
            output_file = gr.File(label="Download Result")

    # --- Event Listeners ---

    # Toggle Query Input visibility based on dropdown
    def toggle_query_input(val):
        return gr.update(visible=(val == "Query (JMESPath)"))

    action_dropdown.change(toggle_query_input, action_dropdown, query_input)

    # Main Processing Logic
    process_btn.click(
        fn=process_data,
        inputs=[input_text, input_file, action_dropdown, query_input],
        outputs=[output_text, output_file]
    )

# --- Launch App ---
if __name__ == "__main__":
    app.launch()