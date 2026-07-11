from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from twscrape import API

STATUS_RE = re.compile(r"https?://(?:www\.)?(?:twitter\.com|x\.com)/[^/?#]+/status/(\d+)", re.I)


class XApiError(RuntimeError):
    pass


def extract_post_id(value: str) -> str:
    match = STATUS_RE.search(value.strip())
    if not match:
        raise ValueError("Send a full twitter.com or x.com status URL")
    return match.group(1)


@dataclass
class Post:
    id: str
    text: str
    author_id: str
    username: str
    name: str
    created_at: str
    parent_id: str | None = None
    metrics: dict[str, int] = field(default_factory=dict)

    @property
    def url(self) -> str:
        return f"https://x.com/{self.username}/status/{self.id}"


@dataclass
class Conversation:
    root: Post
    replies: list[Post]
    complete: bool
    endpoint: str
    pages: int


class XClient:
    """Free collector using an authenticated X web session via twscrape."""

    account_name = "telegram_collector"

    def __init__(self, auth_token: str, ct0: str, max_replies: int = 5000, db_path: str = "/tmp/accounts.db"):
        self.auth_token, self.ct0, self.max_replies = auth_token, ct0, max_replies
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.api = API(db_path)
        self._initialized = False

    async def _initialize(self) -> None:
        if self._initialized:
            return
        cookies = {"auth_token": self.auth_token, "ct0": self.ct0}
        existing = await self.api.pool.get_account(self.account_name)
        if existing is None:
            await self.api.pool.add_account_cookies(
                self.account_name, f"auth_token={self.auth_token}; ct0={self.ct0}"
            )
        elif existing.cookies != cookies:
            # Allow cookie rotation through the TrueNAS environment without
            # requiring manual deletion of the persistent SQLite database.
            existing.cookies = cookies
            existing.active = True
            existing.error_msg = None
            existing.locks = {}
            await self.api.pool.save(existing)
        self._initialized = True

    async def close(self) -> None:
        return None

    @staticmethod
    def _post(tweet) -> Post:
        return Post(
            id=str(tweet.id), text=tweet.rawContent, author_id=str(tweet.user.id),
            username=tweet.user.username, name=tweet.user.displayname,
            created_at=tweet.date.isoformat(),
            parent_id=str(tweet.inReplyToTweetId) if tweet.inReplyToTweetId else None,
            metrics={
                "reply_count": tweet.replyCount, "retweet_count": tweet.retweetCount,
                "like_count": tweet.likeCount, "quote_count": tweet.quoteCount,
            },
        )

    async def conversation(self, post_id: str) -> Conversation:
        await self._initialize()
        try:
            raw_root = await self.api.tweet_details(int(post_id))
            if raw_root is None:
                raise XApiError("X did not return that post; it may be deleted, private, or restricted")
            root = self._post(raw_root)
            found: dict[str, Post] = {}
            reached_limit = False
            # tweet_thread exposes nested replies for the conversation root. For a
            # supplied sub-reply, collect the conversation and filter its descendants.
            conversation_root = int(raw_root.conversationId)
            async for raw in self.api.tweet_thread(conversation_root, limit=self.max_replies + 1):
                post = self._post(raw)
                if post.id != root.id:
                    found[post.id] = post
                if len(found) > self.max_replies:
                    reached_limit = True
                    break
        except XApiError:
            raise
        except Exception as exc:
            raise XApiError(f"free X web collector failed: {exc}") from exc

        descendants: dict[str, Post] = {}
        frontier = {root.id}
        remaining = found.copy()
        while frontier:
            next_frontier: set[str] = set()
            for key, post in list(remaining.items()):
                if post.parent_id in frontier:
                    descendants[key] = remaining.pop(key)
                    next_frontier.add(key)
            frontier = next_frontier
        ordered = sorted(descendants.values(), key=lambda p: (p.created_at, int(p.id)))
        return Conversation(root, ordered, not reached_limit, "free authenticated web session", 0)
