(function(){
  const $ = (s, root=document) => root.querySelector(s);
  const initMap = (el, items=[]) => {
    if (!el || !window.L) { if(el) el.textContent='Map preview requires an internet connection. Location details remain available in the report.'; return; }
    const map=L.map(el,{scrollWheelZoom:false}).setView([12.9716,77.5946],12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
    const bounds=[];
    items.filter(x=>x.lat!==null&&x.lon!==null&&x.lat!==''&&x.lon!=='').forEach(x=>{
      const color=x.status==='Resolved'?'#0b9b8f':'#e58b50';
      const marker=L.circleMarker([Number(x.lat),Number(x.lon)],{radius:8,color:'#fff',weight:2,fillColor:color,fillOpacity:1}).addTo(map);
      marker.bindPopup(`<b>${escapeHtml(x.id||'Complaint')}</b><br>${escapeHtml(x.category||'Civic issue')}<br>Status: ${escapeHtml(x.status||'Submitted')}<br>Priority: ${escapeHtml(x.priority||'—')}`);
      bounds.push([Number(x.lat),Number(x.lon)]);
    });
    if(bounds.length>1) map.fitBounds(bounds,{padding:[25,25],maxZoom:14}); else if(bounds.length===1) map.setView(bounds[0],15);
    else if(el.dataset.empty){const note=document.createElement('div');note.className='map-empty-note';note.textContent=el.dataset.empty;el.appendChild(note);}
    setTimeout(()=>map.invalidateSize(),150);
    return map;
  };
  const escapeHtml = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  document.addEventListener('DOMContentLoaded',()=>{
    const publicMap=$('#public-map'); if(publicMap) initMap(publicMap,JSON.parse(publicMap.dataset.mapItems||'[]'));
    const adminMap=$('#admin-map'); if(adminMap) initMap(adminMap,JSON.parse(adminMap.dataset.mapItems||'[]'));
    const detailMap=$('#detail-map'); if(detailMap){const lat=detailMap.dataset.lat,lon=detailMap.dataset.lon;if(lat&&lon)initMap(detailMap,[{id:'Reported location',category:'Complaint',status:'Submitted',lat,lon}]);else detailMap.textContent='No map coordinates were provided for this report.';}
    const reportMap=$('#report-map');
    if(reportMap&&window.L){const map=L.map(reportMap,{scrollWheelZoom:false}).setView([12.9716,77.5946],12);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap'}).addTo(map);let marker=null;const latInput=$('#latitude'),lonInput=$('#longitude');const place=(lat,lon)=>{latInput.value=lat.toFixed(6);lonInput.value=lon.toFixed(6);if(marker)marker.setLatLng([lat,lon]);else marker=L.marker([lat,lon],{draggable:true}).addTo(map);marker.on('dragend',e=>{const p=e.target.getLatLng();latInput.value=p.lat.toFixed(6);lonInput.value=p.lng.toFixed(6);});map.setView([lat,lon],16);};map.on('click',e=>place(e.latlng.lat,e.latlng.lng));$('#locate-me')?.addEventListener('click',()=>{if(!navigator.geolocation){alert('Geolocation is not supported by this browser.');return;}navigator.geolocation.getCurrentPosition(pos=>place(pos.coords.latitude,pos.coords.longitude),()=>alert('Could not access location. Allow location permission or click the map.'),{enableHighAccuracy:true,timeout:10000});});[latInput,lonInput].forEach(input=>input.addEventListener('change',()=>{const lat=parseFloat(latInput.value),lon=parseFloat(lonInput.value);if(Number.isFinite(lat)&&Number.isFinite(lon)&&Math.abs(lat)<=90&&Math.abs(lon)<=180){if(marker)marker.setLatLng([lat,lon]);else marker=L.marker([lat,lon],{draggable:true}).addTo(map);map.setView([lat,lon],15);}}));setTimeout(()=>map.invalidateSize(),150);}
    $('#photo-input')?.addEventListener('change',e=>{$('#upload-filename').textContent=e.target.files[0]?.name||'No file selected';});
    document.querySelectorAll('[data-copy]').forEach(btn=>btn.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(btn.dataset.copy);btn.textContent='Copied!';}catch(e){btn.textContent=btn.dataset.copy;} }));
    if(window.CIVICTRACK_CHARTS&&window.Chart){const c=window.CIVICTRACK_CHARTS;const palette=['#0b9b8f','#f2a65a','#5b8db8','#8a79b8','#d87865','#73a6a0','#9aa9b2'];const cat=$('#category-chart');if(cat)new Chart(cat,{type:'bar',data:{labels:c.categories.labels,datasets:[{data:c.categories.values,backgroundColor:palette,borderRadius:6,maxBarThickness:30}]},options:{maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{font:{size:9},maxRotation:35}},y:{beginAtZero:true,ticks:{precision:0,font:{size:9}},grid:{color:'#edf1f2'}}}}});const st=$('#status-chart');if(st)new Chart(st,{type:'doughnut',data:{labels:c.statuses.labels,datasets:[{data:c.statuses.values,backgroundColor:palette,borderWidth:3,borderColor:'#fff',hoverOffset:5}]},options:{maintainAspectRatio:false,cutout:'67%',plugins:{legend:{position:'bottom',labels:{boxWidth:9,padding:12,font:{size:9}}}}}});}
  });
})();

