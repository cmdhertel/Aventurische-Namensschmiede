from namegen.loader import list_regions, load_region


NEW_REGION_IDS = [
    "kalifat",
    "mittelreich_nordmarken",
    "mittelreich_warunk",
    "mittelreich_weiden",
    "mittelreich_windhag",
    "norbarden",
    "nostria",
    "selem",
    "suedmeer_bukanier",
    "svelltal",
    "thalusien",
    "trollzacker",
    "tulamidenlande",
    "waldmenschen_utulu",
    "zahori",
    "zyklopeninseln",
]


def test_regions_available() -> None:
    regions = list_regions()
    assert regions


def test_region_has_three_letter_abbreviation() -> None:
    data = load_region("bornland")
    assert len(data.meta.abbreviation) == 3


def test_new_regions_are_listed() -> None:
    regions = list_regions()
    for region_id in NEW_REGION_IDS:
        assert region_id in regions


def test_new_regions_load_with_name_material() -> None:
    for region_id in NEW_REGION_IDS:
        data = load_region(region_id)
        assert len(data.meta.abbreviation) == 3
        assert data.origin.region_id == region_id
        assert (
            data.simple.first.male
            or data.simple.first.female
            or data.simple.first.neutral
        )
