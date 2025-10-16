import yaml
import csv
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
yaml_file = os.path.join(os.path.dirname(script_dir), 'config', 'decision_tree2.yaml')
csv_file = os.path.join(script_dir, 'decision_tree2.csv')

# Read the YAML file
with open(yaml_file, 'r') as f:
    data = yaml.safe_load(f)

# Prepare CSV rows
csv_rows = []

# Add header row
csv_rows.append([
    'Question ID',
    'Level',
    'Risk Area',
    'Type',
    'Question Text',
    'Response Type',
    'Required (True/False)',
    'TRIGGER LOGIC: This question appears ONLY IF...',
    'Parent Question ID',
    'Parent Must Be Answered',
    'TRIGGERING LOGIC: If answered YES, this question triggers...',
    'Questions Triggered by YES',
    'Risk Area Activated by YES',
    'Comments/Notes'
])

# Process qualifying questions
for q in data.get('qualifying_questions', []):
    on_yes = q.get('on_yes', {})

    # Build trigger description
    trigger_description = ''
    if on_yes:
        risk_area = on_yes.get('risk_area', '')
        level = on_yes.get('level', '')
        if risk_area and level:
            trigger_description = f"Show all {level} questions in {risk_area} risk area"

    row = [
        q.get('id', ''),
        q.get('level', ''),
        'Qualifying',
        q.get('type', ''),
        q.get('question', ''),
        q.get('response_type', ''),
        str(q.get('required', '')),
        'Always shown (L1 qualifying question)',  # TRIGGER LOGIC
        '',  # Parent Question ID
        '',  # Parent Must Be Answered
        trigger_description,  # TRIGGERING LOGIC
        '',  # Questions Triggered by YES (specific IDs)
        on_yes.get('risk_area', ''),  # Risk Area Activated
        q.get('comments', '')  # Comments
    ]
    csv_rows.append(row)

# Process risk area questions
risk_areas = data.get('risk_areas', {})
risk_area_map = {
    'third_party': 'Third Party',
    'data_privacy': 'Data Privacy',
    'artificial_intelligence': 'Artificial Intelligence',
    'intellectual_property': 'Intellectual Property'
}

for area_key, area_data in risk_areas.items():
    risk_area_name = risk_area_map.get(area_key, area_key)

    for q in area_data.get('questions', []):
        depends_on = q.get('depends_on', {})
        show_questions = q.get('show_questions', [])

        # Build clear trigger logic description
        trigger_logic = ''
        parent_question_id = ''
        parent_must_be_answered = ''

        if depends_on:
            parent_question_id = depends_on.get('question_id', '')
            parent_must_be_answered = depends_on.get('answer', '')
            trigger_logic = f"Question {parent_question_id} is answered '{parent_must_be_answered}'"
        elif q.get('level') == 'L2':
            trigger_logic = f"L1 qualifying question activates {risk_area_name} risk area"
        elif q.get('level') == 'L3':
            trigger_logic = "Shown based on parent L2 question"

        # Build triggering logic description
        triggering_logic = ''
        if show_questions:
            triggering_logic = f"Shows questions: {', '.join(show_questions)}"

        row = [
            q.get('id', ''),
            q.get('level', ''),
            risk_area_name,
            '',  # type (only for qualifying questions)
            q.get('question', ''),
            q.get('response_type', ''),
            str(q.get('required', '')),
            trigger_logic,  # TRIGGER LOGIC description
            parent_question_id,  # Parent Question ID
            parent_must_be_answered,  # Parent Must Be Answered
            triggering_logic,  # TRIGGERING LOGIC description
            ', '.join(show_questions) if show_questions else '',  # Questions Triggered
            '',  # Risk Area Activated (only for L1 questions)
            q.get('comments', '')  # Comments
        ]
        csv_rows.append(row)

# Write to CSV
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(csv_rows)

print(f"CSV file created successfully at: {csv_file}")
print(f"Total questions exported: {len(csv_rows) - 1}")  # -1 for header row
