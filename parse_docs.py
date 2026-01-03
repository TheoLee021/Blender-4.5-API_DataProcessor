import os
import json
import logging
import re
from bs4 import BeautifulSoup, NavigableString
from glob import glob

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SRC_DIR = "selected_blender_docs"
OUTPUT_FILE = "parsed_blender_api.jsonl"

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

def parse_html_file(file_path):
    """Parses a single HTML file and yields extracted API entities."""
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # 1. Target Content
    article = soup.find("article", role="main") or soup.find("div", role="main")
    if not article:
        return

    # Extract Base URL from Canonical Link
    base_url = ""
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if canonical:
        base_url = canonical.get("href", "").replace("/current/", "/4.5/")

    # 2. Find all definitions (Flat Search)
    definitions = article.find_all("dl", class_=lambda c: c and c.startswith("py"))
    
    # Pre-calculate file ID for main topic detection
    file_id = os.path.splitext(os.path.basename(file_path))[0]

    for dl in definitions:
        entity = {}
        
        # 3. Type Extraction
        classes = dl.get("class", [])
        entity_type = "unknown"
        valid_types = {'class', 'function', 'method', 'attribute', 'data', 'module', 'classmethod', 'staticmethod', 'exception'}
        for cls in classes:
            if cls in valid_types:
                entity_type = cls
                break
            # Handle potential py- prefix variants
            if cls.startswith("py-") and cls[3:] in valid_types:
                entity_type = cls[3:]
                break
        entity["type"] = entity_type

        # 4. Name & ID Extraction
        dt = dl.find("dt")
        if not dt: continue
        
        entity["id"] = dt.get("id", "")
        if not entity["id"]: continue

        # Clean Name logic
        sig_name = dt.find("span", class_="sig-name descname")
        if sig_name:
            entity["name"] = sig_name.get_text()
        else:
            entity["name"] = clean_text(dt.get_text())

        entity["signature"] = clean_text(dt.get_text())
        
        # Add URL
        if base_url and entity.get("id"):
            entity["url"] = f"{base_url}#{entity['id']}"
        else:
            entity["url"] = ""

        # --- Pre-fetch Page-Level Content (Introduction & Examples) ---
        intro_desc = []
        intro_code = []
        
        # If this entity is the main topic of the page
        if entity["id"] == file_id:
            curr = dl.previous_sibling
            while curr:
                if isinstance(curr, NavigableString):
                    curr = curr.previous_sibling
                    continue
                
                tag_name = curr.name
                if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dl']:
                    break # Stop at headers or other definitions
                
                # Capture Description
                if tag_name == 'p':
                    text = clean_text(curr.get_text())
                    if text: intro_desc.insert(0, text)
                
                # Capture Code
                elif tag_name == 'div' and ('highlight' in curr.get('class', []) or curr.find('div', class_='highlight')):
                     pres = curr.find_all('pre')
                     for pre in reversed(pres):
                         intro_code.insert(0, pre.get_text())
                elif tag_name == 'pre':
                     intro_code.insert(0, curr.get_text())
                
                curr = curr.previous_sibling

        # 5. Description & Code Extraction (Safe Logic)
        dd = dl.find("dd")
        description_parts = []
        code_examples = []
        
        if dd:
            for child in dd.children:
                if child.name == 'dl' and 'py' in child.get('class', []):
                    continue
                
                if child.name == 'dl' and 'field-list' in child.get('class', []):
                    continue

                # Code Block Extraction
                if child.name == 'pre':
                    code_examples.append(child.get_text())
                
                elif child.name == 'div':
                    pres = child.find_all('pre')
                    if pres:
                        for pre in pres:
                            code_examples.append(pre.get_text())
                        continue
                    else:
                        text = clean_text(child.get_text())
                        if text: description_parts.append(text)

                # Text Extraction
                elif isinstance(child, NavigableString):
                    text = str(child).strip()
                    if text: description_parts.append(text)
                elif child.name in ['p', 'ul', 'ol', 'div', 'span']:
                    text = clean_text(child.get_text())
                    if text: description_parts.append(text)

            # Combine Intro + Main Content
            entity["description"] = " ".join(intro_desc + description_parts)
            entity["code_examples"] = intro_code + code_examples

            # 6. Structured Fields
            field_list = dd.find("dl", class_="field-list")
            if field_list:
                current_field = None
                
                for child in field_list.children:
                    if child.name == "dt":
                        current_field = clean_text(child.get_text()).lower()
                    elif child.name == "dd" and current_field:
                        field_text = clean_text(child.get_text())
                        
                        if "type" in current_field and "return" not in current_field:
                            entity["data_type"] = field_text
                        elif "return" in current_field:
                            entity["return_type"] = field_text
                        elif "param" in current_field:
                            params = []
                            ul = child.find("ul")
                            if ul:
                                for li in ul.find_all("li"):
                                    params.append(clean_text(li.get_text()))
                            else:
                                params.append(field_text)
                            
                            if "parameters" in entity:
                                entity["parameters"].extend(params)
                            else:
                                entity["parameters"] = params
                        
                        current_field = None

        yield entity

def main():
    if not os.path.exists(SRC_DIR):
        logging.error(f"Source directory '{SRC_DIR}' not found.")
        return

    html_files = glob(os.path.join(SRC_DIR, "*.html"))
    logging.info(f"Found {len(html_files)} HTML files to parse.")
    
    count = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        for file_path in html_files:
            for entity in parse_html_file(file_path):
                out_f.write(json.dumps(entity, ensure_ascii=False) + "\n")
                count += 1
                    
    logging.info(f"Parsed {count} API entities. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()