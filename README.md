# 🚀 Inbox-to-Task Operator
### Turning emails into executable tasks with human-in-the-loop control

---

## 🧠 Overview

Modern work is still routed through inboxes—unstructured, noisy, and inefficient. Every email forces a human to interpret context, prioritize urgency, decide next actions, draft responses, and track follow-ups. This creates unnecessary cognitive overhead and turns the inbox into a place where work gets stuck instead of a place where work gets initiated.

**Inbox-to-Task Operator** rethinks the inbox as a task-generation interface rather than a communication endpoint. Instead of treating emails as isolated messages that must be manually read and answered one by one, the system interprets them as triggers for structured actions. Each incoming email is summarized, classified, converted into a task, routed through a policy layer, and either executed automatically, prepared for human approval, or escalated for direct human handling.

The core goal is simple:

> Move from **message-driven workflows** to **task-driven execution systems**.

This project is intentionally designed as a **CLI-first system**. That keeps the focus on execution, orchestration, and decision-making rather than UI polish. The challenge is not to build a pretty interface. The challenge is to show how ambiguity can be translated into structured work and completed with controlled autonomy.

---

## ⚡ Core Idea

Traditional inbox workflows look like this:

1. Read the email
2. Figure out what it means
3. Decide whether it matters
4. Decide whether it needs a reply
5. Draft a response
6. Remember to follow up later

That loop repeats for every message and introduces both friction and delay.

This system replaces that loop with a task-oriented pipeline:

1. Parse the email
2. Summarize intent
3. Classify urgency and task type
4. Extract the required action
5. Apply a decision policy
6. Execute, draft, or escalate
7. Log the result and continue

Instead of asking, “What does this email say?” the system asks:

> “What work does this email create, and how should that work be handled?”

---

## 🎯 Problem

Inbox-based workflows break down for several reasons:

- **High cognitive overhead**: every message requires interpretation before any action can happen
- **Mixed priority**: newsletters, recruiter emails, follow-ups, and urgent requests all sit in the same queue
- **Implicit actions**: important tasks are hidden inside natural language instead of represented structurally
- **Manual coordination loops**: reply, wait, check back, follow up, repeat
- **Lack of execution flow**: inboxes are good at storing communication, but bad at moving work forward

In practice, this means that low-value work absorbs time while high-value work competes for attention in the same stream.

---

## 💡 Solution

Inbox-to-Task Operator is a CLI-based system that transforms incoming email into an execution pipeline.

For each email, the system:

1. Reads structured input from a JSON inbox
2. Parses sender, subject, and body
3. Summarizes the message using an LLM
4. Classifies:
   - priority
   - intent
   - whether action is required
   - confidence
5. Extracts a structured task
6. Routes the task through a policy engine
7. Chooses one of three modes:
   - **AUTO** for low-risk tasks
   - **DRAFT** for medium-risk tasks requiring approval
   - **ESCALATE** for high-risk or ambiguous tasks
8. Executes the selected action
9. Logs the result and moves on to the next email

This turns the inbox into a system of action rather than a system of accumulation.

---

## 🏗️ End-to-End Architecture

### High-Level System Flow

```text
Incoming Inbox
    ↓
Load Emails
    ↓
For each email:
    ↓
Parse Email
    ↓
Summarize Context
    ↓
Classify Priority + Intent + Action Required
    ↓
Extract Structured Task
    ↓
Policy Engine
    ↓
┌───────────────┬────────────────────┬────────────────────┐
│ AUTO EXECUTE  │ DRAFT FOR APPROVAL │ HUMAN ESCALATION   │
└───────────────┴────────────────────┴────────────────────┘
    ↓
Execute Action / Ask Approval / Escalate
    ↓
Log Result + Store State
```

### Core Design Thesis

The most important architectural choice in this project is that **email is not the end state**. Email is only the entry point. The actual system unit is the **task**, not the message.

That means the pipeline is optimized around:

- intent extraction
- task formation
- action routing
- execution control
- human oversight

---

## 🔁 Detailed Per-Email Execution Flow

Each email moves through a multi-step decision path.

### Step 1: Input Ingestion

The system accepts input from a JSON inbox file.

Example:

```json
{
  "from": "recruiter@startup.com",
  "subject": "Interview Availability",
  "body": "Are you available Thursday for a quick call?"
}
```

At this stage, the system only knows raw content.

---

### Step 2: Email Parsing

The parser extracts:

- sender
- subject
- body
- optional metadata such as timestamps or thread IDs

