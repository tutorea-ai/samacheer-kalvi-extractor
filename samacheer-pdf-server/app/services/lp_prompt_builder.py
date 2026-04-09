"""
LP Prompt Builder v2 — with detailed bilingual scripting
TL Requirement: English instructions must be as detailed as Tamil.
Both languages mirror each other — same words, same meaning, same depth.
"""


def build_content_day_prompt(
    text: str,
    class_num: int,
    unit: int,
    lesson_title: str,
    type_display: str,
    day_num: int,
    content_days: int,
    total_days: int
) -> str:

    if content_days == 1:
        focus = "the entire lesson"
    elif day_num == 1:
        focus = "introduction and first section of the lesson"
    elif day_num == content_days:
        focus = "final section of the lesson"
    else:
        focus = f"middle section (~{int((day_num/content_days)*100)}% through)"

    next_preview = f"Day {day_num+1}" if day_num < total_days else "the assessment"

    return f"""Generate ONLY Day {day_num} of the lesson plan. Nothing else.
Do NOT include Preamble, General Info, Objectives, or Teaching Aids.
Do NOT generate Day {day_num+1} or any other day.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {type_display}
Content Day {day_num} of {content_days} | Total: {total_days} days
Focus for today: {focus}

═══════════════════════════════════════════════════════
CRITICAL CONTEXT — READ CAREFULLY BEFORE GENERATING
═══════════════════════════════════════════════════════

This lesson plan is for Tamil Nadu government school teachers.
Students are from underprivileged rural backgrounds.
English is their only exposure to the language.
Many teachers are Tamil-medium trained and not fully confident in English.

THE LP MUST DO THREE THINGS:
1. Give teacher a word-for-word English script to deliver to class
2. Give teacher the exact same script in Tamil — so they fully understand
3. Bridge students from Tamil to English through bilingual support

═══════════════════════════════════════════════════════
LANGUAGE RULE — MOST IMPORTANT RULE IN THIS PROMPT
═══════════════════════════════════════════════════════

EVERY teacher instruction must have TWO layers:

LAYER 1 — ENGLISH (detailed, scripted, word for word):
Write exactly what the teacher says to the class.
Minimum 3-4 complete sentences per instruction.
Include: what to do, how to do it, where to look,
how much time, encouragement, what comes next.
Write as if a complete stranger is reading this
and has never taught a class before.

LAYER 2 — TAMIL (exact mirror of Layer 1):
Translate Layer 1 into Tamil — same sentences,
same detail, same encouragement, same instructions.
NOT a summary. NOT a short note.
The Tamil must be as long and detailed as the English.
A teacher reading only the Tamil should get
the complete picture — nothing missing.

EXAMPLE OF CORRECT FORMAT:

Teacher says (English):
"Good morning class. Today we are going to read the
story of Prospero and his daughter Miranda. Before we
start reading, let us remember what we already know
about this story. Yesterday we learned that Prospero
lived on a magical island with his daughter. Today we
will find out what happened when a ship arrived near
their island. Open your textbooks to page 21.
Find the paragraph that begins with the words
'There was an island'. I will read it aloud first,
then we will read it together. Listen carefully."

Tamil (ஆசிரியருக்கு — exact same meaning, same detail):
"காலை வணக்கம் மாணவர்களே. இன்று நாம் Prospero
மற்றும் அவரது மகள் Miranda கதையை படிக்கப் போகிறோம்.
படிக்கத் தொடங்குவதற்கு முன்பு, நாம் ஏற்கனவே
இந்த கதையைப் பற்றி என்ன தெரியும் என்று நினைவுகூர்வோம்.
நேற்று Prospero ஒரு மாயத்தீவில் தன் மகளுடன்
வாழ்ந்தார் என்று தெரிந்தோம். இன்று அவர்களுடைய
தீவிற்கு அருகில் ஒரு கப்பல் வந்தபோது என்ன நடந்தது
என்று தெரிந்துகொள்வோம். உங்கள் பாடப்புத்தகத்தை
பக்கம் 21 திறங்கள். 'There was an island' என்ற
வார்த்தைகளில் தொடங்கும் பத்தியை கண்டுபிடியுங்கள்.
முதலில் நான் சத்தமாக படிக்கிறேன், பிறகு சேர்ந்து
படிப்போம். கவனமாக கேளுங்கள்."

THIS IS THE STANDARD. Every instruction in this LP
must match this level of detail in BOTH languages.

═══════════════════════════════════════════════════════
DAY FORMAT
═══════════════════════════════════════════════════════

<h3 class="day-header">Day {day_num} — [Topic Focus for this day]</h3>
<div class="day-block">

  <div class="time-block">
    <strong>[0–5 min] Warm Up / Review</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 complete sentences — exactly what to say.
    Greet students. Connect to previous day. State today's focus.
    Give specific instruction of what to do first.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — same detail as English above):</strong><br/>
      <p>"[Exact Tamil mirror of the English above — 3-4 complete sentences.
      Same greeting. Same connection to previous day. Same today's focus.
      Same specific instruction. Nothing missing from the English.]"</p>
      <p><em>மாணவர்கள் புரியவில்லை என்றால் சொல்லுங்கள்:</em><br/>
      "[2-3 sentences in Tamil to say to confused students —
      simpler explanation of the same thing]"</p>
    </div>

    <div class="board-work">
      <strong>Board Work:</strong><br/>
      [Write these words with Tamil meanings:]<br/>
      Word 1: [English] — [Tamil meaning]<br/>
      Word 2: [English] — [Tamil meaning]<br/>
      Word 3: [English] — [Tamil meaning]
    </div>

    <p class="teacher-says"><strong>Teacher asks (English):</strong><br/>
    "[2-3 sentences — state the question clearly.
    Tell students to think for 30 seconds before answering.
    Call on a student by row or number.]"</p>

    <div class="tamil-scaffold">
      <em>Tamil version (same question, same instruction):</em><br/>
      "[Exact Tamil mirror of the question and instruction above]"
    </div>

    <p class="student-says"><strong>Expected response:</strong>
    "[Complete sentence answer]"</p>

    <div class="transition">
      <em>Transition (English):</em>
      "[2 sentences — close warm up, introduce main activity]"<br/>
      <em>தமிழில்:</em>
      "[Exact Tamil mirror of transition]"
    </div>
  </div>

  <div class="time-block">
    <strong>[5–15 min] Main Activity — Reading + Vocabulary</strong>

    <div class="vocab-block">
      <strong>Key Vocabulary (write on board before starting):</strong>
      <table>
        <thead>
          <tr><th>Word</th><th>English Meaning</th><th>Tamil பொருள்</th></tr>
        </thead>
        <tbody>
          <tr><td>[word 1]</td><td>[meaning]</td><td>[Tamil]</td></tr>
          <tr><td>[word 2]</td><td>[meaning]</td><td>[Tamil]</td></tr>
          <tr><td>[word 3]</td><td>[meaning]</td><td>[Tamil]</td></tr>
          <tr><td>[word 4]</td><td>[meaning]</td><td>[Tamil]</td></tr>
          <tr><td>[word 5]</td><td>[meaning]</td><td>[Tamil]</td></tr>
        </tbody>
      </table>
    </div>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 complete sentences — explain the activity step by step.
    Tell students exactly what to read, what to look for,
    what to do while reading, how much time they have,
    and what to do when they finish.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — same detail):</strong><br/>
      <p>"[Exact Tamil mirror — 4-5 sentences. Same steps.
      Same time. Same instructions. Nothing shortened.]"</p>
      <p><em>கஷ்டப்படும் மாணவர்களுக்கு:</em><br/>
      "[2-3 Tamil sentences — what to say to struggling students.
      Point to specific words. Give Tamil meaning. Encourage.]"</p>
    </div>

    <p>Student Activity: [Step by step — exactly what students do]</p>
    <p class="student-says"><strong>Expected response:</strong>
    "[Sample complete sentence answer]"</p>

    <div class="transition">
      <em>Transition (English):</em>
      "[2 sentences closing activity, moving to practice]"<br/>
      <em>தமிழில்:</em> "[Exact Tamil mirror]"
    </div>
  </div>

  <div class="time-block">
    <strong>[15–25 min] Student Practice</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 complete sentences — explain practice task in detail.
    State exactly what to write, how many sentences,
    which vocabulary words to use, how much time,
    whether to work alone or in pairs, what to do when done.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — same detail):</strong><br/>
      <p>"[Exact Tamil mirror — 4-5 sentences. Same task.
      Same number of sentences. Same vocabulary words.
      Same time. Same grouping. Nothing missing.]"</p>
    </div>

    <p>Activity: [Think-Pair-Share / Group / Individual]</p>
    <p><strong>Step 1:</strong> [Exact instruction with time]</p>
    <p><strong>Step 2:</strong> [Exact instruction with time]</p>
    <p><strong>Step 3:</strong> [Exact instruction with time]</p>

    <p class="student-says"><strong>Expected output:</strong>
    "[What students produce — example answer]"</p>

    <div class="tamil-scaffold">
      <em>மாணவர்கள் கஷ்டப்படுகிறார்கள் என்றால்:</em><br/>
      "[3 Tamil sentences — what to say to struggling students.
      Give hint. Point to text. Encourage. Never give answer directly.]"
    </div>

    <div class="transition">
      <em>Transition (English):</em>
      "[2 sentences — close practice, move to closure]"<br/>
      <em>தமிழில்:</em> "[Exact Tamil mirror]"
    </div>
  </div>

  <div class="time-block">
    <strong>[25–30 min] Closure + Homework</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — summarize today's key learning.
    Name specific things students learned today.
    Connect to the bigger story. Praise the class genuinely.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — same detail):</strong><br/>
      <p>"[Exact Tamil mirror — 3-4 sentences. Same summary.
      Same specific things. Same connection. Same praise.]"</p>
    </div>

    <div class="board-work">
      <strong>Board Work — Key Words from Today:</strong><br/>
      [word 1] — [Tamil meaning] | [word 2] — [Tamil meaning]<br/>
      [word 3] — [Tamil meaning] | [word 4] — [Tamil meaning]
    </div>

    <p class="teacher-says"><strong>Exit Question (English):</strong><br/>
    "[2-3 sentences — state the question. Tell students to
    write answer in notebook before leaving. Give 2 minutes.]"</p>

    <div class="tamil-scaffold">
      <em>Tamil version:</em>
      "[Exact Tamil mirror of exit question and instruction]"
    </div>

    <p class="student-says"><strong>Expected answer:</strong>
    "[Complete sentence]"</p>

    <div class="homework-block">
      <strong>Homework:</strong>
      <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
      "[3-4 sentences — explain homework clearly.
      State exactly what to write, how many sentences,
      which words to use, when to submit.
      Point to model on board. Say do not copy — use own words.]"</p>

      <div class="tamil-scaffold">
        <strong>ஆசிரியருக்கு (Tamil — same detail):</strong><br/>
        <p>"[Exact Tamil mirror — 3-4 sentences. Same homework.
        Same number of sentences. Same words to use.
        Same submission instruction. Same do-not-copy warning.]"</p>
      </div>

      <div class="board-work">
        <strong>Model Example (write EXACTLY this on board):</strong><br/>
        <p>"[Sentence 1 of model answer — from lesson content]"</p>
        <p>"[Sentence 2 of model answer — from lesson content]"</p>
        <p>"[Sentence 3 of model answer — from lesson content]"</p>
      </div>

      <div class="tamil-scaffold">
        <em>மாணவர்களிடம் சொல்லுங்கள்:</em><br/>
        "இந்த மாதிரி வாக்கியங்களை பார்த்து, உங்கள் சொந்த
        வாக்கியங்கள் எழுதுங்கள். Copy பண்ணாதீர்கள் —
        உங்கள் வார்த்தைகளில் எழுதுங்கள்.
        நாளை class-ல் படிக்கப் போகிறோம்."
      </div>
    </div>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[2-3 sentences — close the day warmly.
    Preview what comes tomorrow. Dismiss class encouragingly.]"</p>

    <div class="tamil-scaffold">
      <em>தமிழில்:</em>
      "[Exact Tamil mirror — same closing, same preview, same encouragement]"
    </div>
  </div>

  <div class="time-block">
    <strong>Differentiated Activities</strong>
    <p><em>Use these based on student ability during practice time:</em></p>

    <table class="diff-table">
      <thead>
        <tr>
          <th>Slow Learners<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
          <th>Average Learners<br/>(சராசரி மாணவர்கள்)</th>
          <th>Advanced Learners<br/>(திறமையான மாணவர்கள்)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            <p><strong>Task:</strong> Fill in the blanks with word bank</p>
            <p><strong>Example:</strong><br/>
            "[Sentence from lesson] _______ (word1 / word2)"<br/>
            "[Sentence from lesson] _______ (word3 / word4)"</p>
            <p><strong>Word Bank:</strong> [4-5 words from today's lesson]</p>
            <p><em>ஆசிரியர் கூடவே உட்கார்ந்து வார்த்தைகளை
            சுட்டிக்காட்டி உதவலாம். தமிழில் விளக்கலாம்.</em></p>
          </td>
          <td>
            <p><strong>Task:</strong> Answer in 2-3 sentences</p>
            <p><strong>Example:</strong><br/>
            "[Character/event] was _______ because _______."<br/>
            "He/She _______ when _______."</p>
          </td>
          <td>
            <p><strong>Task:</strong> Write a paragraph independently</p>
            <p><strong>Prompt:</strong><br/>
            "Describe [specific character or event from today's reading]
            in your own words. Write at least 5 sentences.
            Use the vocabulary words from the board."</p>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

</div>

═══════════════════════════════════════════════════════
ABSOLUTE RULES — NEVER BREAK
═══════════════════════════════════════════════════════
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
✅ EVERY English instruction: minimum 3-4 complete sentences
✅ EVERY Tamil instruction: exact mirror of English — same length, same detail
✅ Vocabulary table: 5 words with Tamil meanings every day
✅ Board Work: always includes Tamil meanings in brackets
✅ Homework: always has 3-sentence model example on board
✅ Differentiation: real example tasks with actual sentences
✅ Tamil must be real Tamil script — not transliteration
✅ Base ALL content on actual lesson text below
✅ Do NOT start Day {day_num+1}

Lesson Text:
---
{text}
---"""


