# Import ClickUp Issues

Import a JSON array of issues into a ClickUp list, with automatic dependency linking.

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**

   Copy `.env.example` to `.env` and fill in your values:

   ```ini
   CLICKUP_API_TOKEN=pt_xxxxx
   CLICKUP_LIST_ID=123456789
   ISSUES_FILE=issues.json
   ```

   - **CLICKUP_API_TOKEN** — Generate at ClickUp > Settings > Apps > API Token
   - **CLICKUP_LIST_ID** — The numeric ID of the target list (found in the URL or via the ClickUp API)
   - **ISSUES_FILE** — Path to your JSON file (default: `issues.json`)

## Input format

JSON file must be a top-level array of issue objects:

```json
[
  {
    "title": "Phase 1a — Registration & Onboarding Flow",
    "labels": ["phase-1", "auth", "backend"],
    "depends_on": ["Phase 1a — Database Foundation & Migrations"],
    "body": "Description in markdown..."
  }
]
```

| Field | Required | Description |
|---|---|---|
| `title` | Yes | Task name in ClickUp |
| `body` | No | Task description (supports markdown) |
| `labels` | No | Array of tag names |
| `depends_on` | No | Array of issue titles this task depends on |

## Usage

```bash
python import_issues.py
```

Or specify a different file:

```bash
python import_issues.py path/to/issues.json
```

## Output

`title_to_task_id.json` — a mapping of each issue title to its ClickUp task ID:

```json
{
  "Phase 1a — Registration & Onboarding Flow": "abc123xyz",
  "Phase 1a — Database Foundation & Migrations": "def456uvw"
}
```

## What it does

**Pass 1** — Creates tasks in the specified ClickUp list with name, markdown description, and tags.

**Pass 2** — Links task dependencies. If Issue A has `depends_on: ["Issue B"]`, a dependency is created so that A is marked as waiting on B.