Output:

```json
{
  "from": "recruiter@startup.com",
  "subject": "Interview Availability",
  "body": "Are you available Thursday for a quick call?"
}
```

This creates a normalized object for downstream processing.

---

### Step 3: Context Summarization

An LLM condenses the email into a short semantic summary.

Example output:

> Recruiter is asking for availability to schedule an interview call.

The purpose of summarization is to reduce noise before classification and task extraction.

---

### Step 4: Classification

The classifier determines:

- **priority**: LOW / MEDIUM / HIGH
- **intent**: scheduling / request / newsletter / information / escalation / follow-up
- **action_required**: true / false
- **confidence**: numeric score

Example output:

```json
{
  "priority": "HIGH",
  "intent": "scheduling",
  "action_required": true,
  "confidence": 0.91
}
```

This is one of the most important layers in the system because it affects downstream behavior.

---

### Step 5: Task Extraction

The system converts the message into a structured task representation.

Example:

```json
{
  "task_type": "reply",
  "action": "provide_availability",
  "context": "job interview scheduling",
  "deadline": null
}
```

This is where the email stops being “a message to read” and becomes “a unit of work to process.”

---

### Step 6: Policy Engine

The policy engine decides how to handle the task.

Example decision logic:

```python
if priority == "LOW" and not action_required:
    mode = "AUTO"
elif priority == "MEDIUM":
    mode = "DRAFT"
else:
    mode = "ESCALATE"
```

This can also be extended with rules such as:

- recruiter emails → generate draft
- newsletters → auto archive
- internal urgent requests → escalate
- low-confidence classification → escalate
- ambiguous or emotionally sensitive messages → escalate

The policy engine is the key control layer because it balances autonomy with trust.

---

### Step 7A: AUTO Mode

Used for low-risk emails that do not require meaningful human judgment.

Examples:

- newsletters
- shipping confirmations
- FYI notifications
- generic announcements

Actions may include:

- archive
- label
- summarize
- ignore with logging

Example output:

```text
Priority: LOW
Action: None
Mode: AUTO
Result: Archived
```

---

### Step 7B: DRAFT Mode

Used for medium-risk emails where an action is clear, but human approval is still valuable.

Examples:

- recruiter outreach
- scheduling coordination
- standard follow-ups
- requests for basic information

The system generates a draft and then prompts the user in the CLI:

```text
Approve and send? (y/n/edit):
```

This shows controlled autonomy. The system handles the heavy lifting but keeps a human decision boundary.

---

### Step 7C: ESCALATE Mode

Used for high-risk, ambiguous, or sensitive emails.

Examples:

- messages from a manager requesting urgent updates
- escalation emails from clients
- emotionally sensitive messages
- legal, financial, or ambiguous communication
- low-confidence classifications

In this path, the system provides:

- summary
- extracted task
- suggested next actions
- optional reply candidates

But the final decision stays fully with the human.

---

### Step 8: Execution

The executor performs the action associated with the selected mode.

In the MVP, actions are simulated and logged:

- send email
- archive email
- mark for follow-up
- escalate to human

This is enough to demonstrate system design without spending time on full Gmail integration.

---

### Step 9: Logging and State

Each processed email produces a logged result.

Example:

```json
{
  "email_id": "001",
  "summary": "Recruiter requesting availability",
  "priority": "HIGH",
  "intent": "scheduling",
  "task": "reply_with_availability",
  "mode": "DRAFT",
  "status": "approved_and_sent"
}
```

This creates traceability and gives the system a lightweight memory of what has already happened.

---

## 🧩 Core Components

### 1. `main.py`
CLI entry point.

Responsibilities:

- load inbox file
- iterate through emails
- call orchestrator
- display output in the terminal

---

### 2. `email_processor.py`
Pipeline orchestrator.

Responsibilities:

- parse emails
- coordinate summarization, classification, extraction, and execution
- keep each step ordered and observable

---

### 3. `llm_utils.py`
Abstraction layer for LLM calls.

Responsibilities:

- summarize email
- classify intent and urgency
- extract structured task
- generate reply drafts

This keeps model interaction separate from orchestration logic.

---

### 4. `classifier.py`
Classification logic.

Responsibilities:

- assign priority
- detect intent
- determine whether action is required
- produce confidence scores

---

### 5. `task_extractor.py`
Task conversion layer.

Responsibilities:

- convert unstructured language into structured task JSON
- preserve context needed for execution
- ensure outputs are machine-readable

---

### 6. `policy_engine.py`
Decision layer.

