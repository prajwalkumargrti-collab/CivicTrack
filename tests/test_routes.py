
from app import app, db, Complaint, ComplaintEvent, Verification, User


def create_complaint():
    complaint = Complaint(
        tracking_code="CT-TEST123456",
        citizen_name="Test Citizen",
        phone_last4="1234",
        category="Pothole / Road Damage",
        description="A large pothole is present near the main road.",
        address="Test Main Road",
        ward="Ward 1",
        severity="Medium",
        status="Submitted",
        priority_score=40,
        priority_label="Medium",
    )
    db.session.add(complaint)
    db.session.commit()
    return complaint


def authorize_complaint(client, complaint):
    """Complete the citizen tracking check before accessing protected details."""
    response = client.post(
        "/track",
        data={
            "tracking_code": complaint.tracking_code,
            "phone_last4": "1234",
        },
    )
    assert response.status_code == 302
    assert f"/complaint/{complaint.tracking_code}" in response.location
    return response


def create_admin():
    user = User(
        email="testadmin@example.com",
        name="Test Officer",
        role="admin",
        active=True,
    )
    user.set_password("TestPassword123")
    db.session.add(user)
    db.session.commit()
    return user


def test_report_page_loads():
    with app.test_client() as client:
        response = client.get("/report")
        assert response.status_code == 200


def test_citizen_can_submit_complaint():
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
                "latitude": "",
                "longitude": "",
            },
        )

        assert response.status_code == 302
        assert "/report/success/" in response.location

        complaint = Complaint.query.first()
        assert complaint is not None
        assert complaint.citizen_name == "Test Citizen"
        assert complaint.phone_last4 == "3210"
        assert complaint.status == "Submitted"

        event = ComplaintEvent.query.filter_by(
            complaint_id=complaint.id
        ).first()
        assert event is not None
        assert event.actor == "Citizen"


def test_invalid_complaint_is_rejected():
    with app.test_client() as client:
        response = client.post(
            "/report",
            data={
                "citizen_name": "",
                "phone": "123",
                "category": "Pothole / Road Damage",
                "description": "Short description",
                "address": "",
                "severity": "Medium",
            },
        )

        assert response.status_code == 200
        assert Complaint.query.count() == 0


def test_citizen_can_track_complaint():
    complaint = create_complaint()

    with app.test_client() as client:
        response = client.post(
            "/track",
            data={
                "tracking_code": complaint.tracking_code,
                "phone_last4": "1234",
            },
        )

        assert response.status_code == 302
        assert f"/complaint/{complaint.tracking_code}" in response.location

        detail = client.get(response.location)
        assert detail.status_code == 200


def test_tracking_rejects_wrong_phone_suffix():
    complaint = create_complaint()

    with app.test_client() as client:
        response = client.post(
            "/track",
            data={
                "tracking_code": complaint.tracking_code,
                "phone_last4": "9999",
            },
        )

        assert response.status_code == 200


def test_community_verification_increases_count():
    complaint = create_complaint()

    with app.test_client() as client:
        authorize_complaint(client, complaint)

        response = client.post(
            f"/complaint/{complaint.tracking_code}/verify",
            data={"mobile": "9876543210"},
        )

        assert response.status_code == 302

        updated = db.session.get(Complaint, complaint.id)
        assert updated.verification_count == 1
        assert Verification.query.filter_by(
            complaint_id=complaint.id
        ).count() == 1


def test_same_mobile_cannot_verify_twice():
    complaint = create_complaint()

    with app.test_client() as client:
        authorize_complaint(client, complaint)

        for _ in range(2):
            client.post(
                f"/complaint/{complaint.tracking_code}/verify",
                data={"mobile": "9876543210"},
            )

        updated = db.session.get(Complaint, complaint.id)
        assert updated.verification_count == 1

        assert Verification.query.filter_by(
            complaint_id=complaint.id
        ).count() == 1


def test_closed_complaint_cannot_be_verified():
    complaint = create_complaint()
    complaint.status = "Resolved"
    db.session.commit()

    with app.test_client() as client:
        authorize_complaint(client, complaint)

        client.post(
            f"/complaint/{complaint.tracking_code}/verify",
            data={"mobile": "9876543210"},
        )

        updated = db.session.get(Complaint, complaint.id)
        assert updated.verification_count == 0


def test_admin_dashboard_requires_login():
    with app.test_client() as client:
        response = client.get("/admin/dashboard")

        assert response.status_code == 302
        assert "/admin/login" in response.location


