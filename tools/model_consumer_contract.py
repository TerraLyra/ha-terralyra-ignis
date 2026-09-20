"""Exercise observation consumer behavior in either model namespace.

This file is a repository check, not part of the distributed model package.
"""
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import datetime, timedelta, timezone
import unittest


def consumer_suite(models):
    """Run the same contract against bundled or separately installed classes."""
    class ConsumerContract(unittest.TestCase):
        def observation(self, **changes):
            values = dict(
                provider="synthetic-feed", satellite="synthetic-satellite",
                product="synthetic-product",
                timestamp=datetime(2026, 1, 15, 12, 30, 0, 123456,
                                   tzinfo=timezone(timedelta(hours=11))),
                latitude=0.0, longitude=-179.9, frp_mw=0.0,
                frp_uncertainty_mw=0.0, confidence=0.0, classification=0,
                quality="0", fire_temperature_k=None, fire_area_km2=0.0,
                temporal_filtered=False, source_resolution_km=0.375,
                source_detection_id="000123", source_family="shared-algorithm",
            )
            values.update(changes)
            return models.FireDetection(**values)

        def test_observation_record_retains_distinctions(self):
            record = asdict(self.observation())
            self.assertIs(record["temporal_filtered"], False)
            self.assertIsNone(record["fire_temperature_k"])
            self.assertEqual(record["frp_mw"], 0.0)
            self.assertEqual(record["confidence"], 0.0)
            self.assertIs(type(record["classification"]), int)
            self.assertEqual(record["quality"], "0")
            self.assertEqual(record["source_detection_id"], "000123")
            self.assertEqual(record["source_family"], "shared-algorithm")
            self.assertEqual(record["timestamp"].isoformat(),
                             "2026-01-15T12:30:00.123456+11:00")
            self.assertEqual(models.FireDetection(**record), self.observation())

        def test_copy_does_not_change_original_or_family(self):
            original = self.observation()
            updated = replace(original, frp_mw=5.0, quality=0)
            self.assertEqual(original.frp_mw, 0.0)
            self.assertEqual(original.quality, "0")
            self.assertEqual(updated.frp_mw, 5.0)
            self.assertEqual(updated.source_family, original.source_family)
            with self.assertRaises(FrozenInstanceError):
                original.frp_mw = 5.0

        def test_snapshot_separates_receipt_from_source_time(self):
            detection = self.observation()
            source_time = detection.timestamp
            received = source_time.astimezone(timezone.utc) + timedelta(hours=2)
            snapshot = models.ProviderSnapshot(
                detection.provider, detection.satellite, detection.product,
                source_time, received, models.ProviderStatus.DELAYED,
                "https://example.invalid/source", "synthetic", (detection,),
            )
            self.assertIs(snapshot.detections[0], detection)
            self.assertEqual(snapshot.received_timestamp - snapshot.product_timestamp,
                             timedelta(hours=2))
            self.assertEqual(snapshot.status.value, "delayed")
            # A new empty snapshot must not mutate the retained prior snapshot.
            empty = replace(snapshot, detections=(), status=models.ProviderStatus.NO_PRODUCT)
            self.assertEqual(empty.detections, ())
            self.assertEqual(snapshot.detections, (detection,))
            self.assertEqual(snapshot.status, models.ProviderStatus.DELAYED)

    return unittest.defaultTestLoader.loadTestsFromTestCase(ConsumerContract)


if __name__ == "__main__":
    import sys
    import terralyra_ignis_models

    result = unittest.TextTestRunner(verbosity=2).run(consumer_suite(terralyra_ignis_models))
    forbidden = any(name == "homeassistant" or name.startswith("homeassistant.")
                    or name == "custom_components" or name.startswith("custom_components.")
                    for name in sys.modules)
    if forbidden:
        raise SystemExit("Standalone model check unexpectedly imported the HA runtime")
    raise SystemExit(0 if result.wasSuccessful() else 1)
