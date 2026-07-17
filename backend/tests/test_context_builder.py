from app.services.context_builder import build_chat_context


def test_context_builder_bounds_messages_recaps_and_aggregates_without_history_text():
    messages = [
        {"sender": "user", "text": f"message-{index}"} for index in range(8)
    ]
    recaps = [
        {"title": f"recap-{index}", "summary": f"summary-{index}"}
        for index in range(5)
    ]
    analyses = [
        {
            "emotion": "sadness",
            "domains": ["work"],
            "sleep_substances": ["caffeine"],
            "sleep_hours": 5.5,
        },
        {
            "emotion": "joy",
            "domains": ["relationship"],
            "sleep_substances": [],
            "sleep_hours": None,
        },
        {
            "emotion": "sadness",
            "domains": ["work"],
            "sleep_substances": ["caffeine"],
            "sleep_hours": 6,
        },
    ]

    result = build_chat_context(
        messages=messages,
        recaps=recaps,
        analyses=analyses,
        message_limit=4,
        recap_limit=3,
    )

    assert [row["text"] for row in result["recent_messages"]] == [
        "message-4",
        "message-5",
        "message-6",
        "message-7",
    ]
    assert len(result["recent_recaps"]) == 3
    assert result["emotional_trends"]["emotion_counts"] == {
        "sadness": 2,
        "joy": 1,
    }
    assert result["emotional_trends"]["domain_counts"] == {
        "work": 2,
        "relationship": 1,
    }
    assert result["emotional_trends"]["sleep_substance_counts"] == {"caffeine": 2}
    assert result["emotional_trends"]["reported_sleep_hours"] == [5.5, 6]
    assert "text" not in result["emotional_trends"]


def test_empty_history_returns_explicit_zero_sample_trend():
    result = build_chat_context(
        messages=[], recaps=[], analyses=[], message_limit=12, recap_limit=3
    )

    assert result["emotional_trends"]["sample_size"] == 0
    assert result["recent_messages"] == []
