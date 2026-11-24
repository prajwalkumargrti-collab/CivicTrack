from app import app, haversine_km, priority_for


def test_homepage_loads():
    app.config['TESTING'] = True
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        assert b'CivicTrack' in response.data


def test_haversine_same_point_is_zero():
    assert haversine_km(12.9716, 77.5946, 12.9716, 77.5946) == 0


def test_community_confirmations_raise_score():
    base, _ = priority_for('Pothole / Road Damage', 'Medium', 'Road has a pothole', 0)
    boosted, _ = priority_for('Pothole / Road Damage', 'Medium', 'Road has a pothole', 3)
    assert boosted > base


def test_invalid_coordinates_are_not_used_for_distance():
    assert haversine_km(0, 0, 0, 1) > 100


def test_bharat_ready_frontend_assets_exist():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert (root / 'static' / 'manifest.webmanifest').exists()
    assert (root / 'static' / 'sw.js').exists()
    js = (root / 'static' / 'js' / 'app.js').read_text(encoding='utf-8')
    assert "kn-IN" in js and "hi-IN" in js
    assert "civictrack-report-draft-v1" in js
    assert "voice-input" in js
