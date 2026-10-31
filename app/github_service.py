import base64
import uuid
import httpx
from .config import settings

API = "https://api.github.com"

class GitHubError(RuntimeError):
    pass

def _headers():
    if not settings.github_token:
        raise GitHubError("GitHub is not configured. Add GITHUB_TOKEN to environment.")
    return {"Authorization": f"Bearer {settings.github_token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

async def list_repositories(username: str | None = None):
    url = f"{API}/user/repos" if not username else f"{API}/users/{username}/repos"
    async with httpx.AsyncClient(timeout=25) as client:
        r = await client.get(url, headers=_headers(), params={"per_page": 50, "sort": "updated"})
    if r.status_code >= 400:
        raise GitHubError(f"GitHub API error {r.status_code}: {r.text[:400]}")
    return [{"full_name": x["full_name"], "private": x["private"], "default_branch": x["default_branch"], "html_url": x["html_url"], "description": x.get("description")} for x in r.json()]

async def get_tree(owner: str, repo: str):
    async with httpx.AsyncClient(timeout=25) as client:
        meta = await client.get(f"{API}/repos/{owner}/{repo}", headers=_headers())
        if meta.status_code >= 400:
            raise GitHubError(f"Repo lookup failed: {meta.text[:300]}")
        branch = meta.json()["default_branch"]
        tree = await client.get(f"{API}/repos/{owner}/{repo}/git/trees/{branch}", headers=_headers(), params={"recursive": "1"})
    if tree.status_code >= 400:
        raise GitHubError(f"Tree lookup failed: {tree.text[:300]}")
    return {"default_branch": branch, "files": [x["path"] for x in tree.json().get("tree", []) if x["type"] == "blob"][:500]}

async def read_file(owner: str, repo: str, path: str):
    async with httpx.AsyncClient(timeout=25) as client:
        r = await client.get(f"{API}/repos/{owner}/{repo}/contents/{path}", headers=_headers())
    if r.status_code >= 400:
        raise GitHubError(f"File lookup failed: {r.text[:300]}")
    data = r.json()
    if data.get("encoding") != "base64":
        raise GitHubError("Unsupported GitHub file encoding.")
    return {"path": path, "content": base64.b64decode(data["content"]).decode("utf-8", errors="replace")[:20000], "sha": data["sha"]}

async def create_file_pr(owner: str, repo: str, path: str, content: str, commit_message: str, pr_title: str, pr_body: str):
    headers = _headers()
    async with httpx.AsyncClient(timeout=40) as client:
        meta = await client.get(f"{API}/repos/{owner}/{repo}", headers=headers)
        if meta.status_code >= 400:
            raise GitHubError(f"Repo lookup failed: {meta.text[:300]}")
        base = meta.json()["default_branch"]
        ref = await client.get(f"{API}/repos/{owner}/{repo}/git/ref/heads/{base}", headers=headers)
        if ref.status_code >= 400:
            raise GitHubError(f"Base branch lookup failed: {ref.text[:300]}")
        branch = "aliasgar-ai/" + uuid.uuid4().hex[:10]
        created = await client.post(f"{API}/repos/{owner}/{repo}/git/refs", headers=headers, json={"ref": f"refs/heads/{branch}", "sha": ref.json()["object"]["sha"]})
        if created.status_code >= 400:
            raise GitHubError(f"Branch creation failed: {created.text[:300]}")
        encoded = base64.b64encode(content.encode()).decode()
        file_url = f"{API}/repos/{owner}/{repo}/contents/{path}"
        existing = await client.get(file_url, headers=headers, params={"ref": branch})
        commit_payload = {"message": commit_message, "content": encoded, "branch": branch}
        if existing.status_code == 200:
            commit_payload["sha"] = existing.json()["sha"]
        elif existing.status_code != 404:
            raise GitHubError(f"Could not inspect target file: {existing.text[:300]}")
        commit = await client.put(file_url, headers=headers, json=commit_payload)
        if commit.status_code >= 400:
            raise GitHubError(f"Commit failed; branch {branch} may remain: {commit.text[:300]}")
        pr = await client.post(f"{API}/repos/{owner}/{repo}/pulls", headers=headers, json={"title": pr_title, "body": pr_body, "head": branch, "base": base, "draft": True})
        if pr.status_code >= 400:
            raise GitHubError(f"Commit succeeded on {branch}, but PR failed: {pr.text[:300]}")
        return {"branch": branch, "commit_url": commit.json().get("commit", {}).get("html_url"), "pull_request_url": pr.json().get("html_url")}
