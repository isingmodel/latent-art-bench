import base64
import io

from PIL import Image

from latent_art_bench.painter_feature_generation_v2.assessment_diagnostics import inspect_payload
from latent_art_bench.painter_feature_generation_v2.model_assessment import request_frame


def test_actual_size_and_reported_quality_are_not_silently_accepted():
    image = io.BytesIO()
    Image.new("RGB", (1254, 1254), "white").save(image, format="PNG")
    payload = dict(
        data=[dict(b64_json=base64.b64encode(image.getvalue()).decode())],
        size="1254x1254",
        quality="low",
        output_format="png",
    )
    result = inspect_payload(payload, request_frame()[0]["payload"])
    assert result["image_bytes_returned_and_decodable"]
    assert not result["requested_contract_satisfied"]
    assert set(result["mismatches"]) == {
        "decoded_size_differs_from_requested",
        "reported_size_differs_from_requested",
        "reported_quality_differs_from_requested",
    }
    assert result["reported"]["model"] is None
    assert not result["model_identity_independently_verified"]
