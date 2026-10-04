"""Render notification examples offline; never send a notification."""
from pathlib import Path
import unittest

from jinja2 import Environment, StrictUndefined
import yaml


BLUEPRINT = Path(__file__).resolve().parents[1] / "blueprints/automation/terralyra_ignis/satellite_alert.yaml"


EXAMPLES = {
    "hu": ("Tűz észlelés Home közelében", "Tűz észlelve 42,5km-re a Home ponttól északkeletre"),
    "en": ("Fire detected near Home", "Fire detected 42.5 km northeast of Home"),
    "de": ("Feuer nahe Home erkannt", "Feuer erkannt: 42,5 km nordöstlich von Home"),
    "es": ("Incendio detectado cerca de Home", "Incendio detectado a 42,5 km al noreste de Home"),
    "fr": ("Incendie détecté près de Home", "Incendie détecté à 42,5 km au nord-est de Home"),
    "it": ("Incendio rilevato vicino a Home", "Incendio rilevato a 42,5 km a nord-est di Home"),
}
UNKNOWN_DIRECTION = {
    "hu": "Tűz észlelve 0,0km-re a Home ponttól",
    "en": "Fire detected 0.0 km from Home",
    "de": "Feuer erkannt: 0,0 km von Home",
    "es": "Incendio detectado a 0,0 km de Home",
    "fr": "Incendie détecté à 0,0 km de Home",
    "it": "Incendio rilevato a 0,0 km da Home",
}


class BlueprintLoader(yaml.SafeLoader):
    """Keep input references readable for offline template tests."""


BlueprintLoader.add_constructor("!input", lambda loader, node: loader.construct_scalar(node))


class NotificationTextTests(unittest.TestCase):
    def setUp(self):
        self.config = yaml.load(BLUEPRINT.read_text(), Loader=BlueprintLoader)
        self.env = Environment(undefined=StrictUndefined)

    def render(self, language="hu", places=None):
        if places is None:
            places = [{"location_name": "Home", "distance_km": 42.5, "direction": "NE"}]
        context = {"notification_language": language, "trigger": {
            "platform": "event", "event": {"data": {"alert_locations": places}}}}
        return tuple(self.env.from_string(self.config["actions"][1][key]).render(context)
                     for key in ("title", "message"))

    def test_localized_phone_copy(self):
        for language, expected in EXAMPLES.items():
            with self.subTest(language=language):
                self.assertEqual(self.render(language), expected)

    def test_supported_languages_match_integration(self):
        translations = BLUEPRINT.parents[3] / "custom_components/terralyra_ignis/translations"
        options = self.config["blueprint"]["input"]["language"]["selector"]["select"]["options"]
        self.assertEqual({option["value"] for option in options}, set(EXAMPLES))
        self.assertEqual({path.stem for path in translations.glob("*.json")}, set(EXAMPLES))

    def test_unknown_language_falls_back_to_english(self):
        self.assertEqual(self.render("unsupported"), EXAMPLES["en"])

    def test_french_direction_prepositions(self):
        for direction, phrase in (("E", "à l'est"), ("W", "à l'ouest"),
                                  ("ENE", "à l'est-nord-est"), ("S", "au sud")):
            with self.subTest(direction=direction):
                self.assertEqual(self.render("fr", [{"location_name": "Home",
                    "distance_km": 42.5, "direction": direction}])[1],
                    f"Incendie détecté à 42,5 km {phrase} de Home")

    def test_each_location_uses_its_own_distance_and_direction(self):
        title, message = self.render(places=[
            {"location_name": "Home", "distance_km": 42.5, "direction": "NE"},
            {"location_name": "Cabin", "distance_km": 3.14, "direction": "W"},
        ])
        self.assertEqual(title, "Tűz észlelés Home, Cabin közelében")
        self.assertEqual(message, "Tűz észlelve 42,5km-re a Home ponttól északkeletre. "
                         "Tűz észlelve 3,1km-re a Cabin ponttól nyugatra")

    def test_no_invented_direction(self):
        for direction in (None, "HERE", "unknown"):
            for lang, expected in UNKNOWN_DIRECTION.items():
                with self.subTest(direction=direction, lang=lang):
                    place = {"location_name": "Home", "distance_km": 0}
                    if direction is not None:
                        place["direction"] = direction
                    self.assertEqual(self.render(lang, [place])[1], expected)

    def test_all_compass_points_are_translated(self):
        for direction in "N NNE NE ENE E ESE SE SSE S SSW SW WSW W WNW NW NNW".split():
            for lang in EXAMPLES:
                with self.subTest(direction=direction, lang=lang):
                    text = self.render(lang, [{"location_name": "X", "distance_km": 1,
                                               "direction": direction}])[1]
                    self.assertNotIn(direction, text)
                    without_direction = self.render(lang, [{"location_name": "X",
                                                           "distance_km": 1}])[1]
                    self.assertNotEqual(text, without_direction)

    def test_multiple_locations_and_user_names_in_all_languages(self):
        places = [
            {"location_name": "Árvíz 100%", "distance_km": 42.5, "direction": "NE"},
            {"location_name": "L'été", "distance_km": 3.14, "direction": "W"},
        ]
        for language in EXAMPLES:
            with self.subTest(language=language):
                title, message = self.render(language, places)
                self.assertIn("Árvíz 100%, L'été", title)
                self.assertEqual(message, ". ".join(self.render(language, [place])[1]
                                                   for place in places))
                self.assertIn("3.1" if language == "en" else "3,1", message)

    def test_manual_run_and_empty_event_do_not_notify(self):
        guard = self.env.from_string(self.config["actions"][0]["value_template"])
        for context in ({}, {"trigger": {"platform": "event", "event": {"data": {}}}},
                        {"trigger": {"platform": "state"}}):
            self.assertEqual(guard.render(context), "False")
        self.assertEqual(guard.render(trigger={"platform": "event", "event": {
            "data": {"alert_locations": [{"location_name": "Home"}]}}}), "True")


async def test_home_assistant_blueprint_schema_and_rendering(hass):
    """Validate imported inputs, automation schema and native HA templates."""
    from homeassistant.components.automation.config import (
        AUTOMATION_BLUEPRINT_SCHEMA, PLATFORM_SCHEMA,
    )
    from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
    from homeassistant.helpers.template import Template
    from homeassistant.util.yaml import load_yaml_dict

    blueprint = Blueprint(
        load_yaml_dict(str(BLUEPRINT)), expected_domain="automation",
        schema=AUTOMATION_BLUEPRINT_SCHEMA,
    )
    for language, (expected_title, expected) in EXAMPLES.items():
        inputs = BlueprintInputs(blueprint, {"use_blueprint": {"input": {
            "ignis_entry": "test_entry", "phone": "a" * 32,
            "language": language,
        }}})
        inputs.validate()
        config = PLATFORM_SCHEMA(inputs.async_substitute())
        assert config["triggers"][0]["event_data"] == {"config_entry_id": "test_entry"}
        notification = config["actions"][1]
        context = {"notification_language": language, "trigger": {
            "platform": "event", "event": {"data": {"alert_locations": [
                {"location_name": "Home", "distance_km": 42.5, "direction": "NE"}
            ]}}}}
        title = Template(notification["title"], hass)
        assert title.async_render(context) == expected_title
        message = Template(notification["message"], hass)
        assert message.async_render(context) == expected
        guard = config["actions"][0]["value_template"]
        guard.hass = hass
        assert guard.async_render({}) is False
        assert guard.async_render(context) is True


if __name__ == "__main__":
    unittest.main()
