"""Insert clearly labelled sample complaints for the judge demo. Safe to run repeatedly."""
from datetime import datetime, timedelta
from app import app, db, Complaint, ComplaintEvent, CATEGORIES, priority_for

SAMPLES = [
    dict(code='CT-DEMO1001', name='Ananya Rao', phone='4821', category='Pothole / Road Damage', description='A deep pothole near the school gate is forcing two-wheelers into moving traffic. A minor collision was reported yesterday.', address='12th Main Road, Indiranagar, Bengaluru', ward='Ward 81 · Indiranagar', lat=12.9784, lon=77.6408, severity='Critical', status='In Progress', votes=4, days=3),
    dict(code='CT-DEMO1002', name='Ramesh K', phone='1934', category='Garbage / Illegal Dumping', description='Garbage has been overflowing beside the community market for three days and stray animals are scattering waste.', address='CMH Road Market, Indiranagar, Bengaluru', ward='Ward 81 · Indiranagar', lat=12.9752, lon=77.6415, severity='High', status='Under Review', votes=2, days=2),
    dict(code='CT-DEMO1003', name='Farah S', phone='6720', category='Broken Streetlight', description='Streetlight at the bus stop is not working. The stretch becomes very dark after 7 PM and pedestrians cannot see the footpath.', address='100 Feet Road Bus Stop, Indiranagar, Bengaluru', ward='Ward 81 · Indiranagar', lat=12.9719, lon=77.6412, severity='High', status='Assigned', votes=3, days=1),
    dict(code='CT-DEMO1004', name='Manoj P', phone='8456', category='Water Leakage', description='A continuous water leak is wasting water outside the apartment entrance and making the road slippery.', address='HAL 2nd Stage, Bengaluru', ward='Ward  HAL 2nd Stage', lat=12.9669, lon=77.6483, severity='Medium', status='Resolved', votes=1, days=8),
    dict(code='CT-DEMO1005', name='Lakshmi N', phone='2309', category='Blocked Drain', description='The roadside drain is blocked and water is collecting near the pedestrian crossing whenever it rains.', address='Domlur Flyover Service Road, Bengaluru', ward='Ward 112 · Domlur', lat=12.9609, lon=77.6387, severity='High', status='Submitted', votes=0, days=0),
    dict(code='CT-DEMO1006', name='Joseph D', phone='1128', category='Footpath / Accessibility', description='The footpath ramp is broken and wheelchair users have to move onto the road to cross this junction.', address='Old Airport Road Junction, Bengaluru', ward='Ward 112 · Domlur', lat=12.9594, lon=77.6471, severity='High', status='Resolved', votes=5, days=12),
]

with app.app_context():
    added = 0
    for item in SAMPLES:
        if Complaint.query.filter_by(tracking_code=item['code']).first():
            continue
        score, label = priority_for(item['category'], item['severity'], item['description'], item['votes'])
        c = Complaint(
            tracking_code=item['code'], citizen_name=item['name'], phone_last4=item['phone'],
            category=item['category'], description='[DEMO DATA] ' + item['description'],
            address=item['address'], ward=item['ward'], latitude=item['lat'], longitude=item['lon'],
            severity=item['severity'], status=item['status'], priority_score=score,
            priority_label=label, verification_count=item['votes'],
            created_at=datetime.utcnow()-timedelta(days=item['days'])
        )
        db.session.add(c); db.session.flush()
        db.session.add(ComplaintEvent(complaint_id=c.id, status='Submitted', note='Sample report created for demonstration.', actor='Demo seed'))
        if item['status'] != 'Submitted':
            db.session.add(ComplaintEvent(complaint_id=c.id, status=item['status'], note='Sample status for demonstration; no real municipal action is implied.', actor='Demo seed'))
        added += 1
    db.session.commit()
    print(f'Added {added} demo complaints. Existing demo IDs were left unchanged.')
