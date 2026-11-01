import json
import os
import re
import urllib.request

USERNAME = "tom613951"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def fetch_events():
    url = f"https://api.github.com/users/{USERNAME}/events?per_page=30"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Python-Activity-Updater")
    req.add_header("Accept", "application/vnd.github.v3+json")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def sanitize(text):
    if not text:
        return ""
    # Remove newlines and pipe characters that break Markdown tables
    text = text.replace("\r", " ").replace("\n", " ").replace("|", " - ").strip()
    return re.sub(r"\s+", " ", text)

def format_events_table(events, max_items=6):
    rows = []
    seen = set()

    for e in events:
        etype = e.get("type")
        repo = e.get("repo", {}).get("name")
        if not repo:
            continue
        repo_url = f"https://github.com/{repo}"
        created = e.get("created_at", "")[:10]
        payload = e.get("payload", {})

        key = (etype, repo, created)

        if etype == "PushEvent":
            commits = payload.get("commits", [])
            count = payload.get("size", len(commits))
            if count == 0:
                continue
            msg = sanitize(commits[0].get("message", "")) if commits else ""
            if len(msg) > 60:
                msg = msg[:57] + "..."
            details = f"{count} commit(s): {msg}" if msg else f"{count} commit(s)"
            row = f"| `Push` | [{repo}]({repo_url}) | {details} | `{created}` |"

        elif etype == "ReleaseEvent":
            rel = payload.get("release", {})
            rel_name = sanitize(rel.get("name") or rel.get("tag_name") or "Release")
            rel_url = rel.get("html_url") or f"{repo_url}/releases"
            row = f"| `Release` | [{repo}]({repo_url}) | [{rel_name}]({rel_url}) | `{created}` |"

        elif etype == "PullRequestEvent":
            action = payload.get("action", "opened").capitalize()
            pr = payload.get("pull_request", {})
            pr_title = sanitize(pr.get("title", ""))
            pr_num = pr.get("number", "")
            pr_url = pr.get("html_url", repo_url)
            if len(pr_title) > 60:
                pr_title = pr_title[:57] + "..."
            title_part = f": {pr_title}" if pr_title else ""
            row = f"| `PR {action}` | [{repo}]({repo_url}) | [#{pr_num}{title_part}]({pr_url}) | `{created}` |"

        elif etype == "CreateEvent":
            ref_type = payload.get("ref_type", "resource")
            ref = payload.get("ref")
            if ref_type in ("branch", "tag") and ref:
                ref_clean = sanitize(ref)
                ref_url = f"{repo_url}/tree/{ref}"
                row = f"| `Create {ref_type.capitalize()}` | [{repo}]({repo_url}) | [`{ref_clean}`]({ref_url}) | `{created}` |"
            elif ref_type == "repository":
                row = f"| `Create Repo` | [{repo}]({repo_url}) | [Repository Initialized]({repo_url}) | `{created}` |"
            else:
                continue

        elif etype == "IssueCommentEvent":
            issue = payload.get("issue", {})
            issue_title = sanitize(issue.get("title", ""))
            issue_num = issue.get("number", "")
            issue_url = issue.get("html_url", repo_url)
            if len(issue_title) > 60:
                issue_title = issue_title[:57] + "..."
            row = f"| `Comment` | [{repo}]({repo_url}) | [#{issue_num}: {issue_title}]({issue_url}) | `{created}` |"

        elif etype == "IssuesEvent":
            action = payload.get("action", "opened").capitalize()
            issue = payload.get("issue", {})
            issue_title = sanitize(issue.get("title", ""))
            issue_num = issue.get("number", "")
            issue_url = issue.get("html_url", repo_url)
            if len(issue_title) > 60:
                issue_title = issue_title[:57] + "..."
            row = f"| `Issue {action}` | [{repo}]({repo_url}) | [#{issue_num}: {issue_title}]({issue_url}) | `{created}` |"
        else:
            continue

        if key not in seen:
            seen.add(key)
            rows.append(row)
        if len(rows) >= max_items:
            break

    header = [
        "| Event | Repository | Details | Date |",
        "| :--- | :--- | :--- | :--- |"
    ]
    return header + rows

def update_readme(readme_path, table_rows):
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    replacement = "<!--START_SECTION:activity-->\n" + "\n".join(table_rows) + "\n<!--END_SECTION:activity-->"
    new_content = re.sub(
        r"<!--START_SECTION:activity-->.*?<!--END_SECTION:activity-->",
        replacement,
        content,
        flags=re.DOTALL
    )

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

if __name__ == "__main__":
    events = fetch_events()
    table_lines = format_events_table(events)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    readme_file = os.path.join(root_dir, "README.md")
    
    if os.path.exists(readme_file):
        update_readme(readme_file, table_lines)
        print("Updated README.md with activity table successfully.")
    else:
        print(f"README.md not found at {readme_file}")
