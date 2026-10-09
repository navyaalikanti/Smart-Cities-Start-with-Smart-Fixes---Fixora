import re

with open('frontend/src/style.css', 'r') as f:
    css = f.read()

# Replace root variables
root_replacement = '''
:root {
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: var(--text);
  background: var(--surface);
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;

  --primary: #007F9E;
  --primary-hover: #006D83;
  --emphasis: #075985;
  --accent: #E8F4F8;
  --surface: #FFFFFF;
  --surface-secondary: #F7F9FA;
  --text: #17212B;
  --text-secondary: #526579;
  --border: #DCE4EA;
}
'''
css = re.sub(r':root\s*\{[^}]*\}', root_replacement.strip(), css)

# Fix variables
css = css.replace('var(--green)', 'var(--primary)')
css = css.replace('var(--green-dark)', 'var(--primary-hover)')
css = css.replace('var(--mint)', 'var(--accent)')
css = css.replace('var(--border-strong)', 'var(--border)')

# Colors mapping
colors = {
    r'#(007F9E|007f9e)': 'var(--primary)',
    r'#(006D83|006d83)': 'var(--primary-hover)',
    r'#(E8F4F8|e8f4f8|E7F1F8|e7f1f8|eaf4f7)': 'var(--accent)',
    r'#(FFFFFF|ffffff|fff)(?![0-9a-fA-F])': 'var(--surface)',
    r'#(F7F9FA|f7f9fa|f8f9fa)': 'var(--surface-secondary)',
    r'#(DCE4EA|dce4ea|e5e9ec|e8ebed|e7e9ec|e9ebee|e5eaef|e8ebee|edeff0|e6e9ec|d9dfe4|dce1e5|dfe3e7|eef0f1|cdd5dc|d5dee6|cfd4d9|cfd8e1|d4dadf|edf1f4|e2e8ed|cdd4db)': 'var(--border)',
    r'#(17212B|17212b|111827|26303c|37414c|354254|414851|455261|404d5c|46505b|36485d|4d5863|465c74|505963|395273|395473)': 'var(--text)',
    r'#(526579|64748B|64748b|637080|525a64|5b6979|5a626c|535a63|556170|616974|6e7680|7a8087|757b81|7c8289|778492|768492|797f86|728090|788491|777e85|757c84|838990|828991|878d93|898f96|8b9096|8a9199|8c9299|999ea3|a8aeb4|878d94|898f97|989da2|abafb4|9a9fa4|91979d)': 'var(--text-secondary)'
}

for pat, repl in colors.items():
    css = re.sub(pat, repl, css)

# Helper function to increase font sizes
def increase_font_size(match):
    size = int(match.group(1))
    
    if size <= 8: new_size = 13
    elif size == 9: new_size = 14
    elif size == 10: new_size = 15
    elif size == 11: new_size = 15
    elif size == 12: new_size = 16
    elif size == 13: new_size = 17
    elif size == 14: new_size = 17
    elif size == 15: new_size = 18
    elif size == 17: new_size = 20
    elif size == 18: new_size = 22
    elif size == 19: new_size = 22
    elif size == 20: new_size = 24
    elif size == 22: new_size = 28
    elif size == 23: new_size = 28
    elif size == 25: new_size = 32
    elif size == 29: new_size = 32
    elif size == 32: new_size = 36
    elif size == 35: new_size = 40
    elif size == 37: new_size = 42
    elif size == 43: new_size = 46
    elif size == 45: new_size = 50
    elif size == 54: new_size = 56
    else: new_size = size + 4
    
    return f"font-size:{new_size}px"

css = re.sub(r'font-size:\s*(\d+)px', increase_font_size, css)

with open('frontend/src/style.css', 'w') as f:
    f.write(css)
