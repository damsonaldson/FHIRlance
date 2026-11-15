"""Comprehensive integration tests for the Terminology Validation Engine.

Tests end-to-end integration across validate_resource, profile_engine, dynamic IG loading,
validate_dataset (serial and parallel), CLI flags, and all output formatters (OperationOutcome,
SARIF, JUnit XML, text, JSON).
"""

from __future__ import annotations

import email.message
import gc
import io
import json
import urllib.error
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import fhirlance
import fhirlance.validator
from fhirlance import (
    TxClient,
    TxOptions,
    parse_tx_options,
    validate_binding_value,
    validate_remote_code,
    validate_standalone_codings,
)
from fhirlance.cli import main as cli_main
from fhirlance.dataset import validate_dataset
from fhirlance.formatters import (
    _classify_issue_code,
    _classify_sarif_rule_id,
    _extract_raw_path,
    dataset_to_junit_xml,
    dataset_to_operation_outcome,
    dataset_to_sarif,
    format_dataset_report,
    issues_to_operation_outcome,
    validate_to_operation_outcome,
)
from fhirlance.ig_loader import load_compiled_ig_profiles, load_raw_ig_profiles
from fhirlance.profile_engine import CompiledBindingRule, _compile_binding_specs
from fhirlance.profiles import BASE_RESOURCE_BINDINGS, COMPLETE_CODE_SYSTEMS
from fhirlance.resource_validator import validate_resource
from fhirlance.terminology import (
    _evaluate_code_in_valueset,
    _evaluate_grammar_in_valueset,
    _evaluate_plain_code_in_valueset,
    _normalize_vs_spec,
    _read_sqlite_cache,
    _TxCacheKey,
    _write_sqlite_cache,
)

# =============================================================================
# 1. Public API Exports and Re-exports
# =============================================================================


def test_public_terminology_exports_from_package_root() -> None:
    expected_symbols = [
        "TxOptions",
        "parse_tx_options",
        "validate_standalone_codings",
        "validate_binding_value",
        "validate_remote_code",
        "TxClient",
    ]
    for sym in expected_symbols:
        assert hasattr(fhirlance, sym), f"{sym} missing from fhirlance root"
        assert hasattr(fhirlance.validator, sym), f"{sym} missing from fhirlance.validator"
        assert getattr(fhirlance, sym) is getattr(fhirlance.validator, sym)

    assert parse_tx_options(TxOptions()) is not None
    assert validate_standalone_codings({}, TxOptions()) is not None
    rule = CompiledBindingRule("a", ("a",), "required", "http://vs")
    assert isinstance(rule, CompiledBindingRule)
    assert "http://hl7.org/fhir/administrative-gender" in COMPLETE_CODE_SYSTEMS


# =============================================================================
# 2. validate_resource with Terminology Modes (tx="off", tx="local")
# =============================================================================


def test_validate_resource_tx_off_skips_terminology() -> None:
    invalid_resource: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/administrative-gender",
                    "code": "nonexistent-gender-code",
                }
            ]
        },
    }
    issues_off = validate_resource(invalid_resource, tx="off")
    assert not any("Terminology[" in issue for issue in issues_off)

    issues_local = validate_resource(invalid_resource, tx="local")
    expected_msg = (
        "Terminology[Observation.code.coding[0]]: "
        "code 'nonexistent-gender-code' is not defined in CodeSystem"
    )
    assert any(expected_msg in issue for issue in issues_local)


def test_validate_resource_complete_code_system_standalone() -> None:
    valid_resource: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/administrative-gender",
                    "code": "male",
                }
            ]
        },
    }
    issues_valid = validate_resource(valid_resource, tx="local")
    assert not any("Terminology[" in issue for issue in issues_valid)

    invalid_resource: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/administrative-gender",
                    "code": "nonexistent_code",
                }
            ]
        },
    }
    issues_invalid = validate_resource(invalid_resource, tx="local")
    assert any(
        "code 'nonexistent_code' is not defined in CodeSystem 'http://hl7.org/fhir/administrative-gender'"
        in issue
        for issue in issues_invalid
    )


