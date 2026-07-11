from truenas_bot.render import render_json, render_markdown
import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from truenas_bot.twitter import Conversation, Post, XClient, extract_post_id


def p(id, parent=None, text=None):
    return Post(id=str(id), text=text or f"post {id}", author_id=str(id), username=f"u{id}", name=f"User {id}", created_at=f"2026-01-01T00:00:0{id}Z", parent_id=str(parent) if parent else None)


def test_extract_post_id_ignores_tracking_query():
    assert extract_post_id("https://twitter.com/user/status/2075895007509176382?t=x&s=19") == "2075895007509176382"
    assert extract_post_id("see https://x.com/user/status/123 now") == "123"


def test_markdown_reconstructs_tree_even_if_input_is_unsorted():
    c = Conversation(p(1), [p(3, 2), p(2, 1), p(4, 1)], True, "all", 1)
    md = render_markdown(c)
    assert md.index("`2`") < md.index("`3`") < md.index("`4`")
    assert "    - **@u3**" in md


def test_orphan_is_attached_to_root_and_json_has_edges():
    c = Conversation(p(1), [p(2, 999)], False, "recent", 2)
    assert "  - **@u2**" in render_markdown(c)
    assert '"parent_id": "999"' in render_json(c)


def test_extract_post_id_rejects_non_status_url():
    try:
        extract_post_id("https://x.com/user")
    except ValueError as exc:
        assert "status URL" in str(exc)
    else:
        raise AssertionError("invalid URL was accepted")


def test_free_collector_filters_siblings_from_subtree(tmp_path):
    def raw(id, parent, conversation=1):
        user = SimpleNamespace(id=id, username=f"u{id}", displayname=f"User {id}")
        return SimpleNamespace(
            id=id, rawContent=f"post {id}", user=user, date=datetime.now(timezone.utc),
            inReplyToTweetId=parent, conversationId=conversation, replyCount=0,
            retweetCount=0, likeCount=0, quoteCount=0,
        )

    class FakeAPI:
        async def tweet_details(self, _):
            return raw(2, 1)

        async def tweet_thread(self, *_args, **_kwargs):
            for item in (raw(2, 1), raw(3, 2), raw(4, 1), raw(5, 3)):
                yield item

    async def run():
        client = XClient("a", "c", db_path=str(tmp_path / "accounts.db"))
        client.api = FakeAPI()
        client._initialized = True
        result = await client.conversation("2")
        assert [x.id for x in result.replies] == ["3", "5"]

    asyncio.run(run())
