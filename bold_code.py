"""
bold_code_snippets.py

Makes code snippets bold in a downloaded .docx file.

Code snippets are paragraphs that follow a label paragraph matching patterns like:
  "Python:", "JavaScript:", "Example:", "Example: ...", "Python Example:",
  "JavaScript Example:", "JavaScript Prototype Example:", etc.

Usage:
    python bold_code_snippets.py input.docx output.docx

Dependencies:
    pip install python-docx
"""

import sys
import re
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches label lines that introduce a code block
LABEL_PATTERN = re.compile(
    r"^\s*"
    r"("
    r"Python(\s+\w+(\s+\w+)*)?"          # Python, Python Example, Python Constructor…
    r"|JavaScript(\s+\w+(\s+\w+)*)?"     # JavaScript, JavaScript Prototype Example…
    r"|Arrow Functions in JavaScript"
    r"|Modern JavaScript Class Example"
    r"|CommonJS uses.*"
    r"|Example(:\s*.*)?"                 # Example, Example: Fetching Data with…
    r")"
    r"\s*:?\s*$",
    re.IGNORECASE,
)

# Matches lines that look like code
CODE_HINTS = re.compile(
    r"^\s*("
    # common code keywords / symbols at the start
    r"(def |class |import |from |print\(|for |while |if |else\b|elif |return |"
    r"const |let |var |function |async |await |#|//|\/\*|\*\s|{|}|\[|\]|@|\$)"
    # shell / package manager commands
    r"|(npm |pip |node |python |bash|source |myenv|coverage |describe\(|it\(|cy\.)"
    # assignment, arrow, or call: word = / word( / word[ / word:
    r"|\w[\w.]*\s*(=|=>|\(|\[)\s*"
    # method chain: word.something
    r"|[a-zA-Z_]\w*\.\w"
    # indented lines (2+ spaces then non-space) — typical inside code blocks
    r"|\s{2,}\S"
    r")",
    re.IGNORECASE,
)

# Matches a whole-line comment: optional whitespace then # or //
WHOLE_LINE_COMMENT = re.compile(r"^\s*(#|//)")

def comment_split_index(text: str):
    """
    Return the character index where an inline comment starts, or None.
    Handles:  code  # comment   and   code  // comment
    Only matches # / // that appear AFTER some non-whitespace code content,
    so whole-line comments (line starts with # or //) return None here
    (they are handled separately via WHOLE_LINE_COMMENT).
    """
    # Find the first # or // that is preceded by non-whitespace content
    match = re.search(r'\s+(#|//)', text)
    if match:
        return match.start()  # index of the whitespace before the comment marker
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def paragraph_text(para) -> str:
    return "".join(run.text or "" for run in para.runs)


def is_label(text: str) -> bool:
    return bool(LABEL_PATTERN.match(text.strip()))


def is_code_like(text: str) -> bool:
    return bool(CODE_HINTS.match(text)) if text.strip() else False


def is_clear_prose(text: str) -> bool:
    """Heuristic: long, sentence-like text that ends with punctuation."""
    stripped = text.strip()
    if not stripped:
        return False
    if is_code_like(stripped):
        return False
    words = stripped.split()
    if len(words) > 10 and stripped[-1] in ".,:":
        return True
    if stripped[0].isupper() and not is_code_like(stripped) and len(words) > 7:
        return True
    return False


def run_font_is_mono(run) -> bool:
    rPr = run._r.find(qn("w:rPr"))
    if rPr is None:
        return False
    fonts = rPr.find(qn("w:rFonts"))
    if fonts is None:
        return False
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        val = fonts.get(qn(attr), "")
        if val and any(m in val.lower() for m in ("courier", "mono", "consol", "code", "source code")):
            return True
    return False


def para_is_mono(para) -> bool:
    runs = [r for r in para.runs if r.text.strip()]
    return bool(runs) and all(run_font_is_mono(run) for run in runs)


