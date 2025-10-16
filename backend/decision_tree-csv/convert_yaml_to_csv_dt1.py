import yaml
import csv
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
yaml_file = os.path.join(os.path.dirname(script_dir), 'config', 'decision_tree1.yaml')
csv_file = os.path.join(script_dir, 'decision_tree1.csv')

# Read the YAML file
with open(yaml_file, 'r') as f:
    data = yaml.safe_load(f)

# Prepare CSV rows
csv_rows = []

# Add header row with comprehensive columns
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
    'TRIGGERING LOGIC: What happens when answered...',
    'On YES: Action',
    'On YES: Skip/Show Questions',
    'On NO: Action',
    'On NO: Skip/Show Questions',
    'Skip If Conditions',
    'Show If Any Conditions',
    'Comments/Notes'
])

# Process qualifying questions
for q in data.get('qualifying_questions', []):
    on_yes = q.get('on_yes', {})
    on_no = q.get('on_no', {})

    # Build trigger description for YES
    trigger_yes = ''
    yes_action = ''
    yes_questions = ''
    if on_yes:
        yes_action = on_yes.get('action', '')
        risk_area = on_yes.get('risk_area', '')
        level = on_yes.get('level', '')
        if risk_area and level:
            trigger_yes = f"Show all {level} questions in {risk_area} risk area"
        yes_questions = ', '.join(on_yes.get('show_questions', [])) if on_yes.get('show_questions') else ''

    # Build trigger description for NO
    trigger_no = ''
    no_action = ''
    no_questions = ''
    if on_no:
        no_action = on_no.get('action', '')
        no_questions = ', '.join(on_no.get('skip_questions', [])) if on_no.get('skip_questions') else ''

    triggering_logic = ''
    if trigger_yes:
        triggering_logic = f"YES: {trigger_yes}"
    if trigger_no:
        if triggering_logic:
            triggering_logic += f" | NO: Skip questions {no_questions}"
        else:
            triggering_logic = f"NO: Skip questions {no_questions}"

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
        triggering_logic,  # TRIGGERING LOGIC
        yes_action,  # On YES: Action
        yes_questions,  # On YES: Skip/Show Questions
        no_action,  # On NO: Action
        no_questions,  # On NO: Skip/Show Questions
        '',  # Skip If Conditions
        '',  # Show If Any Conditions
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
        on_yes = q.get('on_yes', {})
        on_no = q.get('on_no', {})
        skip_if = q.get('skip_if', [])
        show_if_any = q.get('show_if_any', [])

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
        elif q.get('level') in ['L3', 'L4']:
            trigger_logic = "Shown based on parent question logic"

        # Add skip_if conditions
        if skip_if:
            skip_conditions = []
            for condition in skip_if:
                skip_conditions.append(f"{condition.get('question_id', '')}={condition.get('answer', '')}")
            trigger_logic += f" (Hidden if: {', '.join(skip_conditions)})"

        # Add show_if_any conditions
        if show_if_any:
            show_conditions = []
            for condition in show_if_any:
                show_conditions.append(f"{condition.get('question_id', '')}={condition.get('answer', '')}")
            trigger_logic += f" (Show if any: {', '.join(show_conditions)})"

        # Build triggering logic description
        triggering_logic = ''
        yes_action = ''
        yes_questions = ''
        no_action = ''
        no_questions = ''

        if on_yes:
            yes_action = on_yes.get('action', '')
            yes_questions = ', '.join(on_yes.get('skip_questions', [])) if on_yes.get('skip_questions') else ''
            if yes_action == 'skip_questions':
                triggering_logic = f"YES: Skip questions {yes_questions}"

        if on_no:
            no_action = on_no.get('action', '')
            no_questions = ', '.join(on_no.get('skip_questions', [])) if on_no.get('skip_questions') else ''
            if no_action == 'skip_questions':
                if triggering_logic:
                    triggering_logic += f" | NO: Skip questions {no_questions}"
                else:
                    triggering_logic = f"NO: Skip questions {no_questions}"

        # Format skip_if and show_if_any for display
        skip_if_display = ''
        if skip_if:
            conditions = [f"{c.get('question_id', '')} = {c.get('answer', '')}" for c in skip_if]
            skip_if_display = '; '.join(conditions)

        show_if_any_display = ''
        if show_if_any:
            conditions = [f"{c.get('question_id', '')} = {c.get('answer', '')}" for c in show_if_any]
            show_if_any_display = '; '.join(conditions)

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
            yes_action,  # On YES: Action
            yes_questions,  # On YES: Skip/Show Questions
            no_action,  # On NO: Action
            no_questions,  # On NO: Skip/Show Questions
            skip_if_display,  # Skip If Conditions
            show_if_any_display,  # Show If Any Conditions
            q.get('comments', '')  # Comments
        ]
        csv_rows.append(row)

# Write to CSV
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(csv_rows)

print(f"CSV file created successfully at: {csv_file}")
print(f"Total questions exported: {len(csv_rows) - 1}")  # -1 for header row
