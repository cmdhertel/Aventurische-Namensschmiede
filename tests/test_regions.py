from namegen.loader import list_regions, load_region


def test_regions_available() -> None:
    regions = list_regions()
    assert regions


def test_region_has_three_letter_abbreviation() -> None:
    data = load_region("bornland")
    assert len(data.meta.abbreviation) == 3