def make_run_bold(run_elem):
    rPr = run_elem.find(qn("w:rPr"))
    if rPr is None:
        rPr = OxmlElement("w:rPr")
        run_elem.insert(0, rPr)
    if rPr.find(qn("w:b")) is None:
        b = OxmlElement("w:b")
        rPr.insert(0, b)
    if rPr.find(qn("w:bCs")) is None:
        bCs = OxmlElement("w:bCs")
        rPr.append(bCs)


def bold_paragraph(para):
    """
    Bold the code portion of a paragraph, leaving comments plain.

    Three cases:
      1. Whole-line comment (starts with # or //) → bold nothing.
      2. Inline comment (code  # comment) → bold only the code portion.
      3. Pure code line → bold everything.
    """
    full_text = paragraph_text(para)

    # Case 1: whole-line comment — skip entirely
    if WHOLE_LINE_COMMENT.match(full_text):
        return

    # Case 2: inline comment — find the split point
    split_idx = comment_split_index(full_text)

    if split_idx is None:
        # Case 3: pure code — bold all runs
        for run in para.runs:
            make_run_bold(run._r)
        return

    # Case 2: bold only characters before split_idx
    char_pos = 0
    for run in para.runs:
        run_text = run.text or ""
        run_start = char_pos
        run_end = char_pos + len(run_text)

        if run_end <= split_idx:
            # Entirely in the code portion
            make_run_bold(run._r)
        elif run_start < split_idx < run_end:
            # Run straddles the boundary — split it into two runs:
            # bold part (before split) and plain part (comment)
            code_part = run_text[:split_idx - run_start]
            comment_part = run_text[split_idx - run_start:]

            # Shorten the existing run to the code portion and bold it
            run.text = code_part
            make_run_bold(run._r)

            # Insert a new plain run after it for the comment
            new_r = OxmlElement("w:r")
            # Copy run properties (font, size, etc.) but without bold
            old_rPr = run._r.find(qn("w:rPr"))
            if old_rPr is not None:
                import copy
                new_rPr = copy.deepcopy(old_rPr)
                # Remove bold tags from the comment run's properties
                for bold_tag in (qn("w:b"), qn("w:bCs")):
                    el = new_rPr.find(bold_tag)
                    if el is not None:
                        new_rPr.remove(el)
                new_r.append(new_rPr)
            new_t = OxmlElement("w:t")
            new_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            new_t.text = comment_part
            new_r.append(new_t)
            run._r.addnext(new_r)
        # else: run_start >= split_idx → entirely in comment, leave plain

        char_pos = run_end


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_document(input_path: str, output_path: str):
    doc = Document(input_path)
    paragraphs = doc.paragraphs
    n = len(paragraphs)

    to_bold = set()

    # Pass 1: label-based detection
    i = 0
    while i < n:
        text = paragraph_text(paragraphs[i]).strip()

        if is_label(text):
            j = i + 1
            found_code = False

            while j < n:
                ptext = paragraph_text(paragraphs[j]).strip()

                if not ptext:
                    # Blank line — look ahead to decide whether block continues
                    look = j + 1
                    while look < n and not paragraph_text(paragraphs[look]).strip():
                        look += 1
                    if look < n:
                        next_text = paragraph_text(paragraphs[look]).strip()
                        if is_code_like(next_text) or para_is_mono(paragraphs[look]):
                            j += 1  # skip blank, stay in block
                            continue
                    break  # end of block

                # A new label starts a new section — stop current block
                if is_label(ptext) and found_code:
                    break

                # Clear prose ends the block
                if is_clear_prose(ptext) and not para_is_mono(paragraphs[j]):
                    break

                to_bold.add(j)
                found_code = True
                j += 1

            i = j
        else:
            i += 1

    # Pass 2: monospace font paragraphs (catches inline code blocks the label pass missed)
    for idx, para in enumerate(paragraphs):
        if para_is_mono(para) and paragraph_text(para).strip():
            to_bold.add(idx)

    # Apply bold
    for idx in sorted(to_bold):
        bold_paragraph(paragraphs[idx])

    print(f"Bolded {len(to_bold)} code paragraphs.")
    doc.save(output_path)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python bold_code_snippets.py input.docx output.docx")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    print(f"Processing: {input_file}")
    process_document(input_file, output_file)