Responsibilities:

- map classifications to actions
- decide between AUTO, DRAFT, and ESCALATE
- enforce simple risk controls

---

### 7. `executor.py`
Execution layer.

Responsibilities:

- simulate actions
- render CLI approval prompts
- log results

---

## 📊 Decision Model

### Decision Table

| Scenario                    | Priority | Action Required | Confidence | Mode      | Result                          |
|----------------------------|----------|-----------------|------------|-----------|---------------------------------|
| Newsletter                 | LOW      | No              | High       | AUTO      | Archive                         |
| Shipping confirmation      | LOW      | No              | High       | AUTO      | Summarize / Archive             |
| Recruiter outreach         | HIGH     | Yes             | High       | DRAFT     | Generate reply for approval     |
| Scheduling email           | MEDIUM   | Yes             | High       | DRAFT     | Draft + human approval          |
| Manager escalation         | HIGH     | Yes             | High       | ESCALATE  | Human review                    |
| Ambiguous message          | MEDIUM   | Unclear         | Low        | ESCALATE  | Human review                    |
| Legal / financial message  | HIGH     | Yes             | Any        | ESCALATE  | Human review                    |

### Risk-Based Autonomy

The system is not designed to maximize automation at all costs. It is designed to maximize **useful execution under supervision**.

That means the key tradeoff is:

> automate aggressively where risk is low, and slow down where judgment matters.

---

## 🖥️ CLI Interaction Flow

### Run Command

```bash
python main.py sample_inbox.json
```

### Example CLI Session

```text
📥 Processing 3 emails...

--------------------------------------------------
Email 1:
From: recruiter@startup.com
Subject: Backend Engineer Role

🧠 Summary:
Recruiter asking for availability for a call.

⚡ Priority: HIGH
📌 Intent: scheduling
🛠 Task: provide_availability
🤖 Mode: DRAFT

✉️ Draft Reply:
Hi, thanks for reaching out. I'm available Thursday between 2–5 PM PST and Friday between 10 AM–1 PM PST. Looking forward to speaking.

👉 Approve and send? (y/n/edit): y
✅ Email sent

--------------------------------------------------
Email 2:
From: newsletter@company.com
Subject: Weekly Product Update

🧠 Summary:
Weekly newsletter with product updates.

⚡ Priority: LOW
📌 Intent: newsletter
🛠 Task: none
🤖 Mode: AUTO

✅ Archived

--------------------------------------------------
Email 3:
From: manager@company.com
Subject: Need project update ASAP

🧠 Summary:
Manager requesting urgent project status and timeline clarity.

⚡ Priority: HIGH
📌 Intent: escalation
🛠 Task: prepare_status_update
🤖 Mode: ESCALATE

⚠️ Escalated to human with summary and suggested reply
```

---

## 📂 Project Structure

```text
inbox-operator/
│── main.py
│── email_processor.py
│── llm_utils.py
│── classifier.py
│── task_extractor.py
│── policy_engine.py
│── executor.py
│── sample_inbox.json
│── README.md
```

---

## 🧪 Example Input

### `sample_inbox.json`

```json
[
  {
    "id": "001",
    "from": "recruiter@startup.com",
    "subject": "Interview Availability",
    "body": "Hi Shivam, are you available Thursday for a quick call to discuss the role?"
  },
  {
    "id": "002",
    "from": "newsletter@company.com",
    "subject": "Weekly Product Update",
    "body": "Here’s everything we shipped this week."
  },
  {
    "id": "003",
    "from": "manager@company.com",
    "subject": "Need project update ASAP",
    "body": "Can you send me a clear project update and revised ETA today?"
  }
]
```

---

## 🧪 Example Scenario Flows

### Flow 1: Newsletter → AUTO

**Input Email**
- From: newsletter@company.com
- Subject: Weekly Update

**System Reasoning**
- intent = newsletter
- action_required = false
- priority = LOW
- confidence = high

**Policy Outcome**
- mode = AUTO

**Execution**
- archive email
- log action

**Result**
- no human involvement required

---

### Flow 2: Recruiter Outreach → DRAFT

**Input Email**
- From: recruiter@startup.com
- Subject: Availability for interview

**System Reasoning**
- intent = scheduling
- action_required = true
- priority = HIGH
- confidence = high

**Policy Outcome**
- mode = DRAFT

**Execution**
- generate reply draft
- display to user
- ask approval
- send if approved

**Result**
- faster response while keeping human control

---

### Flow 3: Urgent Internal Request → ESCALATE

