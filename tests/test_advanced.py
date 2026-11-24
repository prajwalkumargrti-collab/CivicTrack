
from io import BytesIO
from pathlib import Path
import re

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage

import app as civic_app
from app import (
    app,
    db,
    Complaint,
    ComplaintEvent,
    User,
    save_upload,
    find_possible_duplicate,
    dashboard_data,
)


def make_complaint(
    code="CT-ADV123456",
    description="A large pothole is present near the main road.",
    latitude=12.9716,
    longitude=77.5946,
    status="Submitted",
    priority_label="Medium",
    ward="Ward 1",
):
    complaint = Complaint(
        tracking_code=code,
        citizen_name="Test Citizen",
        phone_last4="1234",
        category="Pothole / Road Damage",
        description=description,
        address="Test Main Road",
        ward=ward,
        latitude=latitude,
        longitude=longitude,
        severity="Medium",
        status=status,
        priority_score=50,
        priority_label=priority_label,
    )
    db.session.add(complaint)
    db.session.commit()
    return complaint


def make_admin(role="admin", active=True):
    user = User(
        email="advancedadmin@example.com",
        name="Advanced Test Officer",
        role=role,
        active=active,
    )
    user.set_password("TestPassword123")
    db.session.add(user)
    db.session.commit()
    return user


def make_image_file():
    image_data = BytesIO()
    image = Image.new("RGB", (100, 100), "white")
    image.save(image_data, format="JPEG")
    image_data.seek(0)
    return image_data


# ---------------- IMAGE UPLOAD TESTS ----------------

def test_valid_image_upload(tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))

    with app.app_context():

        upload = FileStorage(
            stream=make_image_file(),
            filename="road_damage.jpg",
            content_type="image/jpeg",
        )

        filename = save_upload(upload)

        assert filename is not None
        assert re.fullmatch(r"[a-f0-9]{32}\.jpg", filename)
        assert (tmp_path / filename).exists()


def test_image_upload_rejects_unsupported_extension():
    with app.app_context():
        upload = FileStorage(
            stream=BytesIO(b"not an image"),
            filename="document.exe",
        )

        with pytest.raises(ValueError, match="JPG, PNG or WEBP"):
            save_upload(upload)


def test_image_upload_rejects_corrupted_image():
    with app.app_context():
        upload = FileStorage(
            stream=BytesIO(b"this is not a valid image"),
            filename="broken.jpg",
        )

        with pytest.raises(ValueError, match="not a valid image"):
            save_upload(upload)


def test_image_upload_rejects_large_dimensions():
    with app.app_context():
        image_data = BytesIO()
        image = Image.new("RGB", (5001, 1), "white")
        image.save(image_data, format="JPEG")
        image_data.seek(0)

        upload = FileStorage(
            stream=image_data,
            filename="large.jpg",
            content_type="image/jpeg",
        )

        with pytest.raises(ValueError, match="dimensions are too large"):
            save_upload(upload)


def test_empty_upload_returns_none():
    with app.app_context():
        assert save_upload(None) is None


def test_upload_endpoint_rejects_unsafe_filename():
    with app.test_client() as client:
        response = client.get("/uploads/../../secret.txt")
        assert response.status_code == 404


# ---------------- DUPLICATE DETECTION TESTS ----------------

def test_duplicate_detection_finds_similar_nearby_complaint():
    if civic_app.TfidfVectorizer is None:
        pytest.skip("scikit-learn is not installed")

    existing = make_complaint(
        description="A large pothole is present near the main road.",
        latitude=12.9716,
        longitude=77.5946,
    )

    duplicate, similarity = find_possible_duplicate(
        "Pothole / Road Damage",
        "A large pothole is present near the main road.",
        12.9716,
        77.5946,
    )

    assert duplicate is not None
    assert duplicate.id == existing.id
    assert similarity >= 0.34


def test_duplicate_detection_ignores_distant_complaints():
    if civic_app.TfidfVectorizer is None:
        pytest.skip("scikit-learn is not installed")

    make_complaint(
        description="A large pothole is present near the main road.",
        latitude=12.9716,
        longitude=77.5946,
    )

    duplicate, similarity = find_possible_duplicate(
        "Pothole / Road Damage",
        "A large pothole is present near the main road.",
        13.05,
        77.70,
    )

    assert duplicate is None
    assert similarity == 0.0


def test_duplicate_detection_ignores_rejected_complaints():
    if civic_app.TfidfVectorizer is None:
        pytest.skip("scikit-learn is not installed")

    make_complaint(
        description="A large pothole is present near the main road.",
        latitude=12.9716,
        longitude=77.5946,
        status="Rejected",
    )

    duplicate, similarity = find_possible_duplicate(
        "Pothole / Road Damage",
        "A large pothole is present near the main road.",
        12.9716,
        77.5946,
    )

    assert duplicate is None
    assert similarity == 0.0


