import streamlit as st
import ollama
import pandas as pd
import re 

# Config
ollama_model = "gemma:2b"

def process_csv(file, status_placeholder) :
    df = pd.read_csv(file)
    result = pd.DataFrame(columns=["Name", "AI Suggested Descriptions"])
    for i, r in df.iterrows() :
        print("\n------------------------------------------------------\n")
        print("Processing row", i+1, "of", len(df))
        status_placeholder.write(f"Processing row {i+1}/{len(df)}: {r['Name']}")
        try :
            df['Name'] = df['Name'].str.strip()
            df['Features'] = df['Features'].str.strip()
            df['Category'] = df['Category'].str.strip()
            prompt = f"""
                        Write a single-sentenced SEO friendly product description using the following details.
                        Product Name : '{r['Name']}' 
                        Features : '{r['Features']}' 
                        Category : '{r['Category']}'
                        Output only the description and nothing else.
                    """
            response = ollama.chat(model=ollama_model, messages=[{"role": "user", "content": prompt}])
            # print("\nAI response:", response)
            description = response.message['content'].strip()
            print("\nGenerated description:", description)
            if 'description' in description.lower() :
                # Try to extract the actual description from various formats
                # 1. Extract text between ** ... **
                match = re.search(r"\*\*(.*?)\*\*", description)
                if match:
                    description = match.group(1).strip()
                else:
                    # 2. Extract after "description:" or "as requested:" or "you requested:"
                    match = re.search(r"(?:description\s*:|as requested\s*:|you requested\s*:)\s*(.*)", description, re.IGNORECASE)
                    if match:
                        description = match.group(1).strip()
                    else:
                        # 3. Remove leading phrases like "Sure, here is..." or similar
                        description = re.sub(r"^(sure[,\.]?|here is[,\.]?|here's[,\.]?|as requested[,\.]?|product description[:,\.]?|the product description is[:,\.]?|description[:,\.]?|ai suggestion[:,\.]?|seo description[:,\.]?|output[:,\.]?|:)\s*", "", description, flags=re.IGNORECASE)
                        description = description.strip()
            print("\n Inserting description:", description)
            result = pd.concat([result, pd.DataFrame({"Name": [r['Name']], "AI Suggested Descriptions": [description]})], ignore_index=True)
        except Exception as e :
            print("\nError processing row", i+1, ":", e)
            status_placeholder.write(f"Error processing row {i+1}: {e}")
            result = pd.concat([result, pd.DataFrame({"Name": [r['Name']], "AI Suggested Descriptions": ["Error generating description"]})], ignore_index=True)
    return result

def main() :
    st.title("SEO Product Description Generator")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is not None :
        generate = st.button("Generate Descriptions")
        if generate :
            status_placeholder = st.empty()
            status_placeholder.text("Processing...")
            result = process_csv(uploaded_file, status_placeholder)
            status_placeholder.text("Processing complete!")
            print("\nProcessing complete. Displaying results.")
            st.subheader("AI Suggestions")
            st.dataframe(result)
            st.download_button("Download CSV", result.to_csv(index=False), "ai_suggestions.csv", "text/csv")
    else :
        st.info("Please upload a CSV file to proceed.")
        return

if __name__ == "__main__" :
    main()