def test_validate_resource_grammar_systems() -> None:
    obs_valid_ucum: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
        "valueQuantity": {
            "value": 120.0,
            "unit": "mm[Hg]",
            "system": "http://unitsofmeasure.org",
            "code": "mm[Hg]",
        },
    }
    issues = validate_resource(obs_valid_ucum, tx="local")
    assert not any("Terminology[" in issue for issue in issues)

    obs_invalid_ucum: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
        "valueQuantity": {
            "value": 120.0,
            "unit": "invalid",
            "system": "http://unitsofmeasure.org",
            "code": "INVALID_UCUM_@@#",
        },
    }
    issues_bad_ucum = validate_resource(obs_invalid_ucum, tx="local")
    assert any(
        "is not valid in grammar system 'http://unitsofmeasure.org'" in issue
        for issue in issues_bad_ucum
    )

    patient_valid_bcp47: dict[str, Any] = {
        "resourceType": "Patient",
        "communication": [
            {
                "language": {
                    "coding": [
                        {
                            "system": "urn:ietf:bcp:47",
                            "code": "en-US",
                        }
                    ]
                }
            }
        ],
    }
    assert not any("Terminology[" in i for i in validate_resource(patient_valid_bcp47, tx="local"))

    patient_bad_bcp47: dict[str, Any] = {
        "resourceType": "Patient",
        "communication": [
            {
                "language": {
                    "coding": [
                        {
                            "system": "urn:ietf:bcp:47",
                            "code": "not a valid language code!@",
                        }
                    ]
                }
            }
        ],
    }
    issues_bad_bcp47 = validate_resource(patient_bad_bcp47, tx="local")
    assert any("is not valid in grammar system 'urn:ietf:bcp:47'" in i for i in issues_bad_bcp47)


def test_validate_resource_grammar_mime_and_iso3166() -> None:
    obs_valid_mime: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "urn:ietf:bcp:13",
                    "code": "application/pdf",
                }
            ]
        },
    }
    assert not any("Terminology[" in i for i in validate_resource(obs_valid_mime, tx="local"))

    obs_invalid_mime: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "urn:ietf:bcp:13",
                    "code": "invalid/mime type with spaces",
                }
            ]
        },
    }
    bad_mime_issues = validate_resource(obs_invalid_mime, tx="local")
    assert any("is not valid in grammar system 'urn:ietf:bcp:13'" in i for i in bad_mime_issues)

    obs_iso3166_bad: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "urn:iso:std:iso:3166",
                    "code": "ZZZZZ999",
                }
            ]
        },
    }
    bad_iso_issues = validate_resource(obs_iso3166_bad, tx="local")
    assert any("is not valid in grammar system 'urn:iso:std:iso:3166'" in i for i in bad_iso_issues)


# =============================================================================
# 3. Nested Resources (contained and Bundle.entry)
# =============================================================================


def test_validate_resource_nested_contained_and_bundle_terminology() -> None:
    contained_obs: dict[str, Any] = {
        "resourceType": "Observation",
        "id": "obs1",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/administrative-gender",
                    "code": "bad-gender",
                }
            ]
        },
    }
    parent_condition: dict[str, Any] = {
        "resourceType": "Condition",
        "subject": {"reference": "Patient/123"},
        "contained": [contained_obs],
    }

    warnings: list[str] = []
    issues = validate_resource(parent_condition, tx="local", _warnings_out=warnings)
    assert any(
        issue.startswith("contained[0]: Terminology[Observation.code.coding[0]]: code 'bad-gender'")
        for issue in issues
    )
    # Check that root was not double validated
    contained_errors = [i for i in issues if "bad-gender" in i]
    assert len(contained_errors) == 1

    bundle: dict[str, Any] = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": contained_obs}],
    }
    bundle_warnings: list[str] = []
    bundle_issues = validate_resource(bundle, tx="local", _warnings_out=bundle_warnings)
    assert any(
        issue.startswith(
            "entry[0].resource: Terminology[Observation.code.coding[0]]: code 'bad-gender'"
        )
        for issue in bundle_issues
    )
    bundle_errors = [i for i in bundle_issues if "bad-gender" in i]
    assert len(bundle_errors) == 1


# =============================================================================
# 4. Base Resource Bindings (BASE_RESOURCE_BINDINGS)
# =============================================================================


