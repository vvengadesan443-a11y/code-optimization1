# Code Optimization Studio — DAG & Peephole

A small full-stack Compiler Design project. The frontend is HTML/CSS/JavaScript; the backend is Python + Flask.

## Features
- Enter different simple assignment / three-address code inputs.
- DAG-style common subexpression reuse for arithmetic expressions.
- Peephole optimizations: constant folding and basic algebraic simplification.
- Optimization trace with before/after explanations.
- Responsive interface.

## Requirements
- Python 3.10+
- pip

## Run locally
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000 in your browser.

## Example input
```text
t1 = a + b
t2 = a + b
t3 = t2 * 1
t4 = 3 * 4
result = t3 + t4
```

## Notes / limitations
This is an educational optimizer, not a complete compiler. It handles simple assignment statements and basic arithmetic. It does not parse full C, loops, conditionals, pointers, side effects, or all compiler control-flow cases. The DAG implementation is a simplified common-subexpression pass; do not use it to optimize arbitrary production code.

## GitHub
1. Create a public repository.
2. Upload all project files and folders, preserving the structure.
3. To run the Flask app online, use a Python-capable host such as Render or PythonAnywhere. GitHub Pages only hosts static frontend files and cannot run this Flask backend.
