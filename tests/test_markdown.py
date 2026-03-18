from datetime import date

from youtube2blog.markdown import render_markdown
from youtube2blog.models import BlogDraft, Citation, VideoMetadata


def test_render_markdown_has_required_sections() -> None:
    metadata = VideoMetadata(
        video_id="dQw4w9WgXcQ",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="테스트 영상",
        channel="테스트 채널",
        published_date=date(2024, 1, 1),
    )
    draft = BlogDraft(
        title="블로그 제목",
        one_line_summary="요약 문장",
        key_points=["포인트 1", "포인트 2"],
        body_sections=[{"heading": "섹션 A", "content": "핵심 주장 [출처: 00:31]"}],
        closing="마무리 문장",
        citations=[Citation(timestamp="00:31", url=metadata.url + "&t=31s", note="핵심 주장 근거")],
    )

    md = render_markdown(draft, metadata)
    assert "# 블로그 제목" in md
    assert "## 한줄 요약" in md
    assert "## 핵심 포인트" in md
    assert "## 본문" in md
    assert "## 마무리" in md
    assert "## 출처" in md
    assert "[출처: 00:31]" in md