def test_validate_resource_base_required_binding() -> None:
    assert "Condition" in BASE_RESOURCE_BINDINGS
    cond_valid: dict[str, Any] = {
        "resourceType": "Condition",
        "subject": {"reference": "Patient/123"},
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                }
            ]
        },
    }
    assert not any("clinicalStatus" in i for i in validate_resource(cond_valid, tx="local"))

    cond_invalid: dict[str, Any] = {
        "resourceType": "Condition",
        "subject": {"reference": "Patient/123"},
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "nonexistent-status",
                }
            ]
        },
    }
    issues = validate_resource(cond_invalid, tx="local")
    assert any(
        "'Condition.clinicalStatus' code 'nonexistent-status' not in required ValueSet "
        "'http://hl7.org/fhir/ValueSet/condition-clinical'" in i
        for i in issues
    )


def test_validate_resource_base_extensible_binding_warning_vs_error() -> None:
    obs_extensible_bad: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
        "interpretation": [
            {
                "coding": [
                    {
                        "system": "http://example.org/custom-interp",
                        "code": "CUSTOM_INTERP",
                    }
                ]
            }
        ],
    }

    # Under strict_extensible=False (default), it emits a warning, not an error
    warnings: list[str] = []
    issues = validate_resource(obs_extensible_bad, tx="local", _warnings_out=warnings)
    assert not any("interpretation" in i for i in issues)
    assert any("not in extensible ValueSet" in w for w in warnings)

    # Under strict_extensible=True, it emits an error
    issues_strict = validate_resource(
        obs_extensible_bad,
        tx=TxOptions(mode="local", strict_extensible=True),
    )
    assert any("not in extensible ValueSet" in i for i in issues_strict)


# =============================================================================
# 5. Profile Bindings (PROFILE_CONSTRAINTS["binding_specs"])
# =============================================================================


def test_validate_profile_bindings_us_core_patient() -> None:
    pat_bad_telecom: dict[str, Any] = {
        "resourceType": "Patient",
        "telecom": [
            {
                "system": "carrier-pigeon",
                "value": "123-456",
            }
        ],
    }
    prof_url = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
    issues = validate_resource(pat_bad_telecom, profile_urls=[prof_url], tx="local")
    assert any(
        "Profile[http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient]: "
        "'Patient.telecom.system' code 'carrier-pigeon' not in required ValueSet" in i
        for i in issues
    )

    pat_good_telecom: dict[str, Any] = {
        "resourceType": "Patient",
        "name": [{"family": "Smith"}],
        "identifier": [{"system": "http://example.org", "value": "1"}],
        "gender": "male",
        "telecom": [
            {
                "system": "phone",
                "value": "123-456",
            }
        ],
    }
    good_issues = validate_resource(pat_good_telecom, profile_urls=[prof_url], tx="local")
    assert not any("telecom.system" in i for i in good_issues)


def test_validate_profile_bindings_vitalsigns_required_preservation() -> None:
    vitals_url = "http://hl7.org/fhir/StructureDefinition/vitalsigns"
    bad_vitals: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "invalid-observation-status",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "85354-9",
                }
            ]
        },
        "subject": {"reference": "Patient/123"},
        "effectiveDateTime": "2026-11-14T12:00:00Z",
    }
    issues = validate_resource(bad_vitals, profile_urls=[vitals_url], tx="local")
    assert any(
        "code 'invalid-observation-status' not in required ValueSet "
        "'http://hl7.org/fhir/ValueSet/observation-status'" in i
        for i in issues
    )


def test_validate_profile_empty_or_text_only_codeable_concept() -> None:
    rules = _compile_binding_specs(
        "Observation",
        {
            "code": {
                "strength": "required",
                "value_set": "http://hl7.org/fhir/ValueSet/observation-status",
                "vs_spec": {"codes": ["final", "registered"]},
            }
        },
        {},
    )
    assert len(rules) == 1
    rule = rules[0]

    # Required CodeableConcept with only text should fail
    res_text = validate_binding_value(
        {"text": "unknown code"},
        rule.path,
        rule.value_set,
        rule.strength,
        TxOptions(mode="local"),
        vs_spec=rule.vs_spec,
    )
    assert len(res_text.errors) == 1
    assert "code 'unknown code' not in required ValueSet" in res_text.errors[0]

    # Required CodeableConcept with empty coding should fail
    res_empty = validate_binding_value(
        {"coding": []},
        rule.path,
        rule.value_set,
        rule.strength,
        TxOptions(mode="local"),
        vs_spec=rule.vs_spec,
    )
    assert len(res_empty.errors) == 1
    assert "has no coding for required ValueSet" in res_empty.errors[0]