**Input Email**
- From: manager@company.com
- Subject: Need update today

**System Reasoning**
- intent = escalation
- action_required = true
- priority = HIGH
- confidence = medium/high

**Policy Outcome**
- mode = ESCALATE

**Execution**
- summarize situation
- present task and suggested response
- wait for human action

**Result**
- sensitive communication stays human-led

---

### Flow 4: Low-Confidence Ambiguous Email → ESCALATE

**Input Email**
- mixed language, vague ask, unclear next step

**System Reasoning**
- confidence < threshold
- task unclear

**Policy Outcome**
- mode = ESCALATE

**Execution**
- present summary
- ask human to decide

**Result**
- avoids unsafe automation

---

## 🔄 Feedback and Failure Handling

A useful operator should not only act when things are easy. It should also handle uncertainty and errors gracefully.

### Failure and Retry Rules

- If classification confidence is below threshold → escalate
- If draft generation fails → use fallback template
- If task extraction is unclear → escalate
- If execution fails → retry once, then log error
- If user rejects draft → allow edit or discard
- If a follow-up is needed → create a pending task

### Example Fallback Draft

```text
Hi, thanks for your email. I’ve reviewed your message and will get back to you shortly.
```

This is simple, safe, and useful when a full contextual draft is unavailable.

---

## 🧠 Key Design Principles

### 1. Task-First Thinking

The core unit of the system is the task, not the email.

That shift matters because messages are not inherently executable, but tasks are.

---

### 2. Controlled Autonomy

Automation is useful only when paired with trust.

This project deliberately uses a tiered autonomy model instead of “auto-reply to everything.”

---

### 3. Human-in-the-Loop

Human approval is treated as a feature, not a limitation.

It is what makes the system practical for real workflows where mistakes carry cost.

---

### 4. Outcome-Oriented Design

The system is evaluated by:

- how much work it removes from the inbox
- how accurately it routes tasks
- how safely it automates
- how clearly it exposes human decision points

---

### 5. CLI-First Execution

A CLI was chosen intentionally because it keeps the scope focused on orchestration and execution.

The value of the project is not the interface. The value is the pipeline.

---

## ⚙️ Tech Stack

- **Python** for orchestration and CLI execution
- **LLM API** (OpenAI or local model) for:
  - summarization
  - classification
  - task extraction
  - draft generation
- **JSON** for inbox input and lightweight state
- **CLI** for human approval loop and execution visibility

---

## 🚧 Scope and Limitations

This MVP intentionally does **not** include:

- Gmail / Outlook integration
- persistent database storage
- web UI
- full auth / permissions system
- parallel multi-threaded execution
- multi-user support

These omissions are intentional. The goal is to validate the **workflow architecture**, not to spend the challenge on infrastructure.

---

## 🚀 Future Improvements

The system can be extended in several directions:

### 1. Email Integration
Connect to Gmail or Outlook APIs for live inbox processing.

### 2. Persistent Task Store
Track tasks across sessions with SQLite or Postgres.

### 3. Follow-Up Scheduler
Automatically create reminders for unanswered threads.

### 4. Calendar Integration
Respond to scheduling emails by checking real availability.

### 5. Better Risk Modeling
Use confidence thresholds, sender trust, and intent sensitivity to improve policy decisions.

### 6. Multi-Agent Workflow
Split the pipeline into separate agents for:
- summarization
- classification
- execution
- follow-up management

### 7. Learning from Edits
Track how humans modify drafts to improve future suggestions.

---

## 📈 Why This Matters

This project reflects a broader shift in how work gets done.

| Traditional Inbox Workflow | Task-Oriented Operator Workflow |
|---------------------------|----------------------------------|
| Message is the endpoint   | Message is the trigger           |
| Human interprets every email | System interprets and routes work |
| Manual prioritization     | Automated classification         |
| Manual replies            | Drafted or executed actions      |
| Work stays in inbox       | Work moves into execution flow   |

The inbox should not be the place where work sits. It should be the place where work begins.

---

## 🧩 Why This Fits the Challenge

This project is aligned with the broader idea of moving from communication-first systems to execution-first systems.

It demonstrates:

- converting ambiguity into structure
- designing task-oriented workflows
- balancing autonomy with control
- using AI as an operator rather than just a text generator
- focusing on outcomes, not just components

It is not just an email assistant. It is an **inbox-native execution operator**.

---

## 🧨 Final Takeaway

> The inbox should not be where work happens.  
> It should be where work begins.
