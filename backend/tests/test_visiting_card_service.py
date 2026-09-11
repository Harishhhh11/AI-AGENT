import pytest

from app.services.visiting_card_service import VisitingCardService


def test_side_1_is_required():
    service = VisitingCardService(lambda *_: {})
    with pytest.raises(ValueError, match="side_1 is required"):
        service.extract(b"", "image/jpeg")


def test_one_sided_card_only_calls_extractor_once():
    calls = []

    def extractor(data, content_type):
        calls.append((data, content_type))
        return {"name": "రవి కుమార్", "phones": ["9876543210"]}

    result = VisitingCardService(extractor).extract(b"front", "image/jpeg")

    assert len(calls) == 1
    assert result["name"] == "రవి కుమార్"
    assert result["metadata"]["side_1_processed"] is True
    assert result["metadata"]["side_2_processed"] is False


def test_two_sided_card_merges_complementary_information_and_removes_duplicates():
    service = VisitingCardService(lambda *_: {})
    result = service.merge(
        {
            "name": "Ravi Kumar",
            "phones": ["+91 98765 43210"],
            "emails": ["ravi@example.com"],
            "services": ["Web Development"],
        },
        {
            "phones": ["+91-98765-43210", "9123456789"],
            "emails": ["RAVI@example.com", "sales@example.com"],
            "address": "Hyderabad, Telangana",
            "services": ["web development", "AI Automation"],
        },
    )

    assert result["name"] == "Ravi Kumar"
    assert result["address"] == "Hyderabad, Telangana"
    assert result["phones"] == ["+91 98765 43210", "9123456789"]
    assert result["emails"] == ["ravi@example.com", "sales@example.com"]
    assert result["services"] == ["Web Development", "AI Automation"]


def test_telugu_values_are_preserved_and_deduplicated():
    service = VisitingCardService(lambda *_: {})
    result = service.merge(
        {"name": "శ్రీ లక్ష్మీ ఎంటర్ప్రైజెస్", "services": ["డిజిటల్ మార్కెటింగ్"]},
        {"services": ["డిజిటల్ మార్కెటింగ్", "వెబ్ డెవలప్మెంట్"]},
    )

    assert result["name"] == "శ్రీ లక్ష్మీ ఎంటర్ప్రైజెస్"
    assert result["services"] == ["డిజిటల్ మార్కెటింగ్", "వెబ్ డెవలప్మెంట్"]


def test_side_2_requires_content_type_when_supplied():
    service = VisitingCardService(lambda *_: {})
    with pytest.raises(ValueError, match="side_2_content_type"):
        service.extract(b"front", "image/jpeg", b"back")