# =============================================================================
# 6. Remote Terminology Server & TxClient
# =============================================================================


def test_remote_tx_validation_mock_success_and_failure(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.sqlite"
    options = TxOptions(mode="remote", server="https://tx.example.org/r4", cache_path=db_path)

    # 1. Success response
    success_resp = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "result", "valueBoolean": True},
            {"name": "message", "valueString": "Code is valid"},
        ],
    }
    with patch("urllib.request.urlopen") as mock_url:
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value.read.return_value = json.dumps(success_resp).encode("utf-8")
        mock_url.return_value = mock_cm

        res, msg = validate_remote_code(
            options=options,
            system="http://example.org/custom-sys",
            code="valid-code-123",
            value_set_url="http://example.org/vs/1",
        )
        assert res is True
        assert msg == "Code is valid"

    # Verify L2 SQLite cache persistence
    cached = _read_sqlite_cache(
        db_path,
        _TxCacheKey(
            "https://tx.example.org/r4",
            "http://example.org/custom-sys",
            "valid-code-123",
            "http://example.org/vs/1",
        ),
    )
    assert cached == (True, "Code is valid")

    # 2. Failure response
    fail_resp = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "result", "valueBoolean": False},
            {"name": "message", "valueString": "Unknown code"},
        ],
    }
    with patch("urllib.request.urlopen") as mock_url:
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value.read.return_value = json.dumps(fail_resp).encode("utf-8")
        mock_url.return_value = mock_cm

        client = TxClient(options)
        res_fail, msg_fail = client.validate_code(
            system="http://example.org/custom-sys",
            code="invalid-code-999",
            value_set_url="http://example.org/vs/1",
        )
        assert res_fail is False
        assert msg_fail == "Unknown code"


def test_remote_tx_validation_network_failure_and_sqlite_errors(tmp_path: Path) -> None:
    db_path = tmp_path / "bad_cache.sqlite"
    options = TxOptions(mode="remote", server="https://tx.example.org/r4", cache_path=db_path)

    # HTTPError from remote server
    err_body = json.dumps(
        {
            "resourceType": "Parameters",
            "parameter": [
                {"name": "result", "valueBoolean": False},
                {"name": "message", "valueString": "Invalid code from 400"},
            ],
        }
    ).encode("utf-8")

    http_error = urllib.error.HTTPError(
        "https://tx.example.org/r4",
        400,
        "Bad Request",
        email.message.Message(),
        io.BytesIO(err_body),
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        res, msg = validate_remote_code(
            options=options,
            system="http://example.org/custom-sys",
            code="code-400",
            value_set_url="http://example.org/vs/1",
        )
        assert res is False
        assert msg == "Invalid code from 400"

    # URLError / unreachable
    url_error = urllib.error.URLError("Connection refused")
    with patch("urllib.request.urlopen", side_effect=url_error):
        res_err, msg_err = validate_remote_code(
            options=options,
            system="http://example.org/custom-sys",
            code="code-unreachable",
            value_set_url="http://example.org/vs/1",
        )
        assert res_err is None
        assert "Terminology server unreachable" in str(msg_err)

    # SQLite exception handling branches
    bad_dir = tmp_path / "not_a_dir" / "cache.sqlite"
    # Calling read and write on an invalid file path returns None / suppresses error
    key = _TxCacheKey("srv", "sys", "code", "vs")
    assert _read_sqlite_cache(bad_dir, key) is None
    _write_sqlite_cache(bad_dir, key, True, None)


# =============================================================================
# 7. Dynamic IG Loading with Terminology Bindings
# =============================================================================


def test_dynamic_ig_loader_with_terminology_bindings(tmp_path: Path) -> None:
    ig_dir = tmp_path / "custom_ig"
    ig_dir.mkdir()

    # 1. Custom CodeSystem
    cs = {
        "resourceType": "CodeSystem",
        "url": "http://example.org/cs/fruits",
        "status": "active",
        "content": "complete",
        "concept": [{"code": "apple"}, {"code": "banana"}, {"code": "cherry"}],
    }
    (ig_dir / "CodeSystem-fruits.json").write_text(json.dumps(cs), encoding="utf-8")

    # 2. Custom ValueSet
    vs = {
        "resourceType": "ValueSet",
        "url": "http://example.org/vs/fruits",
        "status": "active",
        "compose": {
            "include": [
                {
                    "system": "http://example.org/cs/fruits",
                    "concept": [{"code": "apple"}, {"code": "banana"}],
                }
            ]
        },
    }
    (ig_dir / "ValueSet-fruits.json").write_text(json.dumps(vs), encoding="utf-8")

    # 3. Custom StructureDefinition
    sd = {
        "resourceType": "StructureDefinition",
        "url": "http://example.org/StructureDefinition/fruit-observation",
        "name": "FruitObservation",
        "status": "active",
        "kind": "resource",
        "abstract": False,
        "type": "Observation",
        "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Observation",
        "derivation": "constraint",
        "differential": {
            "element": [
                {"path": "Observation.code", "min": 1},
                {
                    "path": "Observation.code",
                    "binding": {
                        "strength": "required",
                        "valueSet": "http://example.org/vs/fruits",
                    },
                },
            ]
        },
    }
    (ig_dir / "StructureDefinition-fruit-observation.json").write_text(
        json.dumps(sd), encoding="utf-8"
    )

    raw_profiles = load_raw_ig_profiles([ig_dir])
    assert "http://example.org/StructureDefinition/fruit-observation" in raw_profiles
    prof_spec = raw_profiles["http://example.org/StructureDefinition/fruit-observation"]
    assert "code" in prof_spec.get("binding_specs", {})

    compiled_profiles = load_compiled_ig_profiles([ig_dir])
    prof_url = "http://example.org/StructureDefinition/fruit-observation"
    assert prof_url in compiled_profiles

    # Valid Observation with apple
    obs_valid: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"coding": [{"system": "http://example.org/cs/fruits", "code": "apple"}]},
    }
    assert not any(
        "http://example.org/vs/fruits" in i
        for i in validate_resource(
            obs_valid, profile_urls=[prof_url], ig_sources=compiled_profiles, tx="local"
        )
    )

    # Invalid Observation with cherry (cherry is in CodeSystem but excluded from ValueSet)
    obs_invalid: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"coding": [{"system": "http://example.org/cs/fruits", "code": "cherry"}]},
    }
    issues = validate_resource(
        obs_invalid, profile_urls=[prof_url], ig_sources=compiled_profiles, tx="local"
    )
    assert any(
        "code 'cherry' not in required ValueSet 'http://example.org/vs/fruits'" in i for i in issues
    )


