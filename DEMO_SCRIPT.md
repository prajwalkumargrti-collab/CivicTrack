# CivicTrack — 60–90 second judge demonstration

Use synthetic demo records only. Say clearly that this is a prototype and is not connected to BBMP or another municipal authority.

## Story

**0–10 seconds — The resident's problem**

“Imagine a resident sees a dangerous pothole near a bus stop. They do not know whether the issue has been reported, who is handling it, or whether it will be fixed.”

**10–25 seconds — Report the issue**

Open the citizen portal. Switch to Kannada or Hindi. Open Report an issue. Select Road Damage, enter a concise description, severity, ward and address. Use the map pin or manual coordinates. Demonstrate the microphone button if the browser supports speech recognition. Submit the report and point out the tracking reference.

**25–40 seconds — Show duplicate awareness**

Submit a second similar report at a nearby coordinate. Explain that CivicTrack uses same-category filtering, geographic distance and TF-IDF/cosine text similarity to flag a possible duplicate. Emphasise that a flag is only a recommendation for officer review; the system does not discard a citizen report.

**40–50 seconds — Community confirmation**

Open the public tracking page and add one community confirmation. Show the updated count and explain how confirmations contribute to the transparent priority score.

**50–70 seconds — Officer action**

Sign in to the officer portal. Show the KPI cards, category/status charts, geotagged map and complaint queue. Update the report status with an officer note.

**70–90 seconds — Public transparency and value**

Return to the public tracking page. Show the updated status and activity timeline. Close with: “CivicTrack connects a resident report to community context, officer action and a visible status history in one traceable workflow.”

## Demo safeguards

- Use the seeded sample records or records created during the demo; identify them as synthetic.
- Do not claim the application sends a report to a government body, dispatches a repair crew, or guarantees a response time.
- Do not call the priority score an official emergency assessment. It is an explainable prototype decision-support score.
- Do not call the duplicate flag a definitive duplicate. It is a candidate for human review.
- Voice input depends on browser speech-recognition support and microphone permission. Always have a typed description ready.
- If map tiles fail, use the address and manually entered coordinates; explain that map tiles require internet access.
