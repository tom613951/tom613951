import json
import os
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

def generate_activity_svg(events, output_path, width=710, height=150):
    lines = []
    seen = set()
    for e in events:
        etype = e.get("type")
        repo = e.get("repo", {}).get("name")
        if not repo:
            continue
        created = e.get("created_at", "")[:10]
        payload = e.get("payload", {})
        key = (etype, repo, created)

        if etype == "PushEvent":
            commits = payload.get("commits", [])
            count = payload.get("size", len(commits))
            if count == 0:
                continue
            text = f"Pushed {count} commit(s) to {repo} ({created})"
        elif etype == "ReleaseEvent":
            rel = payload.get("release", {})
            rel_name = rel.get("name") or rel.get("tag_name") or "new release"
            text = f"Released {rel_name} in {repo} ({created})"
        elif etype == "PullRequestEvent":
            action = payload.get("action", "opened")
            pr = payload.get("pull_request", {})
            pr_title = pr.get("title", "")
            pr_num = pr.get("number", "")
            title_disp = f": {pr_title}" if pr_title else ""
            text = f"{action.capitalize()} PR #{pr_num}{title_disp} in {repo} ({created})"
        elif etype == "CreateEvent":
            ref_type = payload.get("ref_type")
            ref = payload.get("ref")
            if ref_type == "repository":
                text = f"Created repository {repo} ({created})"
            elif ref_type in ("branch", "tag") and ref:
                text = f"Created {ref_type} `{ref}` in {repo} ({created})"
            else:
                continue
        elif etype == "IssueCommentEvent":
            issue = payload.get("issue", {})
            issue_title = issue.get("title", "")
            issue_num = issue.get("number", "")
            if len(issue_title) > 55:
                issue_title = issue_title[:52] + "..."
            text = f"Commented on #{issue_num}: {issue_title} in {repo} ({created})"
        elif etype == "IssuesEvent":
            action = payload.get("action", "opened")
            issue = payload.get("issue", {})
            issue_title = issue.get("title", "")
            issue_num = issue.get("number", "")
            if len(issue_title) > 55:
                issue_title = issue_title[:52] + "..."
            text = f"{action.capitalize()} issue #{issue_num}: {issue_title} in {repo} ({created})"
        else:
            continue

        if key not in seen:
            seen.add(key)
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            lines.append(text)
        if len(lines) >= 6:
            break

    item_height = 28
    total_items = len(lines)
    all_lines = lines + lines
    scroll_distance = total_items * item_height
    duration = max(14, total_items * 3.5)

    text_nodes = []
    for i, line_text in enumerate(all_lines):
        y = i * item_height + 20
        text_nodes.append(f'<g transform="translate(24, {y})">')
        text_nodes.append('  <circle cx="0" cy="-5" r="3" fill="#7aa2f7" />')
        text_nodes.append(f'  <text x="12" y="0" class="log-text">{line_text}</text>')
        text_nodes.append('</g>')

    content_svg = "\n".join(text_nodes)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <style>
    .bg {{
      fill: #1a1b26;
      stroke: #24283b;
      stroke-width: 1.5px;
      rx: 10px;
    }}
    .header-title {{
      font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
      font-size: 13px;
      font-weight: 700;
      fill: #7aa2f7;
      letter-spacing: 0.5px;
    }}
    .header-sub {{
      font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
      font-size: 11px;
      font-weight: 500;
      fill: #565f89;
    }}
    .log-text {{
      font-family: 'Fira Code', 'Cascadia Code', Consolas, monospace;
      font-size: 12px;
      fill: #c0caf5;
    }}
    .scroll-container {{
      animation: scrollUp {duration}s linear infinite;
    }}
    @keyframes scrollUp {{
      0% {{
        transform: translateY(0);
      }}
      100% {{
        transform: translateY(-{scroll_distance}px);
      }}
    }}
    .scroll-container:hover {{
      animation-play-state: paused;
    }}
  </style>

  <!-- Background Card -->
  <rect width="{width}" height="{height}" class="bg" />

  <!-- Card Header -->
  <g transform="translate(24, 26)">
    <text x="0" y="0" class="header-title">RECENT ACTIVITY STREAM</text>
    <text x="{width - 48}" y="0" class="header-sub" text-anchor="end">LIVE FEED • AUTO-SYNCED</text>
    <line x1="0" y1="12" x2="{width - 48}" y2="12" stroke="#24283b" stroke-width="1" />
  </g>

  <!-- Clip path to isolate scroll window -->
  <defs>
    <clipPath id="feed-clip">
      <rect x="0" y="46" width="{width}" height="{height - 54}" rx="0" />
    </clipPath>
    <linearGradient id="fade-top" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1a1b26" stop-opacity="1" />
      <stop offset="100%" stop-color="#1a1b26" stop-opacity="0" />
    </linearGradient>
    <linearGradient id="fade-bottom" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1a1b26" stop-opacity="0" />
      <stop offset="100%" stop-color="#1a1b26" stop-opacity="1" />
    </linearGradient>
  </defs>

  <!-- Scroll content area -->
  <g clip-path="url(#feed-clip)">
    <g class="scroll-container" transform="translate(0, 50)">
      {content_svg}
    </g>
  </g>

  <!-- Top and Bottom Fade Gradients -->
  <rect x="1" y="44" width="{width - 2}" height="14" fill="url(#fade-top)" pointer-events="none" />
  <rect x="1" y="{height - 20}" width="{width - 2}" height="18" fill="url(#fade-bottom)" rx="10" pointer-events="none" />
</svg>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)

if __name__ == "__main__":
    events = fetch_events()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    output_svg = os.path.join(root_dir, "activity-stream.svg")
    
    generate_activity_svg(events, output_svg)
    print(f"Generated activity-stream.svg successfully at {output_svg}")