def test_admin_can_login_and_update_complaint():
    create_admin()
    complaint = create_complaint()

    with app.test_client() as client:
        login_response = client.post(
            "/admin/login",
            data={
                "email": "testadmin@example.com",
                "password": "TestPassword123",
            },
        )

        assert login_response.status_code == 302

        dashboard_response = client.get("/admin/dashboard")
        assert dashboard_response.status_code == 200

        update_response = client.post(
            f"/admin/complaints/{complaint.id}/update",
            data={
                "status": "In Progress",
                "note": "Repair work has started.",
            },
        )

        assert update_response.status_code == 302

        updated = db.session.get(Complaint, complaint.id)
        assert updated.status == "In Progress"

        event = ComplaintEvent.query.filter_by(
            complaint_id=complaint.id,
            status="In Progress",
        ).first()

        assert event is not None
        assert event.actor == "Test Officer"


def test_admin_can_export_complaints_csv():
    create_admin()
    create_complaint()

    with app.test_client() as client:
        client.post(
            "/admin/login",
            data={
                "email": "testadmin@example.com",
                "password": "TestPassword123",
            },
        )

        response = client.get("/admin/export.csv")

        assert response.status_code == 200
        assert "text/csv" in response.content_type
        assert b"CT-TEST123456" in response.data


def test_complaint_image_is_blocked_without_tracking_verification(tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))
    filename = "a" * 32 + ".jpg"
    (tmp_path / filename).write_bytes(b"test image bytes")

    complaint = create_complaint()
    complaint.image_filename = filename
    db.session.commit()

    with app.test_client() as client:
        response = client.get(f"/uploads/{filename}")
        assert response.status_code == 403


def test_verified_citizen_can_view_their_complaint_image(tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))
    filename = "b" * 32 + ".jpg"
    (tmp_path / filename).write_bytes(b"test image bytes")

    complaint = create_complaint()
    complaint.image_filename = filename
    db.session.commit()

    with app.test_client() as client:
        authorize_complaint(client, complaint)
        response = client.get(f"/uploads/{filename}")

        assert response.status_code == 200
        assert response.data == b"test image bytes"
        assert response.headers["Cache-Control"] == "private, no-store"


def test_admin_can_view_complaint_image(tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))
    filename = "c" * 32 + ".jpg"
    (tmp_path / filename).write_bytes(b"test image bytes")

    create_admin()
    complaint = create_complaint()
    complaint.image_filename = filename
    db.session.commit()

    with app.test_client() as client:
        login_response = client.post(
            "/admin/login",
            data={
                "email": "testadmin@example.com",
                "password": "TestPassword123",
            },
        )
        assert login_response.status_code == 302

        response = client.get(f"/uploads/{filename}")
        assert response.status_code == 200
        assert response.data == b"test image bytes"



def test_session_cookie_security_configuration():
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert isinstance(app.config["SESSION_COOKIE_SECURE"], bool)
    assert app.config["PERMANENT_SESSION_LIFETIME"].total_seconds() == 30 * 60


def test_successful_tracking_uses_a_permanent_session():
    complaint = create_complaint()

    with app.test_client() as client:
        authorize_complaint(client, complaint)
        with client.session_transaction() as browser_session:
            assert browser_session.permanent is True
            assert browser_session["authorized_tracking_code"] == complaint.tracking_code


def test_failed_new_tracking_attempt_clears_previous_authorization():
    complaint = create_complaint()

    with app.test_client() as client:
        authorize_complaint(client, complaint)
        response = client.post(
            "/track",
            data={
                "tracking_code": complaint.tracking_code,
                "phone_last4": "9999",
            },
        )
        assert response.status_code == 200

        with client.session_transaction() as browser_session:
            assert "authorized_tracking_code" not in browser_session


def test_admin_login_starts_fresh_permanent_session():
    create_admin()

    with app.test_client() as client:
        with client.session_transaction() as browser_session:
            browser_session["authorized_tracking_code"] = "CT-OLDTRACK123"

        response = client.post(
            "/admin/login",
            data={
                "email": "testadmin@example.com",
                "password": "TestPassword123",
            },
        )
        assert response.status_code == 302

        with client.session_transaction() as browser_session:
            assert browser_session.permanent is True
            assert browser_session.get("_user_id") is not None
            assert "authorized_tracking_code" not in browser_session


def test_admin_logout_clears_staff_and_citizen_session_data():
    create_admin()

    with app.test_client() as client:
        login_response = client.post(
            "/admin/login",
            data={
                "email": "testadmin@example.com",
                "password": "TestPassword123",
            },
        )
        assert login_response.status_code == 302

        with client.session_transaction() as browser_session:
            browser_session["authorized_tracking_code"] = "CT-OLDTRACK123"

        logout_response = client.get("/admin/logout")
        assert logout_response.status_code == 302

        with client.session_transaction() as browser_session:
            assert "_user_id" not in browser_session
            assert "authorized_tracking_code" not in browser_session

        dashboard_response = client.get("/admin/dashboard")
        assert dashboard_response.status_code == 302
        assert "/admin/login" in dashboard_response.location