def test_duplicate_detection_requires_coordinates():
    duplicate, similarity = find_possible_duplicate(
        "Pothole / Road Damage",
        "A large pothole is present near the main road.",
        None,
        None,
    )

    assert duplicate is None
    assert similarity == 0.0


# ---------------- COORDINATE VALIDATION TESTS ----------------

def test_report_rejects_only_one_coordinate():
    with app.test_client() as client:
        response = client.post(
            "/report",
            data={
                "citizen_name": "Test Citizen",
                "phone": "9876543210",
                "category": "Pothole / Road Damage",
                "description": "There is a large pothole near the college entrance.",
                "address": "College Main Road",
                "ward": "Ward 1",
                "severity": "High",
                "latitude": "12.9716",
                "longitude": "",
            },
        )

        assert response.status_code == 200
        assert Complaint.query.count() == 0


def test_report_rejects_out_of_range_coordinates():
    with app.test_client() as client:
        response = client.post(
            "/report",
            data={
                "citizen_name": "Test Citizen",
                "phone": "9876543210",
                "category": "Pothole / Road Damage",
                "description": "There is a large pothole near the college entrance.",
                "address": "College Main Road",
                "ward": "Ward 1",
                "severity": "High",
                "latitude": "120",
                "longitude": "77.5946",
            },
        )

        assert response.status_code == 200
        assert Complaint.query.count() == 0


# ---------------- ADMIN SECURITY TESTS ----------------

def test_admin_login_rejects_wrong_password():
    make_admin()

    with app.test_client() as client:
        response = client.post(
            "/admin/login",
            data={
                "email": "advancedadmin@example.com",
                "password": "WrongPassword",
            },
        )

        assert response.status_code == 200

        dashboard = client.get("/admin/dashboard")
        assert dashboard.status_code == 302


def test_inactive_admin_cannot_login():
    make_admin(active=False)

    with app.test_client() as client:
        client.post(
            "/admin/login",
            data={
                "email": "advancedadmin@example.com",
                "password": "TestPassword123",
            },
        )

        response = client.get("/admin/dashboard")
        assert response.status_code == 302


def test_non_officer_role_cannot_access_admin_dashboard():
    make_admin(role="citizen")

    with app.test_client() as client:
        client.post(
            "/admin/login",
            data={
                "email": "advancedadmin@example.com",
                "password": "TestPassword123",
            },
        )

        response = client.get("/admin/dashboard")
        assert response.status_code == 403


def test_admin_cannot_set_invalid_complaint_status():
    make_admin()
    complaint = make_complaint()

    with app.test_client() as client:
        client.post(
            "/admin/login",
            data={
                "email": "advancedadmin@example.com",
                "password": "TestPassword123",
            },
        )

        response = client.post(
            f"/admin/complaints/{complaint.id}/update",
            data={
                "status": "Invalid Status",
                "note": "Testing invalid status",
            },
        )

        assert response.status_code == 302

        updated = db.session.get(Complaint, complaint.id)
        assert updated.status == "Submitted"


# ---------------- DASHBOARD ANALYTICS TESTS ----------------

def test_empty_dashboard_has_zero_statistics():
    stats = dashboard_data()

    assert stats["total"] == 0
    assert stats["active"] == 0
    assert stats["resolved"] == 0
    assert stats["critical"] == 0
    assert stats["resolution_rate"] == 0
    assert stats["avg_resolution_hours"] is None
    assert len(stats["trend"]["labels"]) == 14
    assert len(stats["trend"]["values"]) == 14


def test_dashboard_calculates_complaint_statistics():
    from datetime import datetime, timedelta, timezone

    active = make_complaint(
        code="CT-ACTIVE12345",
        status="In Progress",
        priority_label="High",
        ward="Ward 1",
    )

    resolved = make_complaint(
        code="CT-RESOLVED123",
        status="Resolved",
        priority_label="Medium",
        ward="Ward 2",
    )

    resolved.created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=5)
    resolved.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.add(
        ComplaintEvent(
            complaint_id=resolved.id,
            status="Resolved",
            note="Repair completed.",
            actor="Test Officer",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
    )
    db.session.commit()

    stats = dashboard_data()

    assert stats["total"] == 2
    assert stats["active"] == 1
    assert stats["resolved"] == 1
    assert stats["critical"] == 1
    assert stats["resolution_rate"] == 50
    assert stats["avg_resolution_hours"] is not None
    assert len(stats["wards"]) == 2
    assert len(stats["recent"]) == 2
