from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict

from .twitter import Conversation, Post


def _clean(text: str) -> str:
    return " ".join(text.replace("\r", " ").replace("\n", " ").split())


def render_markdown(conversation: Conversation) -> str:
    children: dict[str, list[Post]] = defaultdict(list)
    known = {conversation.root.id, *(p.id for p in conversation.replies)}
    for post in conversation.replies:
        children[post.parent_id if post.parent_id in known else conversation.root.id].append(post)
    for posts in children.values():
        posts.sort(key=lambda p: (p.created_at, int(p.id)))
    status = "complete within the selected X search endpoint" if conversation.complete else "truncated by configured safety limit"
    lines = [
        "# X conversation tree", "",
        f"- Root: {conversation.root.url}", f"- Replies collected: {len(conversation.replies)}",
        f"- Collector: `{conversation.endpoint}` ({conversation.requests} reply request(s))", f"- Collection status: {status}", "",
    ]

    def visit(post: Post, depth: int) -> None:
        lines.extend([
            f"{'  ' * depth}- **@{post.username}** ({post.name}) — {post.created_at}",
            f"{'  ' * depth}  - ID: `{post.id}` | [source]({post.url})",
            f"{'  ' * depth}  - {_clean(post.text)}",
        ])
        for child in children.get(post.id, []):
            visit(child, depth + 1)

    visit(conversation.root, 0)
    return "\n".join(lines) + "\n"


def render_json(conversation: Conversation) -> str:
    posts = [conversation.root, *conversation.replies]
    payload = {
        "metadata": {"complete": conversation.complete, "collector": conversation.endpoint, "reply_requests": conversation.requests},
        "root_id": conversation.root.id,
        "posts": {p.id: {**asdict(p), "url": p.url} for p in posts},
        "edges": [{"parent_id": p.parent_id, "child_id": p.id} for p in conversation.replies],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
