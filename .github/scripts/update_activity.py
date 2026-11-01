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

def format_events(events, max_items=6):
    lines = []
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
            line = f"- Pushed {count} commit(s) to [{repo}]({repo_url}) ({created})"
        elif etype == "ReleaseEvent":
            rel = payload.get("release", {})
            rel_name = rel.get("name") or rel.get("tag_name") or "new release"
            rel_url = rel.get("html_url") or f"{repo_url}/releases"
            line = f"- Released [{rel_name}]({rel_url}) in [{repo}]({repo_url}) ({created})"
        elif etype == "PullRequestEvent":
            action = payload.get("action", "opened")
            pr = payload.get("pull_request", {})
            pr_title = pr.get("title", "")
            pr_num = pr.get("number", "")
            pr_url = pr.get("html_url", repo_url)
            title_disp = f": {pr_title}" if pr_title else ""
            line = f"- {action.capitalize()} PR [#{pr_num}{title_disp}]({pr_url}) in [{repo}]({repo_url}) ({created})"
        elif etype == "CreateEvent":
            ref_type = payload.get("ref_type")
            ref = payload.get("ref")
            if ref_type == "repository":
                line = f"- Created repository [{repo}]({repo_url}) ({created})"
            elif ref_type in ("branch", "tag") and ref:
                line = f"- Created {ref_type} `{ref}` in [{repo}]({repo_url}) ({created})"
            else:
                continue
        elif etype == "IssueCommentEvent":
            issue = payload.get("issue", {})
            issue_title = issue.get("title", "")
            issue_num = issue.get("number", "")
            issue_url = issue.get("html_url", repo_url)
            if len(issue_title) > 60:
                issue_title = issue_title[:57] + "..."
            line = f"- Commented on issue [#{issue_num}: {issue_title}]({issue_url}) in [{repo}]({repo_url}) ({created})"
        elif etype == "IssuesEvent":
            action = payload.get("action", "opened")
            issue = payload.get("issue", {})
            issue_title = issue.get("title", "")
            issue_num = issue.get("number", "")
            issue_url = issue.get("html_url", repo_url)
            if len(issue_title) > 60:
                issue_title = issue_title[:57] + "..."
            line = f"- {action.capitalize()} issue [#{issue_num}: {issue_title}]({issue_url}) in [{repo}]({repo_url}) ({created})"
        else:
            continue

        if key not in seen:
            seen.add(key)
            lines.append(line)
        if len(lines) >= max_items:
            break

    return lines

def update_readme(readme_path, activity_lines):
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    replacement = "<!--START_SECTION:activity-->\n" + "\n".join(activity_lines) + "\n<!--END_SECTION:activity-->"
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
    activity = format_events(events)
    # Target README.md at repo root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    readme_file = os.path.join(root_dir, "README.md")
    
    if os.path.exists(readme_file):
        update_readme(readme_file, activity)
        print("Updated README.md successfully.")
    else:
        print(f"README.md not found at {readme_file}")