# =============================================================================
# 8. Dataset Validation Integration (Serial and Parallel)
# =============================================================================


def test_dataset_validation_with_terminology_serial_and_parallel(tmp_path: Path) -> None:
    # 1. Valid file
    valid_file = tmp_path / "valid.json"
    valid_file.write_text(
        json.dumps(
            {
                "resourceType": "Patient",
                "gender": "male",
            }
        ),
        encoding="utf-8",
    )

    # 2. File with terminology warning (extensible binding)
    warning_file = tmp_path / "warning.json"
    warning_file.write_text(
        json.dumps(
            {
                "resourceType": "Observation",
                "status": "final",
                "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                "interpretation": [
                    {
                        "coding": [
                            {
                                "system": "http://example.org/custom-interp",
                                "code": "CUSTOM_INTERP",
                            }
                        ]
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    # 3. File with terminology error (required binding)
    error_file = tmp_path / "error.json"
    error_file.write_text(
        json.dumps(
            {
                "resourceType": "Condition",
                "subject": {"reference": "Patient/123"},
                "clinicalStatus": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": "bogus-status",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    for parallel_mode in (False, True):
        report = validate_dataset(
            tmp_path,
            parallel=parallel_mode,
            threads=2 if parallel_mode else None,
            tx="local",
        )
        assert report["total_resources"] == 3
        # The warning file is counted as valid since it has 0 errors!
        assert report["valid_resources"] == 2
        assert report["invalid_resources"] == 1
        assert len(report["issues"]) == 1
        assert len(report["warnings"]) == 1

        # Test tx="off" ignores terminology errors
        report_off = validate_dataset(
            tmp_path,
            parallel=parallel_mode,
            threads=2 if parallel_mode else None,
            tx="off",
        )
        assert report_off["valid_resources"] == 3
        assert report_off["invalid_resources"] == 0
        assert len(report_off["issues"]) == 0

        # Test strict_extensible=True turns warning into error
        report_strict = validate_dataset(
            tmp_path,
            parallel=parallel_mode,
            threads=2 if parallel_mode else None,
            tx="local",
            strict_extensible=True,
        )
        assert report_strict["valid_resources"] == 1
        assert report_strict["invalid_resources"] == 2
        assert len(report_strict["issues"]) == 2


def test_dataset_ndjson_with_terminology_warnings_and_errors(tmp_path: Path) -> None:
    ndjson_file = tmp_path / "bundle.ndjson"
    lines = [
        json.dumps({"resourceType": "Patient", "gender": "female"}),
        json.dumps(
            {
                "resourceType": "Observation",
                "status": "final",
                "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                "interpretation": [
                    {
                        "coding": [
                            {
                                "system": "http://example.org/custom-interp",
                                "code": "CUSTOM_INTERP",
                            }
                        ]
                    }
                ],
            }
        ),
    ]
    ndjson_file.write_text("\n".join(lines), encoding="utf-8")

    report = validate_dataset(ndjson_file, tx="local")
    assert report["total_resources"] == 2
    assert report["valid_resources"] == 2
    assert len(report["warnings"]) == 1
    assert "line" in report["warnings"][0]
    assert report["warnings"][0]["line"] == 2


# =============================================================================
# 9. CLI Flags Integration
# =============================================================================


def test_cli_flags_tx_off_and_local(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Error resource file
    err_file = tmp_path / "err.json"
    err_file.write_text(
        json.dumps(
            {
                "resourceType": "Condition",
                "subject": {"reference": "Patient/123"},
                "clinicalStatus": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": "bogus-status",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    # 1. CLI with --tx off -> exits 0
    monkeypatch.setattr("sys.argv", ["fhirlance", str(err_file), "--tx", "off"])
    rc_off = cli_main()
    assert rc_off == 0

    # 2. CLI with --tx local -> exits 1
    monkeypatch.setattr("sys.argv", ["fhirlance", str(err_file), "--tx", "local"])
    rc_local = cli_main()
    assert rc_local == 1

    # 3. CLI with aliases -tx, --term, -term
    for flag in ("-tx", "--term", "-term"):
        monkeypatch.setattr("sys.argv", ["fhirlance", str(err_file), flag, "off"])
        assert cli_main() == 0


def test_cli_strict_extensible_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    warn_file = tmp_path / "warn.json"
    warn_file.write_text(
        json.dumps(
            {
                "resourceType": "Observation",
                "status": "final",
                "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                "interpretation": [
                    {
                        "coding": [
                            {
                                "system": "http://example.org/custom-interp",
                                "code": "CUSTOM_INTERP",
                            }
                        ]
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    # Default tx=local does not fail on warnings
    monkeypatch.setattr("sys.argv", ["fhirlance", str(warn_file)])
    assert cli_main() == 0

    # --strict-extensible treats warnings as errors -> exits 1
    monkeypatch.setattr("sys.argv", ["fhirlance", str(warn_file), "--strict-extensible"])
    assert cli_main() == 1


# =============================================================================
# 10. Formatters Integration (OperationOutcome, SARIF, JUnit, Text)
# =============================================================================


def test_formatters_operation_outcome_and_sarif_with_terminology() -> None:
    raw_issue = (
        "Terminology[Observation.code.coding[0]]: code 'bad' is not in CodeSystem 'http://sys'"
    )
    assert _classify_issue_code(raw_issue) == "code-invalid"
    assert _classify_sarif_rule_id(raw_issue) == "FHIRLANCE_TERMINOLOGY"
    assert _extract_raw_path(raw_issue) == "Observation.code.coding[0]"

    # issues_to_operation_outcome
    oo = issues_to_operation_outcome(
        [raw_issue],
        resource_type="Observation",
        warnings=["Observation.interpretation: could not validate code 'xyz'"],
    )
    issues_list = oo.get("issue", [])
    assert len(issues_list) == 2
    err_item = next(i for i in issues_list if i["severity"] == "error")
    assert err_item["code"] == "code-invalid"
    assert err_item["expression"] == ["Observation.code.coding[0]"]

    warn_item = next(i for i in issues_list if i["severity"] == "warning")
    assert warn_item["code"] == "code-invalid"

    # validate_to_operation_outcome
    invalid_obs: dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/administrative-gender",
                    "code": "nonexistent_code",
                }
            ]
        },
    }
    val_oo = validate_to_operation_outcome(invalid_obs, tx="local")
    assert any(iss.get("code") == "code-invalid" for iss in val_oo.get("issue", []))

    # dataset_to_operation_outcome
    report: dict[str, Any] = {
        "total_files": 1,
        "total_resources": 1,
        "valid_resources": 0,
        "invalid_resources": 1,
        "issues": [
            {
                "file": "test.json",
                "resourceType": "Observation",
                "id": "obs1",
                "issues": [raw_issue],
            }
        ],
        "warnings": [
            {
                "file": "test.json",
                "resourceType": "Observation",
                "id": "obs1",
                "warnings": ["Warning: check terminology"],
            }
        ],
    }
    dataset_oo = dataset_to_operation_outcome(report)
    assert len(dataset_oo.get("issue", [])) == 2

    # dataset_to_sarif
    sarif_obj = dataset_to_sarif(report)
    runs = sarif_obj.get("runs", [])
    assert len(runs) == 1
    sarif_results = runs[0].get("results", [])
    assert any(r["ruleId"] == "FHIRLANCE_TERMINOLOGY" for r in sarif_results)

    # dataset_to_junit_xml
    junit_xml = dataset_to_junit_xml(report)
    assert 'classname="test.json"' in junit_xml
    assert 'name="validate_obs1"' in junit_xml
    assert "<failure" in junit_xml

    # format_dataset_report
    text_out = format_dataset_report(report, output_format="text")
    assert "invalid=1" in text_out

    json_out = format_dataset_report(report, output_format="json")
    parsed_json = json.loads(json_out)
    assert parsed_json["invalid_resources"] == 1


# =============================================================================
# 11. Additional Low-Level Branch Coverage
# =============================================================================


def test_terminology_branch_coverage_helpers() -> None:
    # 1. _evaluate_grammar_in_valueset branches
    # invalid grammar
    r, _m = _evaluate_grammar_in_valueset("http://unitsofmeasure.org", "bad!", False, None)
    assert r is False

    # grammar with system in sys_codes
    r_sys, _ = _evaluate_grammar_in_valueset(
        "http://unitsofmeasure.org",
        "mg",
        True,
        {"system_codes": {"http://unitsofmeasure.org": ["mg", "kg"]}},
    )
    assert r_sys is True

    # grammar with empty spec
    r_empty, _ = _evaluate_grammar_in_valueset("http://unitsofmeasure.org", "mg", True, {})
    assert r_empty is True

    # 2. _evaluate_plain_code_in_valueset branches
    # plain code matching grammar in external_systems
    r_plain = _evaluate_plain_code_in_valueset(
        "mg", {"external_systems": ["http://unitsofmeasure.org"]}
    )
    assert r_plain == (True, None)

    # plain code failing grammar in all external_systems
    r_plain_bad = _evaluate_plain_code_in_valueset(
        "bad-code-123", {"external_systems": ["http://unitsofmeasure.org"]}
    )
    assert r_plain_bad is not None
    assert r_plain_bad[0] is False

    # 3. _normalize_vs_spec with iterable
    norm = _normalize_vs_spec(["code1", "code2"])
    assert norm == {"codes": frozenset(["code1", "code2"])}

    # 4. _evaluate_code_in_valueset with None vs_spec
    res_none, _ = _evaluate_code_in_valueset(
        "http://unitsofmeasure.org", "mg", "http://any-vs", None, TxOptions(mode="local")
    )
    assert res_none is True


# =============================================================================
# 12. Regressions from Adversarial Audit
# =============================================================================


def test_ephemeral_vs_spec_no_id_collision_under_gc() -> None:
    # Pass ephemeral dict 1
    res1 = validate_binding_value(
        "CODE_A",
        "Test.path",
        "http://example.org/vs/1",
        "required",
        TxOptions(mode="local"),
        vs_spec={"codes": ["CODE_A"]},
    )
    assert not res1.errors

    gc.collect()

    # Pass ephemeral dict 2 with completely different codes
    res2 = validate_binding_value(
        "CODE_A",
        "Test.path",
        "http://example.org/vs/2",
        "required",
        TxOptions(mode="local"),
        vs_spec={"codes": ["CODE_B"]},
    )
    assert len(res2.errors) == 1
    assert "code 'CODE_A' not in required ValueSet" in res2.errors[0]


def test_multi_coding_codeable_concept_order_and_attribution() -> None:
    vs_spec = {
        "codes": ["valid1"],
        "system_codes": {"http://sys1": ["valid1"]},
        "external_systems": [],
    }

    # a) [local_coding, valid_coding] passes regardless of order
    concept_a = {
        "coding": [
            {"system": "http://other-local", "code": "foo"},
            {"system": "http://sys1", "code": "valid1"},
        ]
    }
    res_a = validate_binding_value(
        concept_a,
        "Test.path",
        "http://vs1",
        "extensible",
        TxOptions(mode="local"),
        vs_spec=vs_spec,
    )
    assert not res_a.errors
    assert not res_a.warnings

    # b) [local_coding, invalid_known_system_coding] fails with error regardless of order
    concept_b1 = {
        "coding": [
            {"system": "http://other-local", "code": "foo"},
            {"system": "http://sys1", "code": "invalid_code_in_sys1"},
        ]
    }
    res_b1 = validate_binding_value(
        concept_b1,
        "Test.path",
        "http://vs1",
        "extensible",
        TxOptions(mode="local"),
        vs_spec=vs_spec,
    )
    assert len(res_b1.errors) == 1
    assert "code 'invalid_code_in_sys1' not in extensible ValueSet" in res_b1.errors[0]

    concept_b2 = {
        "coding": [
            {"system": "http://sys1", "code": "invalid_code_in_sys1"},
            {"system": "http://other-local", "code": "foo"},
        ]
    }
    res_b2 = validate_binding_value(
        concept_b2,
        "Test.path",
        "http://vs1",
        "extensible",
        TxOptions(mode="local"),
        vs_spec=vs_spec,
    )
    assert len(res_b2.errors) == 1
    assert "code 'invalid_code_in_sys1' not in extensible ValueSet" in res_b2.errors[0]

    # c) [local_coding, remote_unreachable_coding] attributes warning to remote_unreachable_coding
    vs_spec_ext = {
        "codes": [],
        "system_codes": {},
        "external_systems": ["http://snomed.info/sct"],
    }
    concept_c = {
        "coding": [
            {"system": "http://other-local", "code": "local_code"},
            {"system": "http://snomed.info/sct", "code": "snomed_unreachable_code"},
        ]
    }
    url_err = urllib.error.URLError("Connection refused")
    with patch("urllib.request.urlopen", side_effect=url_err):
        res_c = validate_binding_value(
            concept_c,
            "Test.path",
            "http://vs_ext",
            "required",
            TxOptions(mode="remote", server="https://tx.example.org/r4"),
            vs_spec=vs_spec_ext,
        )
        assert len(res_c.warnings) == 1
        assert "could not validate code 'snomed_unreachable_code'" in res_c.warnings[0]


def test_coding_missing_code_on_required_binding() -> None:
    concept = {"coding": [{"display": "No code"}]}
    res = validate_binding_value(
        concept,
        "Test.path",
        "http://vs1",
        "required",
        TxOptions(mode="local"),
        vs_spec={"codes": ["code1"]},
    )
    assert len(res.errors) == 1
    assert "'Test.path' has no coding for required ValueSet 'http://vs1'" in res.errors[0]

    res_ext = validate_binding_value(
        concept,
        "Test.path",
        "http://vs1",
        "extensible",
        TxOptions(mode="local"),
        vs_spec={"codes": ["code1"]},
    )
    assert not res_ext.errors
    assert not res_ext.warnings


def test_deduplicate_base_binding_vs_active_profile_binding() -> None:
    bad_obs = {
        "resourceType": "Observation",
        "status": "invalid-status-xyz",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                    }
                ]
            }
        ],
        "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9"}]},
        "subject": {"reference": "Patient/123"},
        "effectiveDateTime": "2026-11-14T12:00:00Z",
    }
    vitals_url = "http://hl7.org/fhir/StructureDefinition/vitalsigns"
    issues = validate_resource(
        bad_obs,
        profile_urls=[vitals_url],
        tx="local",
    )
    status_errors = [i for i in issues if "invalid-status-xyz" in i]
    assert len(status_errors) == 1
    assert status_errors[0].startswith(
        "Profile[http://hl7.org/fhir/StructureDefinition/vitalsigns]:"
    )