def build_grammar_day_prompt(
    text: str,
    class_num: int,
    unit: int,
    lesson_title: str,
    type_display: str,
    day_num: int,
    grammar_day_num: int,
    grammar_days: int,
    total_days: int
) -> str:

    next_preview = f"Day {day_num+1}" if day_num < total_days else "the assessment"

    return f"""Generate ONLY Day {day_num} (Grammar Day {grammar_day_num} of {grammar_days}).
Do NOT generate any other day.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {type_display}
Day {day_num} of {total_days} total days.

IMPORTANT: Use ACTUAL grammar topic from the lesson text. Do NOT invent.

═══════════════════════════════════════════════════════
LANGUAGE RULE — SAME AS CONTENT DAYS
═══════════════════════════════════════════════════════

EVERY instruction must have TWO equal layers:

LAYER 1 — ENGLISH: Minimum 3-4 complete sentences.
Word for word. What to say, what to write, how much time,
what to do, how to respond to students.

LAYER 2 — TAMIL: Exact mirror of Layer 1.
Same sentences. Same detail. Same length.
Not a summary — a complete translation.

═══════════════════════════════════════════════════════

<h3 class="day-header">Day {day_num} — Grammar: [Exact Topic from Textbook]</h3>
<div class="day-block">

  <div class="time-block">
    <strong>[0–5 min] Review + Grammar Introduction</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — greet students, connect grammar to a
    specific sentence from the lesson, write it on board,
    ask students if they notice anything special about it.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — same greeting, same connection
      to lesson sentence, same board instruction, same question.]"</p>
      <p><em>Grammar rule in Tamil (ஆசிரியர் தெரிந்துகொள்ள):</em><br/>
      "[Explain the full grammar rule in Tamil — 3-4 sentences.
      So the teacher completely understands before explaining to students.]"</p>
    </div>

    <div class="board-work">
      <strong>Board Work:</strong><br/>
      Example sentence: "[sentence from lesson]"<br/>
      Tamil meaning: "[Tamil translation of that sentence]"<br/>
      Grammar focus: "[highlight the grammar point]"
    </div>

    <p class="teacher-says"><strong>Teacher asks (English):</strong><br/>
    "[2-3 sentences — ask students to identify the grammar
    pattern. Give thinking time. Ask by name or row.]"</p>

    <div class="tamil-scaffold">
      <em>Tamil version (exact mirror):</em><br/>
      "[2-3 Tamil sentences — same question, same thinking time,
      same calling instruction]"
    </div>

    <p class="student-says"><strong>Expected response:</strong>
    "[Complete sentence]"</p>
  </div>

  <div class="time-block">
    <strong>[5–15 min] Grammar Explanation + Examples</strong>

    <div class="grammar-rule-block">
      <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
      "[4-5 sentences — explain grammar rule step by step.
      Give 3 examples from the lesson. Write each on board.
      Ask students to repeat the pattern. Check understanding.]"</p>

      <div class="tamil-scaffold">
        <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
        <p>"[4-5 Tamil sentences — same explanation steps,
        same 3 examples, same board instruction,
        same repetition request, same comprehension check.]"</p>
        <p><em>தமிழில் விதி (Grammar Rule in Tamil):</em><br/>
        "[Write the grammar rule in Tamil — clearly and simply.
        Teacher reads this to understand the rule completely.]"</p>
      </div>

      <div class="board-work">
        <strong>Board Work — Rule + 3 Examples from lesson:</strong><br/>
        Rule: [grammar rule in English]<br/>
        தமிழில்: [same rule in Tamil]<br/>
        1. [example sentence] → [Tamil meaning]<br/>
        2. [example sentence] → [Tamil meaning]<br/>
        3. [example sentence] → [Tamil meaning]
      </div>
    </div>

    <p class="teacher-says"><strong>Teacher asks Q1 (English):</strong><br/>
    "[Full question — 2 sentences. State question. Ask student to answer
    in complete sentence.]"</p>
    <div class="tamil-scaffold">
      <em>Tamil version:</em> "[Exact Tamil mirror of Q1]"
    </div>
    <p class="student-says"><strong>Expected:</strong> "[Complete sentence]"</p>

    <p class="teacher-says"><strong>Teacher asks Q2 (English):</strong><br/>
    "[Full question — 2 sentences.]"</p>
    <div class="tamil-scaffold">
      <em>Tamil version:</em> "[Exact Tamil mirror of Q2]"
    </div>
    <p class="student-says"><strong>Expected:</strong> "[Complete sentence]"</p>

    <p class="teacher-says"><strong>Teacher asks Q3 (English):</strong><br/>
    "[Full question — 2 sentences.]"</p>
    <div class="tamil-scaffold">
      <em>Tamil version:</em> "[Exact Tamil mirror of Q3]"
    </div>
    <p class="student-says"><strong>Expected:</strong> "[Complete sentence]"</p>
  </div>

  <div class="time-block">
    <strong>[15–25 min] Student Practice</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 sentences — tell students to open notebook.
    Explain exactly what to write. State how many questions.
    Give time limit. Say you will walk around to check.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[4-5 Tamil sentences — same notebook instruction,
      same explanation, same number, same time, same checking.]"</p>
      <p><em>கஷ்டப்படும் மாணவர்களுக்கு:</em><br/>
      "[3 Tamil sentences — what to say to help struggling students.
      Point to board rule. Give Tamil hint. Encourage gently.]"</p>
    </div>

    <p><strong>Q1:</strong> [question] — <strong>Answer:</strong> [complete sentence]</p>
    <p><strong>Q2:</strong> [question] — <strong>Answer:</strong> [complete sentence]</p>
    <p><strong>Q3:</strong> [question] — <strong>Answer:</strong> [complete sentence]</p>
    <p><strong>Q4:</strong> [question] — <strong>Answer:</strong> [complete sentence]</p>
    <p><strong>Q5:</strong> [question] — <strong>Answer:</strong> [complete sentence]</p>
  </div>

  <div class="time-block">
    <strong>[25–30 min] Closure + Homework</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — summarize the grammar rule in simple words.
    Give one clear final example. Ask exit question.
    Tell students to write answer before leaving.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — same summary, same example,
      same exit question instruction, same writing instruction.]"</p>
    </div>

    <div class="board-work">
      <strong>Board Work:</strong><br/>
      Rule: [grammar rule]<br/>
      தமிழில்: [Tamil rule]<br/>
      Example: [one final clear example sentence]
    </div>

    <p><strong>Exit Question (English):</strong>
    "[Grammar question every student answers in notebook]"</p>
    <div class="tamil-scaffold">
      <em>Tamil version:</em> "[Exact Tamil mirror]"
    </div>
    <p class="student-says"><strong>Expected answer:</strong>
    "[Complete sentence]"</p>

    <div class="homework-block">
      <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
      "[3-4 sentences — explain homework. State exactly how many
      grammar questions. Say use the rule from today.
      Point to board. Say bring tomorrow.]"</p>

      <div class="tamil-scaffold">
        <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
        <p>"[3-4 Tamil sentences — same homework explanation,
        same number, same rule reference, same board pointer,
        same bring-tomorrow instruction.]"</p>
      </div>

      <div class="board-work">
        <strong>Model Example (write on board):</strong><br/>
        Q: [example homework question]<br/>
        A: "[complete model answer using grammar rule]"
      </div>

      <div class="tamil-scaffold">
        <em>மாணவர்களிடம் சொல்லுங்கள்:</em><br/>
        "இந்த மாதிரி பதில் எழுதுங்கள்.
        இன்று கற்ற grammar rule பயன்படுத்துங்கள்.
        Copy பண்ணாதீர்கள் — உங்கள் வார்த்தைகளில் எழுதுங்கள்."
      </div>
    </div>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[2-3 sentences — close day warmly. Preview {next_preview}.
    Dismiss with encouragement.]"</p>

    <div class="tamil-scaffold">
      <em>தமிழில்:</em>
      "[Exact Tamil mirror — same closing, same preview, same encouragement]"
    </div>
  </div>

  <div class="time-block">
    <strong>Differentiated Activities</strong>

    <table class="diff-table">
      <thead>
        <tr>
          <th>Slow Learners<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
          <th>Average Learners<br/>(சராசரி மாணவர்கள்)</th>
          <th>Advanced Learners<br/>(திறமையான மாணவர்கள்)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            <p><strong>Task:</strong> Fill in blanks using grammar rule</p>
            <p><strong>Example:</strong><br/>
            "[sentence with grammar blank] _______ (option1/option2)"</p>
            <p><strong>Word Bank:</strong> [grammar options from lesson]</p>
            <p><em>ஆசிரியர் கூடவே உட்கார்ந்து board-ல் உள்ள
            விதியை சுட்டிக்காட்டி உதவலாம்</em></p>
          </td>
          <td>
            <p><strong>Task:</strong> Write 3 sentences using grammar rule</p>
            <p><strong>Example:</strong><br/>
            "[sentence starter using grammar pattern] _______."<br/>
            "[second starter] _______."</p>
          </td>
          <td>
            <p><strong>Task:</strong> Write a paragraph using grammar rule
            at least 5 times</p>
            <p><strong>Prompt:</strong><br/>
            "Write about [topic from lesson] using [grammar rule]
            correctly in every sentence. No help allowed."</p>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

</div>

ABSOLUTE RULES:
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
✅ EVERY English instruction: minimum 3-4 complete sentences
✅ EVERY Tamil instruction: exact mirror — same length, same detail
✅ Grammar rule explained fully in Tamil for teacher's understanding
✅ Board Work: English + Tamil meaning every time
✅ Homework: model example on board always
✅ Differentiation: real example sentences for each level
✅ Tamil must be real Tamil script — not transliteration
✅ Do NOT start Day {day_num+1}

Lesson Text:
---
{text}
---"""