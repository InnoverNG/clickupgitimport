import os
import json
import time
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
LIST_ID = os.getenv("CLICKUP_LIST_ID")
ISSUES_FILE = os.getenv("ISSUES_FILE", "issues.json")
MAPPING_OUTPUT = "title_to_task_id.json"
DELAY = 0.5

if not API_TOKEN:
    print("Error: CLICKUP_API_TOKEN not set in .env")
    sys.exit(1)
if not LIST_ID:
    print("Error: CLICKUP_LIST_ID not set in .env")
    sys.exit(1)

HEADERS = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json",
}
BASE_URL = "https://api.clickup.com/api/v2"


def load_issues(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("Error: JSON file must contain an array of issues")
        sys.exit(1)
    return data


def create_task(issue):
    url = f"{BASE_URL}/list/{LIST_ID}/task"
    payload = {
        "name": issue["title"],
        "markdown_description": issue.get("body", ""),
        "tags": issue.get("labels", []),
    }
    resp = requests.post(url, json=payload, headers=HEADERS)
    if resp.status_code == 200:
        data = resp.json()
        return data["id"]
    else:
        print(f"  Failed to create task '{issue['title']}': {resp.status_code} {resp.text}")
        return None


def add_dependency(task_id, depends_on_id):
    url = f"{BASE_URL}/task/{task_id}/dependency"
    payload = {"depends_on": depends_on_id}
    resp = requests.post(url, json=payload, headers=HEADERS)
    if resp.status_code == 200:
        print(f"    Linked dependency: {task_id} -> {depends_on_id}")
    else:
        print(f"    Failed to link dependency {task_id} -> {depends_on_id}: {resp.status_code} {resp.text}")


def main():
    issues_file = sys.argv[1] if len(sys.argv) > 1 else ISSUES_FILE

    if not Path(issues_file).exists():
        print(f"Error: File not found: {issues_file}")
        sys.exit(1)

    issues = load_issues(issues_file)
    print(f"Loaded {len(issues)} issues from {issues_file}")

    title_map = {}

    print("\n--- Pass 1: Creating tasks ---")
    for i, issue in enumerate(issues, 1):
        title = issue.get("title")
        if not title:
            print(f"  [{i}] Skipping issue with no title")
            continue

        if title in title_map:
            print(f"  [{i}] Warning: duplicate title '{title}' — skipping")
            continue

        print(f"  [{i}/{len(issues)}] Creating: {title}")
        task_id = create_task(issue)
        if task_id:
            title_map[title] = task_id
            print(f"    -> {task_id}")
        time.sleep(DELAY)

    with open(MAPPING_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(title_map, f, indent=2, ensure_ascii=False)
    print(f"\nMapping saved to {MAPPING_OUTPUT}")

    print("\n--- Pass 2: Linking dependencies ---")
    dep_count = 0
    for i, issue in enumerate(issues, 1):
        title = issue.get("title")
        depends_on = issue.get("depends_on", [])
        if not depends_on:
            continue

        task_id = title_map.get(title)
        if not task_id:
            print(f"  [{i}] Skipping dependencies for '{title}' — task not found in mapping")
            continue

        for dep_title in depends_on:
            dep_id = title_map.get(dep_title)
            if not dep_id:
                print(f"  [{i}] Warning: dependency target '{dep_title}' not found in mapping — skipping")
                continue
            print(f"  [{i}] Linking '{title}' -> '{dep_title}'")
            add_dependency(task_id, dep_id)
            dep_count += 1
            time.sleep(DELAY)

    print(f"\nDone! Created {len(title_map)} tasks, linked {dep_count} dependencies.")


if __name__ == "__main__":
    main()
