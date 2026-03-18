from datetime import date

from youtube2blog.config import AppConfig
from youtube2blog.errors import TranscriptUnavailableError
from youtube2blog.models import BlogDraft, Citation, TranscriptSegment, VideoMetadata
from youtube2blog.pipeline import build_markdown_from_url


def test_pipeline_uses_stt_fallback(monkeypatch) -> None:
    config = AppConfig(
        openai_api_key="test-key",
        openai_model="gpt-4.1-mini",
        openai_stt_model="gpt-4o-mini-transcribe",
        openai_temperature=0.2,
        max_segments=50,
        language="ko",
    )
    metadata = VideoMetadata(
        video_id="dQw4w9WgXcQ",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="테스트 영상",
        channel="테스트 채널",
        published_date=date(2024, 1, 1),
    )

    monkeypatch.setattr("youtube2blog.pipeline.fetch_metadata", lambda url: metadata)

    def _raise_transcript(url, language):
        raise TranscriptUnavailableError("no transcript")

    monkeypatch.setattr("youtube2blog.pipeline.fetch_transcript", _raise_transcript)
    monkeypatch.setattr(
        "youtube2blog.pipeline.transcribe_audio",
        lambda url, client, model: [TranscriptSegment(start_ts=0.0, end_ts=1.0, text="테스트 대본")],
    )
    monkeypatch.setattr(
        "youtube2blog.pipeline.generate_post",
        lambda **kwargs: BlogDraft(
            title="생성 글",
            one_line_summary="요약",
            key_points=["포인트"],
            body_sections=[{"heading": "요점", "content": "내용 [출처: 00:00]"}],
            closing="끝",
            citations=[Citation(timestamp="00:00", url=metadata.url, note="근거")],
        ),
    )

    markdown, resolved_metadata = build_markdown_from_url(metadata.url, config=config)
    assert "생성 글" in markdown
    assert "## 출처" in markdown
    assert resolved_metadata.video_id == "dQw4w9WgXcQ"