/* Build for Bharat: language support, voice-assisted reporting and draft recovery. */
(function () {
  const translations = {
    en: {
      nav_home:'Home', nav_report:'Report an issue', nav_track:'Track complaint', nav_officer:'Officer portal ↗',
      report_title:'Report a civic issue', report_intro:'Give your local team the details they need to act. Fields marked * are required.',
      issue_details:'Issue details', issue_prompt:'What is happening in your area?', category_label:'Issue category', select_issue:'Select issue type',
      describe_label:'Describe the issue', describe_placeholder:'Describe the problem, nearby landmark and how it affects people...',
      describe_help:'Be specific. Mention nearby landmarks and how the issue affects people. Minimum 20 characters.',
      voice_start:'Speak description', voice_stop:'Stop listening', voice_hint:'Voice input works in supported browsers. Your microphone audio is not uploaded.',
      voice_listening:'Listening… speak clearly.', voice_unsupported:'Voice input is not supported in this browser. You can type your description.',
      voice_denied:'Microphone permission was denied. Allow microphone access or type your description.', voice_error:'Could not capture speech. Please try again or type your description.',
      severity_label:'How urgent is it?', ward_label:'Ward / area', ward_placeholder:'e.g. Ward 42 / Indiranagar',
      location_title:'Where is it?', location_help:'Pin the exact location or enter an address.', address_label:'Street address / landmark',
      address_placeholder:'Street, landmark, locality, city', map_location:'Map location (recommended)', use_location:'◎ Use my location',
      photo_title:'Photo evidence', photo_help:'A clear photo helps the officer assess the issue.', photo_choose:'Choose a photo or take one',
      photo_limit:'JPG, PNG or WEBP · Maximum 5 MB · Optional', contact_title:'Your contact details',
      contact_help:'Used only to protect access to your tracking record.', name_label:'Your name', name_placeholder:'Full name',
      mobile_label:'Mobile number', mobile_placeholder:'10-digit mobile number', cancel:'Cancel', submit_complaint:'Submit complaint',
      draft_saved:'Draft saved on this device. It will remain here if your connection drops.', draft_restored:'Your saved draft was restored.',
      online:'You are back online. Your draft is safe; submit it when ready.', offline:'You are offline. Your draft is being saved on this device.',
      track_title:'Know where things stand.', track_intro:'Your report deserves a response. Check its current status and see every recorded update.', track_heading:'Track your report', track_help:'Enter the tracking code from your submission receipt and the last four digits of your mobile number.', tracking_code_label:'Tracking code', phone_last4_label:'Last 4 digits of mobile', find_complaint:'Find my complaint →', home_eyebrow:'A MORE RESPONSIVE CITY STARTS HERE', home_title:'See an issue? Make it visible.', home_lead:'Report potholes, overflowing garbage, broken streetlights and other civic issues. Follow every update — from the first report to resolution.', home_report:'＋ Report a civic issue', home_track:'Track a complaint →', how_title:'From street-level issue to visible action.', how_intro:'A simple, accountable workflow designed for residents and the teams who serve them.', step_report:'Report with context', step_confirm:'Community confirms', step_track:'Track the response', cat_pothole:'Pothole / Road Damage', cat_garbage:'Garbage / Illegal Dumping', cat_light:'Broken Streetlight', cat_water:'Water Leakage', cat_drain:'Blocked Drain', cat_footpath:'Footpath / Accessibility', cat_other:'Other', low:'Low', medium:'Medium', high:'High', critical:'Critical'
    },
    kn: {
      nav_home:'ಮುಖಪುಟ', nav_report:'ಸಮಸ್ಯೆ ವರದಿ', nav_track:'ದೂರು ಪರಿಶೀಲಿಸಿ', nav_officer:'ಅಧಿಕಾರಿ ಪೋರ್ಟಲ್ ↗',
      report_title:'ನಾಗರಿಕ ಸಮಸ್ಯೆಯನ್ನು ವರದಿ ಮಾಡಿ', report_intro:'ಕ್ರಮ ಕೈಗೊಳ್ಳಲು ನಿಮ್ಮ ಸ್ಥಳೀಯ ತಂಡಕ್ಕೆ ಅಗತ್ಯವಾದ ವಿವರಗಳನ್ನು ನೀಡಿ. * ಗುರುತಿನ ಕ್ಷೇತ್ರಗಳು ಕಡ್ಡಾಯ.',
      issue_details:'ಸಮಸ್ಯೆಯ ವಿವರಗಳು', issue_prompt:'ನಿಮ್ಮ ಪ್ರದೇಶದಲ್ಲಿ ಏನು ಸಮಸ್ಯೆ ಇದೆ?', category_label:'ಸಮಸ್ಯೆಯ ವರ್ಗ', select_issue:'ಸಮಸ್ಯೆಯ ಪ್ರಕಾರ ಆಯ್ಕೆಮಾಡಿ',
      describe_label:'ಸಮಸ್ಯೆಯನ್ನು ವಿವರಿಸಿ', describe_placeholder:'ಸಮಸ್ಯೆ, ಹತ್ತಿರದ ಗುರುತು ಮತ್ತು ಜನರ ಮೇಲೆ ಅದರ ಪರಿಣಾಮವನ್ನು ವಿವರಿಸಿ...',
      describe_help:'ಸ್ಪಷ್ಟವಾಗಿ ವಿವರಿಸಿ. ಹತ್ತಿರದ ಸ್ಥಳ ಗುರುತುಗಳನ್ನು ತಿಳಿಸಿ. ಕನಿಷ್ಠ 20 ಅಕ್ಷರಗಳು.',
      voice_start:'ಮಾತನಾಡಿ ವಿವರಿಸಿ', voice_stop:'ಕೇಳುವುದನ್ನು ನಿಲ್ಲಿಸಿ', voice_hint:'ಬೆಂಬಲಿತ ಬ್ರೌಸರ್‌ಗಳಲ್ಲಿ ಧ್ವನಿ ಇನ್‌ಪುಟ್ ಲಭ್ಯ. ನಿಮ್ಮ ಧ್ವನಿ ಅಪ್‌ಲೋಡ್ ಆಗುವುದಿಲ್ಲ.',
      voice_listening:'ಕೇಳಲಾಗುತ್ತಿದೆ… ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ.', voice_unsupported:'ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಧ್ವನಿ ಇನ್‌ಪುಟ್ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ಟೈಪ್ ಮಾಡಿ.',
      voice_denied:'ಮೈಕ್ರೊಫೋನ್ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ. ಅನುಮತಿ ನೀಡಿ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ.', voice_error:'ಧ್ವನಿಯನ್ನು ಗುರುತಿಸಲಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ.',
      severity_label:'ಸಮಸ್ಯೆಯ ತುರ್ತು ಮಟ್ಟ', ward_label:'ವಾರ್ಡ್ / ಪ್ರದೇಶ', ward_placeholder:'ಉದಾ. ವಾರ್ಡ್ 42 / ಇಂದಿರಾನಗರ',
      location_title:'ಸಮಸ್ಯೆ ಎಲ್ಲಿದೆ?', location_help:'ನಕ್ಷೆಯಲ್ಲಿ ಸ್ಥಳ ಗುರುತಿಸಿ ಅಥವಾ ವಿಳಾಸ ನಮೂದಿಸಿ.', address_label:'ರಸ್ತೆ ವಿಳಾಸ / ಸ್ಥಳ ಗುರುತು',
      address_placeholder:'ರಸ್ತೆ, ಸ್ಥಳ ಗುರುತು, ಪ್ರದೇಶ, ನಗರ', map_location:'ನಕ್ಷೆಯ ಸ್ಥಳ (ಶಿಫಾರಸು)', use_location:'◎ ನನ್ನ ಸ್ಥಳ ಬಳಸಿ',
      photo_title:'ಛಾಯಾಚಿತ್ರ ಸಾಕ್ಷಿ', photo_help:'ಸ್ಪಷ್ಟವಾದ ಚಿತ್ರವು ಅಧಿಕಾರಿಗೆ ಸಮಸ್ಯೆಯನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ.', photo_choose:'ಚಿತ್ರ ಆಯ್ಕೆಮಾಡಿ ಅಥವಾ ತೆಗೆಯಿರಿ',
      photo_limit:'JPG, PNG ಅಥವಾ WEBP · ಗರಿಷ್ಠ 5 MB · ಐಚ್ಛಿಕ', contact_title:'ನಿಮ್ಮ ಸಂಪರ್ಕ ವಿವರಗಳು',
      contact_help:'ನಿಮ್ಮ ದೂರಿನ ಟ್ರ್ಯಾಕಿಂಗ್ ದಾಖಲೆಗೆ ಪ್ರವೇಶವನ್ನು ರಕ್ಷಿಸಲು ಮಾತ್ರ ಬಳಸಲಾಗುತ್ತದೆ.', name_label:'ನಿಮ್ಮ ಹೆಸರು', name_placeholder:'ಪೂರ್ಣ ಹೆಸರು',
      mobile_label:'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ', mobile_placeholder:'10 ಅಂಕಿಯ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ', cancel:'ರದ್ದುಮಾಡಿ', submit_complaint:'ದೂರು ಸಲ್ಲಿಸಿ',
      draft_saved:'ಈ ಸಾಧನದಲ್ಲಿ ಕರಡು ಉಳಿಸಲಾಗಿದೆ. ಸಂಪರ್ಕ ಕಡಿತವಾದರೂ ಇದು ಉಳಿಯುತ್ತದೆ.', draft_restored:'ನಿಮ್ಮ ಉಳಿಸಿದ ಕರಡನ್ನು ಮರುಸ್ಥಾಪಿಸಲಾಗಿದೆ.',
      online:'ಮತ್ತೆ ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಲಭ್ಯ. ನಿಮ್ಮ ಕರಡು ಸುರಕ್ಷಿತವಾಗಿದೆ.', offline:'ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಇಲ್ಲ. ಕರಡು ಈ ಸಾಧನದಲ್ಲಿ ಉಳಿಸಲಾಗುತ್ತಿದೆ.',
      track_title:'ನಿಮ್ಮ ದೂರಿನ ಸ್ಥಿತಿಯನ್ನು ತಿಳಿಯಿರಿ.', track_intro:'ನಿಮ್ಮ ವರದಿಗೆ ಪ್ರತಿಕ್ರಿಯೆ ಸಿಗಬೇಕು. ಪ್ರಸ್ತುತ ಸ್ಥಿತಿ ಮತ್ತು ಎಲ್ಲಾ ನವೀಕರಣಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.', track_heading:'ನಿಮ್ಮ ದೂರನ್ನು ಪರಿಶೀಲಿಸಿ', track_help:'ನಿಮ್ಮ ವರದಿ ಸ್ವೀಕೃತಿ ಪತ್ರದಲ್ಲಿರುವ ಟ್ರ್ಯಾಕಿಂಗ್ ಕೋಡ್ ಮತ್ತು ಮೊಬೈಲ್‌ನ ಕೊನೆಯ ನಾಲ್ಕು ಅಂಕೆಗಳನ್ನು ನಮೂದಿಸಿ.', tracking_code_label:'ಟ್ರ್ಯಾಕಿಂಗ್ ಕೋಡ್', phone_last4_label:'ಮೊಬೈಲ್‌ನ ಕೊನೆಯ 4 ಅಂಕೆಗಳು', find_complaint:'ನನ್ನ ದೂರನ್ನು ಹುಡುಕಿ →', home_eyebrow:'ಉತ್ತಮವಾಗಿ ಸ್ಪಂದಿಸುವ ನಗರ ಇಲ್ಲಿಂದ ಆರಂಭವಾಗುತ್ತದೆ', home_title:'ಸಮಸ್ಯೆ ಕಂಡಿದೆಯೇ? ಅದನ್ನು ವರದಿ ಮಾಡಿ.', home_lead:'ಗುಂಡಿಗಳು, ತುಂಬಿದ ಕಸ, ಕೆಟ್ಟ ಬೀದಿ ದೀಪಗಳು ಮತ್ತು ಇತರ ನಾಗರಿಕ ಸಮಸ್ಯೆಗಳನ್ನು ವರದಿ ಮಾಡಿ. ವರದಿಯಿಂದ ಪರಿಹಾರವರೆಗೆ ಪ್ರತಿಯೊಂದು ನವೀಕರಣವನ್ನು ಗಮನಿಸಿ.', home_report:'＋ ನಾಗರಿಕ ಸಮಸ್ಯೆ ವರದಿ', home_track:'ದೂರನ್ನು ಪರಿಶೀಲಿಸಿ →', how_title:'ರಸ್ತೆಯ ಸಮಸ್ಯೆಯಿಂದ ಕಾಣುವ ಕ್ರಮದವರೆಗೆ.', how_intro:'ನಿವಾಸಿಗಳು ಮತ್ತು ಸೇವೆ ಒದಗಿಸುವ ತಂಡಗಳಿಗಾಗಿ ಸರಳ, ಹೊಣೆಗಾರಿಕೆಯ ಕಾರ್ಯವಿಧಾನ.', step_report:'ವಿವರಗಳೊಂದಿಗೆ ವರದಿ ಮಾಡಿ', step_confirm:'ಸಮುದಾಯ ದೃಢೀಕರಿಸುತ್ತದೆ', step_track:'ಪ್ರತಿಕ್ರಿಯೆಯನ್ನು ಪರಿಶೀಲಿಸಿ', cat_pothole:'ಗುಂಡಿ / ರಸ್ತೆ ಹಾನಿ', cat_garbage:'ಕಸ / ಅಕ್ರಮ ತ್ಯಾಜ್ಯ', cat_light:'ಕೆಟ್ಟುಹೋದ ಬೀದಿ ದೀಪ', cat_water:'ನೀರಿನ ಸೋರಿಕೆ', cat_drain:'ಮುಚ್ಚಿಹೋದ ಚರಂಡಿ', cat_footpath:'ಪಾದಚಾರಿ ಮಾರ್ಗ / ಪ್ರವೇಶಸೌಲಭ್ಯ', cat_other:'ಇತರೆ', low:'ಕಡಿಮೆ', medium:'ಮಧ್ಯಮ', high:'ಹೆಚ್ಚು', critical:'ಅತ್ಯಂತ ತುರ್ತು'
    },
    hi: {
      nav_home:'होम', nav_report:'समस्या दर्ज करें', nav_track:'शिकायत ट्रैक करें', nav_officer:'अधिकारी पोर्टल ↗',
      report_title:'नागरिक समस्या दर्ज करें', report_intro:'कार्रवाई के लिए अपनी स्थानीय टीम को आवश्यक जानकारी दें। * वाले फ़ील्ड अनिवार्य हैं।',
      issue_details:'समस्या का विवरण', issue_prompt:'आपके क्षेत्र में क्या समस्या है?', category_label:'समस्या की श्रेणी', select_issue:'समस्या का प्रकार चुनें',
      describe_label:'समस्या का वर्णन करें', describe_placeholder:'समस्या, नज़दीकी पहचान और लोगों पर इसके प्रभाव का वर्णन करें...',
      describe_help:'स्पष्ट जानकारी दें। पास के लैंडमार्क बताएं। कम से कम 20 अक्षर।',
      voice_start:'बोलकर बताएं', voice_stop:'सुनना बंद करें', voice_hint:'वॉइस इनपुट समर्थित ब्राउज़र में काम करता है। आपकी आवाज़ अपलोड नहीं होती।',
      voice_listening:'सुन रहे हैं… स्पष्ट बोलें।', voice_unsupported:'इस ब्राउज़र में वॉइस इनपुट उपलब्ध नहीं है। कृपया टाइप करें।',
      voice_denied:'माइक्रोफ़ोन की अनुमति नहीं मिली। अनुमति दें या टाइप करें।', voice_error:'आवाज़ समझ नहीं आई। फिर प्रयास करें या टाइप करें।',
      severity_label:'समस्या कितनी गंभीर है?', ward_label:'वार्ड / क्षेत्र', ward_placeholder:'उदा. वार्ड 42 / इंदिरानगर',
      location_title:'समस्या कहाँ है?', location_help:'नक्शे पर स्थान चुनें या पता दर्ज करें।', address_label:'सड़क का पता / पहचान',
      address_placeholder:'सड़क, लैंडमार्क, इलाका, शहर', map_location:'नक्शे पर स्थान (अनुशंसित)', use_location:'◎ मेरा स्थान उपयोग करें',
      photo_title:'फ़ोटो प्रमाण', photo_help:'स्पष्ट फ़ोटो अधिकारी को समस्या समझने में मदद करती है।', photo_choose:'फ़ोटो चुनें या लें',
      photo_limit:'JPG, PNG या WEBP · अधिकतम 5 MB · वैकल्पिक', contact_title:'आपकी संपर्क जानकारी',
      contact_help:'इसका उपयोग केवल आपकी ट्रैकिंग जानकारी तक पहुँच सुरक्षित रखने के लिए किया जाता है।', name_label:'आपका नाम', name_placeholder:'पूरा नाम',
      mobile_label:'मोबाइल नंबर', mobile_placeholder:'10 अंकों का मोबाइल नंबर', cancel:'रद्द करें', submit_complaint:'शिकायत दर्ज करें',
      draft_saved:'ड्राफ़्ट इस डिवाइस पर सेव है। कनेक्शन टूटने पर भी यह रहेगा।', draft_restored:'आपका सेव किया हुआ ड्राफ़्ट वापस लाया गया है।',
      online:'इंटरनेट वापस आ गया है। आपका ड्राफ़्ट सुरक्षित है।', offline:'आप ऑफ़लाइन हैं। ड्राफ़्ट इस डिवाइस पर सेव हो रहा है।',
      track_title:'अपनी शिकायत की स्थिति जानें।', track_intro:'आपकी रिपोर्ट पर जवाब मिलना चाहिए। वर्तमान स्थिति और सभी अपडेट देखें।', track_heading:'अपनी रिपोर्ट ट्रैक करें', track_help:'अपनी रसीद पर दिया गया ट्रैकिंग कोड और मोबाइल नंबर के आखिरी चार अंक दर्ज करें।', tracking_code_label:'ट्रैकिंग कोड', phone_last4_label:'मोबाइल के आखिरी 4 अंक', find_complaint:'मेरी शिकायत खोजें →', home_eyebrow:'बेहतर प्रतिक्रिया देने वाला शहर यहीं से शुरू होता है', home_title:'समस्या दिखी? उसे दर्ज करें।', home_lead:'गड्ढे, कचरे का ढेर, खराब स्ट्रीट लाइट और अन्य नागरिक समस्याएँ दर्ज करें। पहली रिपोर्ट से समाधान तक हर अपडेट देखें।', home_report:'＋ नागरिक समस्या दर्ज करें', home_track:'शिकायत ट्रैक करें →', how_title:'सड़क की समस्या से दिखने वाली कार्रवाई तक।', how_intro:'निवासियों और सेवा देने वाली टीमों के लिए सरल और जवाबदेह प्रक्रिया।', step_report:'विवरण के साथ रिपोर्ट करें', step_confirm:'समुदाय पुष्टि करता है', step_track:'कार्रवाई ट्रैक करें', cat_pothole:'गड्ढा / सड़क की क्षति', cat_garbage:'कचरा / अवैध डंपिंग', cat_light:'खराब स्ट्रीट लाइट', cat_water:'पानी का रिसाव', cat_drain:'बंद नाली', cat_footpath:'फुटपाथ / सुगम्यता', cat_other:'अन्य', low:'कम', medium:'मध्यम', high:'उच्च', critical:'अत्यंत गंभीर'
    }
  };

  const getLang = () => localStorage.getItem('civictrack-language') || 'en';
  const t = (key) => (translations[getLang()] || translations.en)[key] || translations.en[key] || key;
  const applyLanguage = (lang) => {
    if (!translations[lang]) lang = 'en';
    localStorage.setItem('civictrack-language', lang);
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
    const categoryLabels = {'Pothole / Road Damage':'cat_pothole','Garbage / Illegal Dumping':'cat_garbage','Broken Streetlight':'cat_light','Water Leakage':'cat_water','Blocked Drain':'cat_drain','Footpath / Accessibility':'cat_footpath','Other':'cat_other'};
    document.querySelectorAll('select[name=category] option').forEach(option => { if(categoryLabels[option.value]) option.textContent=t(categoryLabels[option.value]); });
    document.querySelectorAll('select[name=severity] option').forEach(option => { const key=option.value.toLowerCase(); if(['low','medium','high','critical'].includes(key)) option.textContent=t(key); });
    const switcher = document.getElementById('language-switcher');
    if (switcher) switcher.value = lang;
    const voiceLabel = document.querySelector('#voice-input [data-i18n]');
    if (voiceLabel) voiceLabel.textContent = t('voice_start');
  };

  document.addEventListener('DOMContentLoaded', () => {
    applyLanguage(getLang());
    document.getElementById('language-switcher')?.addEventListener('change', e => applyLanguage(e.target.value));

    const form = document.querySelector('form.form-card');
    if (form) {
      const draftKey = 'civictrack-report-draft-v1';
      const fields = ['category','description','severity','ward','address','latitude','longitude'];
      const status = document.createElement('p');
      status.className = 'micro-note draft-status';
      status.setAttribute('role','status');
      form.prepend(status);
      const saveDraft = () => {
        const data = {};
        fields.forEach(name => { const el=form.elements.namedItem(name); if(el) data[name]=el.value; });
        try { localStorage.setItem(draftKey, JSON.stringify(data)); status.textContent=t('draft_saved'); } catch (_) {}
      };
      try {
        const saved = JSON.parse(localStorage.getItem(draftKey) || 'null');
        if (saved) {
          fields.forEach(name => { const el=form.elements.namedItem(name); if(el && saved[name] !== undefined) el.value=saved[name]; });
          status.textContent=t('draft_restored');
        }
      } catch (_) {}
      form.addEventListener('input', saveDraft);
      form.addEventListener('change', saveDraft);
      form.addEventListener('submit', () => { saveDraft(); });
      window.addEventListener('online', () => { status.textContent=t('online'); });
      window.addEventListener('offline', () => { status.textContent=t('offline'); });
      if (!navigator.onLine) status.textContent=t('offline');
    }

    const voiceButton = document.getElementById('voice-input');
    const description = document.querySelector('textarea[name="description"]');
    const voiceStatus = document.getElementById('voice-status');
    if (voiceButton && description && voiceStatus) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      let recognition = null;
      if (!SpeechRecognition) {
        voiceButton.addEventListener('click', () => { voiceStatus.textContent=t('voice_unsupported'); voiceStatus.classList.add('is-error'); });
      } else {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.onstart = () => { voiceButton.setAttribute('aria-pressed','true'); voiceButton.querySelector('span').textContent=t('voice_stop'); voiceStatus.textContent=t('voice_listening'); voiceStatus.classList.add('is-listening'); voiceStatus.classList.remove('is-error'); };
        recognition.onresult = (event) => {
          let finalText = '';
          for (let i=event.resultIndex; i<event.results.length; i++) if(event.results[i].isFinal) finalText += event.results[i][0].transcript + ' ';
          if (finalText) { description.value = (description.value.trim() + ' ' + finalText.trim()).trim(); description.dispatchEvent(new Event('input',{bubbles:true})); }
        };
        recognition.onerror = (event) => { voiceStatus.textContent = event.error === 'not-allowed' ? t('voice_denied') : t('voice_error'); voiceStatus.classList.add('is-error'); };
        recognition.onend = () => { voiceButton.setAttribute('aria-pressed','false'); voiceButton.querySelector('span').textContent=t('voice_start'); voiceStatus.classList.remove('is-listening'); };
        voiceButton.addEventListener('click', () => {
          if (voiceButton.getAttribute('aria-pressed') === 'true') { recognition.stop(); return; }
          recognition.lang = getLang() === 'kn' ? 'kn-IN' : getLang() === 'hi' ? 'hi-IN' : 'en-IN';
          try { recognition.start(); } catch (_) { voiceStatus.textContent=t('voice_error'); }
        });
      }
    }

    const formEl = document.querySelector('form.form-card');
    if (formEl && location.pathname.includes('/report/success') === false) {
      // Keep draft on validation/network failure; successful receipt page clears it below.
    }
    if (location.pathname.includes('/report/success/')) localStorage.removeItem('civictrack-report-draft-v1');
  });
})();
