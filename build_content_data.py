#!/usr/bin/env python3
"""
build_content_data.py — converts manual_data.json into content-data.js
for the Management Academy web app, following the exact schema used by
the F&I Academy site (window.ACADEMY_DATA = {modules, moduleQuizzes,
part1Exam, part2Exam}).

Goal statements and forward-pointer text are intentionally excluded from
module blocks, matching the F&I reference: the web app's own "next
module" navigation replaces the manual's printed forward pointer, and the
goal statement isn't rendered on the web (same as F&I).
"""
import json

with open('manual_data.json', encoding='utf-8') as f:
    blocks = json.load(f)


def runs_to_md(runs):
    """Reconstruct **bold** / *italic* markdown from parsed runs, matching
    the markdown-in-text convention content-data.js / app.js's renderInline()
    expects."""
    out = []
    for r in runs:
        t = r.get('text', '')
        if r.get('bold') and r.get('italic'):
            out.append(f'***{t}***')
        elif r.get('bold'):
            out.append(f'**{t}**')
        elif r.get('italic'):
            out.append(f'*{t}*')
        else:
            out.append(t)
    return ''.join(out)


PART_TITLES = {}  # 'I' -> title label, 'II' -> title label
PART_LABELS = {}  # 'I' -> "PART I" style short label (unused downstream but kept for clarity)

modules = []
module_quizzes = {}
part1_exam = []
part2_exam = []

current_module = None
current_part_roman = None
pending_section_num = None
last_type = None
bullet_accum = None  # list of markdown strings, flushed into a 'bullets' block

current_question = None
current_section = None  # 'module', 'exam1', 'exam2'


def flush_bullets():
    global bullet_accum
    if bullet_accum:
        current_module['blocks'].append({"type": "bullets", "items": bullet_accum})
    bullet_accum = None


for idx, b in enumerate(blocks):
    t = b['type']

    if t == 'part_divider':
        roman = 'I' if b['title'] == 'PART I' else 'II'
        PART_TITLES[roman] = b['subtitle_label'].title() if False else b['subtitle_label']
        current_part_roman = roman
        last_type = t
        continue

    if t == 'module_number':
        if current_module:
            flush_bullets()
            modules.append(current_module)
        current_module = {
            "num": int(b['number']),
            "title": None,
            "part": current_part_roman,
            "tagline": None,
            "blocks": [],
        }
        current_section = 'module'
        current_question = None
        bullet_accum = None
        continue

    if t == 'module_title':
        current_module['title'] = b['title']
        last_type = t
        continue

    if t == 'tagline':
        current_module['tagline'] = b['text']
        last_type = t
        continue

    # Module-content block types only apply while we're inside an actual
    # module's content (current_section == 'module'). Exam/TOC-adjacent
    # lines like the exam subtitle ("Leading the Department") use the same
    # generic paragraph/bold patterns but aren't module content.
    if t in ('section_label', 'callout', 'bullet', 'labeled_bullet', 'weak', 'strong', 'paragraph') \
            and (current_module is None or current_section != 'module'):
        last_type = t
        continue

    if t == 'section_label':
        pending_section_num = b['text'].replace('PART ', '')
        last_type = t
        continue

    if t == 'callout':
        if last_type == 'section_label':
            flush_bullets()
            current_module['blocks'].append({"type": "part", "num": pending_section_num, "title": b['text']})
        else:
            flush_bullets()
            current_module['blocks'].append({"type": "emphasis", "text": b['text']})
        last_type = t
        continue

    if t == 'bullet':
        text_md = runs_to_md(b['runs'])
        if bullet_accum is None:
            bullet_accum = []
        bullet_accum.append(text_md)
        last_type = t
        continue

    if t == 'labeled_bullet':
        text_md = f"**{b['label']}**  —  " + runs_to_md(b['runs'])
        if bullet_accum is None:
            bullet_accum = []
        bullet_accum.append(text_md)
        last_type = t
        continue

    if t in ('weak', 'strong'):
        flush_bullets()
        label = 'WEAK:' if t == 'weak' else 'STRONG:'
        text_md = f"**{label}** " + runs_to_md(b['runs'])
        current_module['blocks'].append({"type": "para", "text": text_md})
        last_type = t
        continue

    if t == 'paragraph':
        if current_section == 'goal_skip':
            last_type = t
            continue
        flush_bullets()
        current_module['blocks'].append({"type": "para", "text": runs_to_md(b['runs'])})
        last_type = t
        continue

    # Excluded from web content, matching F&I: goal_head, goal_text (plain
    # paragraph right after it — but we can't distinguish goal_text from a
    # normal paragraph by type alone, so we special-case: skip paragraphs
    # that immediately follow a goal_head, until the forward pointer)
    if t == 'goal_head':
        current_section = 'goal_skip'
        last_type = t
        continue

    if t == 'forward':
        current_section = 'module'
        last_type = t
        continue

    if t == 'review_head':
        flush_bullets()
        if current_module:
            modules.append(current_module)
            current_module = None
        current_section = 'review'
        current_module_num_for_quiz = int(b['number'])
        module_quizzes[str(current_module_num_for_quiz)] = []
        last_type = t
        continue

    if t == 'check_head' or t == 'check_sub':
        last_type = t
        continue

    if t == 'exam_head':
        current_section = 'exam1' if b['title'] == 'PART I EXAM' else 'exam2'
        last_type = t
        continue

    if t == 'question':
        current_question = {"q": runs_to_md(b['runs']), "options": [], "answer": 0}
        last_type = t
        continue

    if t == 'option':
        current_question['options'].append(runs_to_md(b['runs']))
        if b['correct']:
            current_question['answer'] = len(current_question['options']) - 1
        # an option is always the last block of a question; commit when we
        # have 4 options collected
        if len(current_question['options']) == 4:
            if current_section == 'review':
                module_quizzes[str(current_module_num_for_quiz)].append(current_question)
            elif current_section == 'exam1':
                part1_exam.append(current_question)
            elif current_section == 'exam2':
                part2_exam.append(current_question)
            current_question = None
        last_type = t
        continue

    if t == 'hr':
        continue

    # doc_pretitle / doc_title / doc_subtitle / doc_tagline / doc_roles /
    # title_page_end are title-page only — not part of module content.
    last_type = t

# flush any trailing module (shouldn't normally happen since review_head closes it)
if current_module:
    flush_bullets()
    modules.append(current_module)

print(f"Parsed {len(modules)} modules")
print(f"Module quizzes: {len(module_quizzes)}")
print(f"Part I exam questions: {len(part1_exam)}")
print(f"Part II exam questions: {len(part2_exam)}")

data = {
    "modules": modules,
    "moduleQuizzes": module_quizzes,
    "part1Exam": part1_exam,
    "part2Exam": part2_exam,
}

with open('content-data.js', 'w', encoding='utf-8') as f:
    f.write("// Auto-generated from the locked Motos America Management Academy manual.\n")
    f.write("// Do not hand-edit; regenerate from the source docx/manual_data.json if content changes.\n")
    f.write("window.ACADEMY_DATA = ")
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write(";\n")

print("Wrote content-data.js")
