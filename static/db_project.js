let isGalleryActive = false; let galleryAnimationId;
let panTarget = 0; let currentPan = 0; let autoPanSpeed = 1.0; 
let isModalOpen = false; 

let isAdminGlobal = false;
let currentDetailArtId = null; let currentDetailArtPrice = 0; let isArtOwnerGlobal = false;
let currentInfoId = null; let currentInfoType = null; let isInfoOwnerGlobal = false;

let currentResId = null; let currentResTotalPrice = 0;
let currentResItemId = null; let currentResItemType = null;

let currentPayType = null; let currentPayId = null; let appliedCouponCode = null;

let currentCommentsData = [];
let currentReviewsData = [];
let currentUserGlobal = null;

function toggleForm() {
    var loginBox = document.getElementById("login-box"); var registerBox = document.getElementById("register-box");
    if (loginBox && registerBox) {
        if (loginBox.style.display !== "none") { loginBox.style.display = "none"; registerBox.style.display = "block"; } 
        else { loginBox.style.display = "block"; registerBox.style.display = "none"; }
    }
}
function toggleSidebar() {
    var sidebar = document.getElementById("sidebar"); var mainContent = document.getElementById("main-content");
    if (sidebar && mainContent) { sidebar.classList.toggle("active"); mainContent.classList.toggle("shifted"); }
}

function loadContent(pageName) {
    currentPageNameGlobal = pageName;
    fetch(`/api/content/${pageName}`).then(res => res.json()).then(data => {
        var dynamicContent = document.getElementById("dynamic-content"); var mainContent = document.getElementById("main-content"); 
        if(dynamicContent) {
            dynamicContent.innerHTML = data.html;
            isAdminGlobal = data.is_admin;
            if (data.sidebar) {
                var sidebarLinks = document.querySelector(".sidebar-links");
                if (sidebarLinks) sidebarLinks.innerHTML = data.sidebar;
            }
            if(pageName === 'gallery') {
                mainContent.classList.add('gallery-mode'); isGalleryActive = true; panTarget = 0; currentPan = 0; autoPanSpeed = 1.0; animateGallery();
            } else {
                mainContent.classList.remove('gallery-mode'); isGalleryActive = false; cancelAnimationFrame(galleryAnimationId);
            }
            
            if(pageName === 'admin_panel') {
                loadAdminChatUsers();
            }
            
            if(pageName === 'comparison') {
                loadSavedComparisons();
            }
            
            if(!isAdminGlobal) {
                startGlobalNotificationCheck();
            }

            let chatContainer = document.getElementById('live-chat-container');
            if(chatContainer) {
                chatContainer.style.display = (!isAdminGlobal && pageName === 'support') ? 'block' : 'none';
            }
            
            // Support sayfasına girildiyse bildirimleri temizle
            if(pageName === 'support') {
                let link = document.getElementById('sidebar-support-link');
                if(link) {
                    let dot = link.querySelector('.notification-dot');
                    if(dot) dot.style.display = 'none';
                }
                
                // Sayaçları güncelle (okundu say)
                if(!isAdminGlobal) {
                    fetch('/api/check_notifications').then(res => res.json()).then(data => {
                        if(data.success) {
                            lastSeenTicketReplyCount = data.ticket_count;
                            localStorage.setItem('lastSeenTicketReplyCount', lastSeenTicketReplyCount);
                            // Not: Chat sayacı sadece chat penceresi açılınca temizlenmeye devam eder (isteğe bağlı)
                            // Ancak isterseniz burada lastSeenAdminMsgCount = data.chat_count da yapabilirsiniz.
                            
                            // Eğer okunmamış mesaj varsa, butona noktanın hemen geçmesi için manuel tetikliyoruz
                            checkNotifications();
                        }
                    });
                }
            }
        }
    });
    if(window.innerWidth < 768) toggleSidebar();
}

function openAnyModal(modalId) { var modal = document.getElementById(modalId); if(modal) { modal.style.display = 'flex'; setTimeout(() => modal.classList.add('show'), 10); } }
function closeAnyModal(modalId) { var modal = document.getElementById(modalId); if(modal) { modal.classList.remove('show'); setTimeout(() => modal.style.display = 'none', 300); } }

function submitProfile(event) {
    event.preventDefault(); var formData = new FormData();
    formData.append('fullname', document.getElementById("prof-fullname").value); formData.append('email', document.getElementById("prof-email").value); formData.append('password', document.getElementById("prof-password").value);
    var fileInput = document.getElementById('profile-upload'); if (fileInput && fileInput.files[0]) formData.append('profile_img', fileInput.files[0]);
    fetch('/api/update_profile', { method: 'POST', body: formData }).then(res => res.json()).then(data => {
        var msgBox = document.getElementById("profile-message"); msgBox.textContent = data.message; msgBox.style.color = data.success ? "#27ae60" : "#e74c3c";
        if(data.success) document.getElementById("prof-password").value = ""; 
    });
}
function previewImage(event, targetId, textIdToHide = null) {
    var reader = new FileReader();
    reader.onload = function() { var output = document.getElementById(targetId); output.src = reader.result; output.style.display = 'block'; if(textIdToHide) document.getElementById(textIdToHide).style.display = 'none'; };
    if (event.target.files[0]) reader.readAsDataURL(event.target.files[0]);
}

function submitArt() {
    var title = document.getElementById('art-title').value; var cat = document.getElementById('art-cat').value; var desc = document.getElementById('art-desc').value; var price = document.getElementById('art-price').value; var fileInput = document.getElementById('art-file');
    if (!title || !cat || !desc || !price || !fileInput.files[0]) return alert("Eksik alan var.");
    var formData = new FormData(); formData.append('title', title); formData.append('category', cat); formData.append('desc', desc); formData.append('price', price); formData.append('art_image', fileInput.files[0]);
    fetch('/api/add_art', { method: 'POST', body: formData }).then(res => res.json()).then(data => { if(data.success) { closeAnyModal('art-modal'); loadContent('gallery'); } });
}

// --- KARŞILAŞTIRMA FONKSİYONLARI ---
let currentCompType = null;
let itemsToCompare = [];

function openComparisonSelector(type) {
    currentCompType = type;
    const title = type === 'art' ? 'Karşılaştırılacak Eserleri Seçin' : 'Karşılaştırılacak Etkinlikleri Seçin';
    document.getElementById('comp-selector-title').textContent = title;
    
    fetch(`/api/get_items_for_comparison/${type}`).then(res => res.json()).then(data => {
        if(data.success) {
            let html = '';
            data.items.forEach(item => {
                html += `
                <div style="display:flex; align-items:center; gap:10px; padding:10px; border-bottom:1px solid #eee;">
                    <input type="checkbox" class="comp-checkbox" value="${item.unique_id}" data-title="${item.title}">
                    <span style="font-size:14px;">${item.title}</span>
                </div>`;
            });
            document.getElementById('comp-selector-items').innerHTML = html || 'Öğe bulunamadı.';
            openAnyModal('comp-selector-modal');
        }
    });
}

function startComparison() {
    const checkboxes = document.querySelectorAll('.comp-checkbox:checked');
    if(checkboxes.length < 2) return alert("En az 2 öğe seçmelisiniz.");
    
    const ids = Array.from(checkboxes).map(cb => cb.value);
    renderComparisonTable(ids, currentCompType);
    closeAnyModal('comp-selector-modal');
}

function renderComparisonTable(ids, type) {
    fetch(`/api/get_items_for_comparison/${type}`).then(res => res.json()).then(data => {
        if(!data.success) return;
        const selectedItems = data.items.filter(item => ids.includes(item.unique_id) || ids.includes(String(item.id)));
        
        let html = '<table style="width:100%; border-collapse:collapse; background:white; border-radius:12px; overflow:hidden; box-shadow:0 5px 15px rgba(0,0,0,0.05);">';
        
        if(type === 'art') {
            html += `
                <tr style="background:#6a89cc; color:white;">
                    <th style="padding:15px; text-align:left;">Özellik</th>
                    ${selectedItems.map(item => `<th style="padding:15px;">${item.title}</th>`).join('')}
                </tr>
                <tr><td style="padding:15px; font-weight:bold; border-bottom:1px solid #eee;">Sanatçı</td>${selectedItems.map(item => `<td style="padding:15px; text-align:center; border-bottom:1px solid #eee;">${item.artist}</td>`).join('')}</tr>
                <tr><td style="padding:15px; font-weight:bold; border-bottom:1px solid #eee;">Kategori</td>${selectedItems.map(item => `<td style="padding:15px; text-align:center; border-bottom:1px solid #eee;">${item.category}</td>`).join('')}</tr>
                <tr><td style="padding:15px; font-weight:bold; border-bottom:1px solid #eee;">Fiyat</td>${selectedItems.map(item => `<td style="padding:15px; text-align:center; border-bottom:1px solid #eee; font-weight:bold; color:#27ae60;">${item.price} ₺</td>`).join('')}</tr>
            `;
        } else {
            html += `
                <tr style="background:#e67e22; color:white;">
                    <th style="padding:15px; text-align:left;">Özellik</th>
                    ${selectedItems.map(item => `<th style="padding:15px;">${item.title}</th>`).join('')}
                </tr>
                <tr><td style="padding:15px; font-weight:bold; border-bottom:1px solid #eee;">Tarih</td>${selectedItems.map(item => `<td style="padding:15px; text-align:center; border-bottom:1px solid #eee;">${item.date}</td>`).join('')}</tr>
                <tr><td style="padding:15px; font-weight:bold; border-bottom:1px solid #eee;">Kontenjan</td>${selectedItems.map(item => `<td style="padding:15px; text-align:center; border-bottom:1px solid #eee;">${item.capacity} Kişi</td>`).join('')}</tr>
                <tr><td style="padding:15px; font-weight:bold; border-bottom:1px solid #eee;">Ücret</td>${selectedItems.map(item => `<td style="padding:15px; text-align:center; border-bottom:1px solid #eee; font-weight:bold; color:#27ae60;">${item.price} ₺</td>`).join('')}</tr>
            `;
        }
        
        html += '</table>';
        html += `
            <div style="margin-top:20px; text-align:right;">
                <input type="text" id="comp-save-title" placeholder="Karşılaştırma Başlığı" style="padding:10px; border-radius:6px; border:1px solid #ccc; width:250px; margin-right:10px;">
                <button class="btn" style="width:auto; background:#27ae60;" onclick="saveCurrentComparison('${type}', [${ids.map(id => `'${id}'`).join(',')}])">Sonucu Kaydet</button>
            </div>`;
            
        document.getElementById('comparison-result-area').innerHTML = html;
    });
}

function saveCurrentComparison(type, ids) {
    const title = document.getElementById('comp-save-title').value.trim();
    if(!title) return alert("Lütfen bir başlık girin.");
    
    fetch('/api/save_comparison', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({type: type, ids: ids, title: title})
    }).then(res => res.json()).then(data => {
        if(data.success) {
            alert("Karşılaştırma kaydedildi!");
            loadSavedComparisons();
        }
    });
}

function loadSavedComparisons() {
    fetch('/api/get_saved_comparisons').then(res => res.json()).then(data => {
        if(data.success) {
            let html = '';
            data.comparisons.forEach(c => {
                const typeLabel = c.comp_type === 'art' ? '🎨 Eser' : '📅 Etkinlik';
                html += `
                <div style="background:white; padding:15px; border-radius:10px; border:1px solid #eee; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="color:#2c3e50;">${c.title}</strong> <span style="font-size:12px; color:#888; margin-left:10px;">(${typeLabel})</span>
                    </div>
                    <div style="display:flex; gap:10px;">
                        <button class="btn" style="width:auto; padding:5px 15px; font-size:12px; background:#6a89cc;" onclick="renderComparisonTable('${c.item_ids}'.split(','), '${c.comp_type}')">Görüntüle</button>
                        <button class="btn" style="width:auto; padding:5px 15px; font-size:12px; background:#ff4757;" onclick="deleteComparison(${c.id})">Sil</button>
                    </div>
                </div>`;
            });
            const container = document.getElementById('saved-comparisons-list');
            if(container) container.innerHTML = html || '<p style="color:#aaa; text-align:center;">Henüz kayıtlı karşılaştırmanız yok.</p>';
        }
    });
}

function deleteComparison(id) {
    if(!confirm("Bu karşılaştırmayı silmek istediğinize emin misiniz?")) return;
    fetch(`/api/delete_comparison/${id}`, { method: 'POST' }).then(res => res.json()).then(data => {
        if(data.success) loadSavedComparisons();
    });
}
function submitWorkshop() {
    var title = document.getElementById('w-title').value; var date = document.getElementById('w-date').value; var time = document.getElementById('w-time').value; var price = document.getElementById('w-price').value; var capacity = document.getElementById('w-capacity').value; var desc = document.getElementById('w-desc').value; var fileInput = document.getElementById('w-file');
    if (!title || !fileInput.files[0]) return alert("Afiş ve başlık zorunludur.");
    var formData = new FormData(); formData.append('title', title); formData.append('date', date); formData.append('time', time); formData.append('price', price); formData.append('capacity', capacity); formData.append('desc', desc); formData.append('w_image', fileInput.files[0]);
    fetch('/api/add_workshop', { method: 'POST', body: formData }).then(res => res.json()).then(data => { if(data.success) { closeAnyModal('workshop-modal'); loadContent('workshops'); } });
}
function submitEvent() {
    var title = document.getElementById('e-title').value; var date = document.getElementById('e-date').value; var time = document.getElementById('e-time').value; var price = document.getElementById('e-price').value; var capacity = document.getElementById('e-capacity').value; var desc = document.getElementById('e-desc').value; var fileInput = document.getElementById('e-file');
    if (!title || !fileInput.files[0]) return alert("Afiş ve başlık zorunludur.");
    var formData = new FormData(); formData.append('title', title); formData.append('date', date); formData.append('time', time); formData.append('price', price); formData.append('capacity', capacity); formData.append('desc', desc); formData.append('e_image', fileInput.files[0]);
    fetch('/api/add_event', { method: 'POST', body: formData }).then(res => res.json()).then(data => { if(data.success) { closeAnyModal('event-modal'); loadContent('events'); } });
}

function fetchComments() {
    fetch(`/api/get_details/${currentDetailArtId}`).then(res => res.json()).then(data => {
        currentCommentsData = data.comments; currentUserGlobal = data.current_user_id; renderComments();
    });
}
function renderComments() {
    var sortBy = document.getElementById('comment-sort') ? document.getElementById('comment-sort').value : 'newest';
    var sorted = [...currentCommentsData];
    if(sortBy === 'highest') sorted.sort((a,b) => b.rating - a.rating);
    else sorted.sort((a,b) => new Date(b.created_at) - new Date(a.created_at));

    var html = '';
    if(sorted.length === 0) html = '<div style="color:#aaa; text-align:center; padding-top:20px;">İlk yorumu sen yap!</div>';
    
    sorted.forEach(c => {
        var deleteMenu = (c.user_id === currentUserGlobal && !isAdminGlobal) ? `<div class="three-dots-menu" style="margin-left:auto;"><button class="three-dots-btn">⋮</button><div class="three-dots-content"><a href="#" style="color:red;" onclick="deleteComment(${c.id}); return false;">Sil</a></div></div>` : '';
        var rateSelect = (!isAdminGlobal && c.user_id !== currentUserGlobal) ? `<select style="margin-left:10px; padding:1px; font-size:11px;" onchange="rateItem('comment', ${c.id}, this.value)"><option>Puanla</option><option value="5">5 ⭐</option><option value="4">4 ⭐</option><option value="3">3 ⭐</option><option value="2">2 ⭐</option><option value="1">1 ⭐</option></select>` : '';
        var ratingBadge = c.rating > 0 ? `<span style="color:#f1c40f; font-size:12px; margin-left:5px;">⭐ ${c.rating}</span>` : `<span style="color:#ccc; font-size:12px; margin-left:5px;">(Puan Yok)</span>`;
        var ownerReplyHtml = c.reply ? `<div style="margin-top:8px; padding:8px; background:#e8effc; border-left:3px solid #6a89cc; font-size:12px;"><strong>Sanatçı Yanıtı:</strong> ${c.reply}</div>` : '';
        var replyBtnHtml = (isArtOwnerGlobal && !c.reply && !isAdminGlobal) ? `<div style="margin-top:5px; text-align:right;"><button style="background:none; border:none; color:#6a89cc; cursor:pointer; font-size:11px; font-weight:bold;" onclick="showReplyInput('comment', ${c.id})">Yanıtla</button></div>` : '';
        
        html += `
        <div style="display:flex; gap:10px; margin-bottom: 12px; align-items: flex-start; width: 100%;">
            <img src="${c.img}" style="width:30px; height:30px; border-radius:50%; object-fit:cover;">
            <div style="background: #fff; padding: 8px 12px; border-radius: 12px; font-size:13px; border: 1px solid #eee; flex-grow:1;">
                <div style="display:flex; align-items:center;">
                    <strong style="color:#444; font-size:12px;">${c.author}</strong>
                    ${ratingBadge} ${rateSelect}
                    ${deleteMenu}
                </div>
                <div style="margin-top:5px;">${c.text}</div>
                ${ownerReplyHtml} ${replyBtnHtml}
                <div id="reply-box-comment-${c.id}" style="display:none; margin-top:5px; display:flex; gap:5px;"><input type="text" id="reply-input-comment-${c.id}" placeholder="Yanıtınız..." style="flex-grow:1; padding:5px; font-size:11px;"><button onclick="sendReply('comment', ${c.id})" style="padding:5px; font-size:11px; background:#6a89cc; color:white; border:none; border-radius:4px; cursor:pointer;">Gönder</button></div>
            </div>
        </div>`;
    });
    html = html.replace(/display:flex; gap:5px;"/g, 'display:none; gap:5px;"'); 
    var container = document.getElementById('comments-container'); if(container) container.innerHTML = html;
}

function fetchReviews(type, itemId, containerId) {
    fetch(`/api/get_reviews/${type}/${itemId}`).then(res => res.json()).then(data => {
        currentReviewsData = data.reviews; currentUserGlobal = data.current_user_id; renderReviews(containerId);
    });
}
function renderReviews(containerId) {
    if(!containerId) containerId = 'info-reviews-container';
    var sortBy = document.getElementById('review-sort') ? document.getElementById('review-sort').value : 'newest';
    var sorted = [...currentReviewsData];
    if(sortBy === 'highest') sorted.sort((a,b) => b.rating - a.rating);
    else sorted.sort((a,b) => new Date(b.created_at) - new Date(a.created_at));

    var html = '';
    if(sorted.length === 0) html = '<div style="color:#aaa; text-align:center; padding-top:10px;">Henüz değerlendirme yok.</div>';
    
    sorted.forEach(r => {
        var deleteMenu = (r.user_id === currentUserGlobal && !isAdminGlobal) ? `<div class="three-dots-menu" style="margin-left:auto;"><button class="three-dots-btn">⋮</button><div class="three-dots-content"><a href="#" style="color:red;" onclick="deleteReview(${r.id}, '${currentInfoType}', ${currentInfoId}, '${containerId}'); return false;">Sil</a></div></div>` : '';
        var rateSelect = (!isAdminGlobal && r.user_id !== currentUserGlobal) ? `<select style="margin-left:10px; padding:1px; font-size:11px;" onchange="rateItem('review', ${r.id}, this.value)"><option>Puanla</option><option value="5">5 ⭐</option><option value="4">4 ⭐</option><option value="3">3 ⭐</option><option value="2">2 ⭐</option><option value="1">1 ⭐</option></select>` : '';
        var ratingBadge = r.rating > 0 ? `<span style="color:#f1c40f; font-size:12px; margin-left:5px;">⭐ ${r.rating}</span>` : `<span style="color:#ccc; font-size:12px; margin-left:5px;">(Puan Yok)</span>`;
        var ownerReplyHtml = r.reply ? `<div style="margin-top:8px; padding:8px; background:#e8effc; border-left:3px solid #6a89cc; font-size:12px;"><strong>Organizatör Yanıtı:</strong> ${r.reply}</div>` : '';
        var replyBtnHtml = (isInfoOwnerGlobal && !r.reply && !isAdminGlobal) ? `<div style="margin-top:5px; text-align:right;"><button style="background:none; border:none; color:#6a89cc; cursor:pointer; font-size:11px; font-weight:bold;" onclick="showReplyInput('review', ${r.id})">Yanıtla</button></div>` : '';
        
        html += `
        <div style="display:flex; gap:10px; margin-bottom: 12px; align-items: flex-start; width: 100%;">
            <img src="${r.img}" style="width:30px; height:30px; border-radius:50%; object-fit:cover;">
            <div style="background: #fff; padding: 8px 12px; border-radius: 12px; font-size:13px; border: 1px solid #eee; flex-grow:1;">
                <div style="display:flex; align-items:center;">
                    <strong style="color:#444; font-size:12px;">${r.author}</strong>
                    ${ratingBadge} ${rateSelect}
                    ${deleteMenu}
                </div>
                <div style="margin-top:5px;">${r.text}</div>
                ${ownerReplyHtml} ${replyBtnHtml}
                <div id="reply-box-review-${r.id}" style="display:none; margin-top:5px; display:flex; gap:5px;"><input type="text" id="reply-input-review-${r.id}" placeholder="Yanıtınız..." style="flex-grow:1; padding:5px; font-size:11px;"><button onclick="sendReply('review', ${r.id})" style="padding:5px; font-size:11px; background:#6a89cc; color:white; border:none; border-radius:4px; cursor:pointer;">Gönder</button></div>
            </div>
        </div>`;
    });
    html = html.replace(/display:flex; gap:5px;"/g, 'display:none; gap:5px;"'); 
    var container = document.getElementById(containerId); if(container) container.innerHTML = html;
}

function rateItem(type, id, rating) {
    if(rating === "Puanla") return;
    var endpoint = type === 'comment' ? '/api/rate_comment' : '/api/rate_review';
    fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: id, rating: rating }) })
    .then(res => res.json()).then(data => { if(data.success) { if(type === 'comment') fetchComments(); else fetchReviews(currentInfoType, currentInfoId, 'info-reviews-container'); } });
}
function showReplyInput(type, id) { var box = document.getElementById(`reply-box-${type}-${id}`); if(box) box.style.display = 'flex'; }
function sendReply(type, id) {
    var input = document.getElementById(`reply-input-${type}-${id}`); if(!input || input.value.trim() === '') return;
    var endpoint = type === 'comment' ? '/api/reply_comment' : '/api/reply_review';
    fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: id, reply: input.value }) })
    .then(res => res.json()).then(data => { if(data.success) { if(type === 'comment') fetchComments(); else fetchReviews(currentInfoType, currentInfoId, 'info-reviews-container'); } });
}

function openSummaryReport() {
    var box = document.getElementById('summary-box');
    if(!box) return;
    if(box.style.display === 'block') { box.style.display = 'none'; return; }
    
    fetch(`/api/get_summary/${currentInfoType}/${currentInfoId}`)
    .then(res => res.json()).then(data => {
        if(data.success) {
            document.getElementById('sum-tickets').textContent = data.total_paid_tickets + " / " + data.capacity;
            document.getElementById('sum-revenue').textContent = data.total_revenue + " ₺";
            document.getElementById('sum-rating').textContent = "⭐ " + data.avg_rating + " (" + data.total_reviews + ")";
            box.style.display = 'block';
        }
    });
}

function openDetailModal(id, title, desc, price, img_path, author_name, author_img, like_count, isOwner, isSold) {
    currentDetailArtId = id; currentDetailArtPrice = price; isArtOwnerGlobal = isOwner;
    document.getElementById('detail-img').src = img_path; document.getElementById('detail-title').textContent = title; document.getElementById('detail-desc').textContent = desc; document.getElementById('detail-price').textContent = price + " ₺"; document.getElementById('detail-author-name').textContent = author_name; document.getElementById('detail-author-img').src = author_img; document.getElementById('modal-like-count').textContent = like_count;
    var ownerMenu = document.getElementById('art-owner-menu'); if(ownerMenu) ownerMenu.style.display = isOwner ? 'inline-block' : 'none';
    
    var buyBtn = document.getElementById('buy-btn'); var soldBadge = document.getElementById('sold-badge');
    var likeBtn = document.getElementById('like-btn'); var favBtn = document.getElementById('favorite-btn');
    var commentInputArea = document.querySelector('.interaction-bar div:last-child'); 

    if (isAdminGlobal) {
        if(buyBtn) buyBtn.style.display = 'none';
        if(likeBtn) likeBtn.style.display = 'none';
        if(favBtn) favBtn.style.display = 'none';
        if(commentInputArea) commentInputArea.style.display = 'none';
        if(soldBadge) soldBadge.style.display = isSold ? 'inline-block' : 'none';
    } else {
        if (isSold) { buyBtn.style.display = 'none'; soldBadge.style.display = 'inline-block'; } 
        else { soldBadge.style.display = 'none'; buyBtn.style.display = isOwner ? 'none' : 'inline-block'; }
        if(likeBtn) likeBtn.style.display = 'inline-block';
        if(favBtn) favBtn.style.display = 'inline-block';
        if(commentInputArea) commentInputArea.style.display = 'flex';
    }

    document.getElementById('new-comment').value = ''; document.getElementById('comments-container').innerHTML = 'Yükleniyor...';
    fetch(`/api/get_details/${id}`).then(res => res.json()).then(data => {
        if (!isAdminGlobal) {
            if (data.user_liked) likeBtn.innerHTML = `❤️ Beğendin (<span id="modal-like-count">${like_count}</span>)`; else likeBtn.innerHTML = `🤍 Beğen (<span id="modal-like-count">${like_count}</span>)`;
            if (data.user_favorited) favBtn.innerHTML = `📌 Favorilerden Çıkar`; else favBtn.innerHTML = `📌 Favoriye Ekle`;
        }
        currentCommentsData = data.comments; currentUserGlobal = data.current_user_id; renderComments();
    });
    openAnyModal('art-detail-modal'); isModalOpen = true; 
}
function closeDetailModal() { closeAnyModal('art-detail-modal'); isModalOpen = false; }
function toggleLike() {
    if(!currentDetailArtId) return;
    fetch('/api/like_art', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ art_id: currentDetailArtId }) })
    .then(res => res.json()).then(data => {
        if(data.success) {
            var likeBtn = document.getElementById('like-btn'); if (data.liked) likeBtn.innerHTML = `❤️ Beğendin (<span id="modal-like-count">${data.new_count}</span>)`; else likeBtn.innerHTML = `🤍 Beğen (<span id="modal-like-count">${data.new_count}</span>)`;
            var floatingBadge = document.getElementById('badge-like-' + currentDetailArtId); 
            if(floatingBadge) floatingBadge.innerHTML = floatingBadge.innerHTML.replace(/❤️ \d+/, '❤️ ' + data.new_count);
        }
    });
}
function toggleFavorite() {
    if(!currentDetailArtId) return;
    fetch('/api/toggle_favorite', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ art_id: currentDetailArtId }) }).then(res => res.json()).then(data => {
        if(data.success) { var favBtn = document.getElementById('favorite-btn'); if (data.favorited) favBtn.innerHTML = `📌 Favorilerden Çıkar`; else favBtn.innerHTML = `📌 Favoriye Ekle`; }
    });
}
function postComment() {
    var text = document.getElementById('new-comment').value; if(text.trim() === '') return;
    fetch('/api/add_comment', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ art_id: currentDetailArtId, comment: text }) }).then(res => res.json()).then(data => { if(data.success) { document.getElementById('new-comment').value = ''; fetchComments(); }});
}
function deleteComment(commentId) { fetch('/api/delete_comment/' + commentId, { method: 'POST' }).then(res => res.json()).then(data => { if(data.success) fetchComments(); }); }
function deleteCurrentArt() { if(confirm('Eser silinecek. Emin misiniz?')) { fetch('/api/delete_art/' + currentDetailArtId, { method: 'POST' }).then(res => res.json()).then(data => { if(data.success) { closeDetailModal(); loadContent('gallery'); } }); } }

function openInfoModal(id, type, title, desc, date, time, price, capacity, img, author, authorImg, isOwner, reservedTickets, isPast) {
    currentInfoId = id; currentInfoType = type; isInfoOwnerGlobal = isOwner;
    document.getElementById('info-img').src = img; document.getElementById('info-title').textContent = title; document.getElementById('info-desc').textContent = desc; document.getElementById('info-datetime').innerHTML = date + "<br>" + time; document.getElementById('info-price').textContent = price + " ₺"; document.getElementById('info-author-name').textContent = author; document.getElementById('info-author-img').src = authorImg; document.getElementById('info-role').textContent = (type === 'workshop' ? 'Eğitmen' : 'Organizatör');
    var ownerMenu = document.getElementById('info-owner-menu'); if(ownerMenu) ownerMenu.style.display = isOwner ? 'inline-block' : 'none';
    let remaining = capacity - (reservedTickets || 0); document.getElementById('info-capacity').textContent = remaining + " Kişi (Kalan)";
    
    var sumBox = document.getElementById('summary-box'); if(sumBox) sumBox.style.display = 'none';

    let reserveBox = document.getElementById('reservation-box');
    if(reserveBox) {
        if (isAdminGlobal) reserveBox.innerHTML = '<p style="color:#666;">Yöneticiler rezervasyon yapamazlar.</p>';
        else if (isPast) reserveBox.innerHTML = '<p style="color:#e74c3c; font-weight:bold; font-size:16px;">⏳ Bu etkinlik sona ermiştir.</p>';
        else if (isOwner) reserveBox.innerHTML = '<p style="color:#666;">Kendi etkinliğinize rezervasyon yapamazsınız.</p>';
        else if (remaining <= 0) reserveBox.innerHTML = '<p style="color:red; font-weight:bold;">❌ Kontenjan Doldu</p>';
        else reserveBox.innerHTML = `<div style="display:flex; justify-content:center; gap:10px; align-items:center;"><label style="font-weight:bold; color:#555;">Kişi Sayısı:</label><input type="number" id="reserve-count" min="1" max="${remaining}" value="1" style="width:60px; padding:8px; border-radius:6px; border:1px solid #ccc;"><button class="btn" style="width:auto; padding:8px 20px; background:#27ae60;" onclick="reserveTickets()">Rezervasyon Yap</button></div>`;
    }
    fetchReviews(type, id, 'info-reviews-container'); openAnyModal('info-detail-modal');
}
function reserveTickets() {
    var count = document.getElementById('reserve-count').value;
    fetch('/api/reserve', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: currentInfoId, type: currentInfoType, tickets: count }) }).then(res => res.json()).then(data => { alert(data.message); if(data.success) { closeAnyModal('info-detail-modal'); loadContent('reservations'); }});
}
function deleteCurrentInfo() {
    if(confirm('Silmek istediğinize emin misiniz?')) {
        var route = (currentInfoType === 'workshop') ? '/api/delete_workshop/' : '/api/delete_event/';
        fetch(route + currentInfoId, { method: 'POST' }).then(res => res.json()).then(data => { if(data.success) { closeAnyModal('info-detail-modal'); loadContent(currentInfoType === 'workshop' ? 'workshops' : 'events'); }});
    }
}

function openReservationModal(resId, title, date, time, price, tickets, img, author, type, itemId, maxAllowed, payStatus, isPast) {
    currentResId = resId; currentResTotalPrice = price * tickets; currentResItemId = itemId; currentResItemType = type;
    document.getElementById('res-img').src = img; document.getElementById('res-title').textContent = title; document.getElementById('res-author').textContent = (type === 'workshop' ? 'Eğitmen: ' : 'Organizatör: ') + author; document.getElementById('res-datetime').innerHTML = date + "<br>" + time; document.getElementById('res-price').textContent = price + " ₺ (Toplam: " + currentResTotalPrice + " ₺)";
    var input = document.getElementById('res-tickets-input'); if(input) { input.max = maxAllowed; input.value = tickets; }
    var payArea = document.getElementById('res-payment-area'); var mngArea = document.getElementById('res-management-area'); var revArea = document.getElementById('res-review-area'); 
    if (isPast) {
        payArea.style.display = 'none'; mngArea.style.display = 'none'; revArea.style.display = 'block'; document.getElementById('new-review').value = ''; fetchReviews(type, itemId, 'reviews-container');
    } else {
        revArea.style.display = 'none';
        if (payStatus === 'Ödendi') { payArea.style.display = 'none'; mngArea.style.display = 'none'; } else { payArea.style.display = 'block'; mngArea.style.display = 'flex'; }
    }
    openAnyModal('reservation-detail-modal');
}
function updateReservation() {
    var tickets = document.getElementById('res-tickets-input').value;
    fetch('/api/update_reservation', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({res_id: currentResId, tickets: tickets}) }).then(res => res.json()).then(data => { alert(data.message); if(data.success) { closeAnyModal('reservation-detail-modal'); loadContent('reservations'); }});
}
function cancelReservation() { if(confirm("Rezervasyonunuzu iptal etmek istediğinize emin misiniz?")) { fetch('/api/cancel_reservation/' + currentResId, { method: 'POST' }).then(res => res.json()).then(data => { if(data.success) { closeAnyModal('reservation-detail-modal'); loadContent('reservations'); }}); } }

function postReview() {
    var text = document.getElementById('new-review').value; 
    var rating = document.getElementById('new-review-rating').value;
    if(text.trim() === '') return;
    fetch('/api/add_review', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item_type: currentResItemType, item_id: currentResItemId, review: text, event_rating: rating }) }).then(res => res.json()).then(data => { if(data.success) { document.getElementById('new-review').value = ''; fetchReviews(currentResItemType, currentResItemId, 'reviews-container'); }});
}
function deleteReview(revId, type, itemId, containerId) { fetch('/api/delete_review/' + revId, { method: 'POST' }).then(res => res.json()).then(data => { if(data.success) fetchReviews(type, itemId, containerId); }); }

function applyCoupon() {
    let codeInput = document.getElementById('coupon-code');
    let msg = document.getElementById('coupon-message');
    let code = codeInput.value.trim().toUpperCase();
    
    if(!code) return;
    
    fetch('/api/apply_coupon', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code: code})
    }).then(res => res.json()).then(data => {
        msg.textContent = data.message;
        msg.style.display = 'block';
        msg.style.color = data.success ? '#27ae60' : '#e74c3c';
        
        if(data.success) {
            appliedCouponCode = code;
            let amtEl = document.getElementById('payment-amount');
            let baseAmount = parseFloat(amtEl.dataset.baseAmount);
            let discounted = baseAmount * (1 - data.discount_rate);
            
            amtEl.innerHTML = `<span style="text-decoration: line-through; color:#aaa; font-size:18px; margin-right:8px;">${baseAmount.toFixed(2)} ₺</span><span style="color:#27ae60;">${discounted.toFixed(2)} ₺</span><div style="font-size:14px; color:#e67e22; margin-top:5px;">(Kupon Uygulandı)</div>`;
            codeInput.disabled = true;
        }
    });
}

function openPaymentModal(type, id, amount) {
    currentPayType = type; currentPayId = id; appliedCouponCode = null;
    let amtEl = document.getElementById('payment-amount');
    amtEl.dataset.baseAmount = amount;
    amtEl.innerHTML = amount + " ₺";
    
    let codeInput = document.getElementById('coupon-code');
    if(codeInput) {
        codeInput.value = '';
        codeInput.disabled = false;
    }
    let msg = document.getElementById('coupon-message');
    if(msg) msg.style.display = 'none';

    if(type === 'art') closeAnyModal('art-detail-modal'); if(type === 'reservation') closeAnyModal('reservation-detail-modal');
    openAnyModal('payment-modal');
}
function confirmPayment() {
    fetch('/api/process_payment', { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ type: currentPayType, id: currentPayId, coupon_code: appliedCouponCode }) 
    }).then(res => res.json()).then(data => {
        alert(data.message); if(data.success) { closeAnyModal('payment-modal'); if(currentPayType === 'art') loadContent('purchases'); if(currentPayType === 'reservation') loadContent('reservations'); }
    });
}

function animateGallery() {
    if (!isGalleryActive) return;
    var canvas = document.getElementById('gallery-canvas'); var viewport = document.querySelector('.gallery-viewport');
    if (!canvas || !viewport) return;
    var maxPan = Math.max(0, canvas.scrollWidth - viewport.clientWidth);
    if (!isModalOpen) panTarget += autoPanSpeed;
    if (panTarget >= maxPan && autoPanSpeed > 0) autoPanSpeed = -1.0;
    if (panTarget <= 0 && autoPanSpeed < 0) autoPanSpeed = 1.0;
    currentPan += (panTarget - currentPan) * 0.05; canvas.style.transform = `translateX(-${currentPan}px)`;
    galleryAnimationId = requestAnimationFrame(animateGallery);
}
function panGallery(direction) { panTarget += direction * 500; }

function submitTicket(e) {
    e.preventDefault();
    var subject = document.getElementById('ticket-subject').value;
    var message = document.getElementById('ticket-message').value;
    if(!subject || !message) return;
    fetch('/api/create_ticket', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({subject: subject, message: message}) }).then(res => res.json()).then(data => {
        alert(data.message);
        if(data.success) { loadContent('support'); }
    });
}

// --- CANLI DESTEK FONKSİYONLARI ---
let liveChatInterval;
let globalNotificationInterval;
let activeChatUserId = null;
let lastSeenAdminMsgCount = parseInt(localStorage.getItem('lastSeenAdminMsgCount')) || 0;
let lastSeenTicketReplyCount = parseInt(localStorage.getItem('lastSeenTicketReplyCount')) || 0;
let currentPageNameGlobal = 'gallery';

function toggleLiveChat() {
    let body = document.getElementById('live-chat-body');
    let container = document.getElementById('live-chat-container');
    let header = document.getElementById('live-chat-header');
    
    if(body.style.display === 'none') {
        body.style.display = 'flex';
        container.style.height = '400px';
        startChatPolling();
        
        // Chat bildirimini temizle (noktayı kaldır)
        let dot = header.querySelector('.notification-dot');
        if(dot) dot.style.display = 'none';
        
        // Chat sayacını güncelle
        fetch('/api/check_notifications').then(res => res.json()).then(data => {
            if(data.success) {
                lastSeenAdminMsgCount = data.chat_count;
                localStorage.setItem('lastSeenAdminMsgCount', lastSeenAdminMsgCount);
            }
        });
    } else {
        body.style.display = 'none';
        container.style.height = 'auto';
        stopChatPolling();
    }
}

function startChatPolling() {
    fetchChat();
    if(liveChatInterval) clearInterval(liveChatInterval);
    liveChatInterval = setInterval(fetchChat, 3000);
}

function stopChatPolling() {
    clearInterval(liveChatInterval);
}

function fetchChat() {
    fetch('/api/get_chat').then(res => res.json()).then(data => {
        if(data.success) {
            renderChatMessages('live-chat-messages', data.messages);
        }
    });
}

function startGlobalNotificationCheck() {
    if(globalNotificationInterval) clearInterval(globalNotificationInterval);
    checkNotifications(); // İlk seferinde anında çalıştır
    globalNotificationInterval = setInterval(checkNotifications, 5000);
}

function checkNotifications() {
    if(isAdminGlobal) return;
    
    fetch('/api/check_notifications').then(res => res.json()).then(data => {
        if(data.success) {
            let hasNewChat = data.chat_count > lastSeenAdminMsgCount;
            let hasNewTicket = data.ticket_count > lastSeenTicketReplyCount;
            
            if(hasNewChat || hasNewTicket) {
                // Yeni bir şeyler var!
                if(currentPageNameGlobal !== 'support') {
                    // Sidebar linkine nokta koy
                    let link = document.getElementById('sidebar-support-link');
                    if(link) {
                        let dot = link.querySelector('.notification-dot');
                        if(!dot) link.innerHTML += ' <span class="notification-dot"></span>';
                        else dot.style.display = 'inline-block';
                    }
                } else {
                    // Sayfa support'taysa
                    
                    // 1. Eğer yeni bir TALEP yanıtı varsa, sidebar'daki noktayı temizle (çünkü zaten sayfadayız)
                    // (loadContent zaten bunu yapıyor ama burada da garantiye alabiliriz)
                    
                    // 2. Eğer yeni bir CHAT mesajı varsa ve chat kapalıysa chat butonuna nokta koy
                    if(hasNewChat) {
                        let body = document.getElementById('live-chat-body');
                        if(body && body.style.display === 'none') {
                            let header = document.getElementById('live-chat-header');
                            if(header) {
                                let dot = header.querySelector('.notification-dot');
                                if(!dot) header.innerHTML += ' <span class="notification-dot"></span>';
                                else dot.style.display = 'inline-block';
                            }
                        }
                    }
                }
            }
        }
    });
}

function renderChatMessages(containerId, messages) {
    let container = document.getElementById(containerId);
    if(!container) return;
    let html = '';
    messages.forEach(m => {
        let cls = m.is_from_admin ? 'admin' : 'user';
        if(containerId === 'admin-chat-messages') {
            cls = m.is_from_admin ? 'user' : 'admin';
        }
        html += `<div class="chat-msg ${cls}">${m.message}</div>`;
    });
    container.innerHTML = html || (containerId === 'live-chat-messages' ? '<p style="font-size: 12px; color: #888; text-align: center;">Size nasıl yardımcı olabiliriz?</p>' : '');
    container.scrollTop = container.scrollHeight;
}

function sendLiveChatMessage() {
    let input = document.getElementById('live-chat-input');
    let msg = input.value.trim();
    if(!msg) return;
    fetch('/api/send_chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: msg})
    }).then(res => res.json()).then(data => {
        if(data.success) {
            input.value = '';
            fetchChat();
        }
    });
}

function loadAdminChatUsers() {
    fetch('/api/get_chat_users').then(res => res.json()).then(data => {
        if(data.success) {
            let container = document.getElementById('admin-chat-users');
            if(!container) return;
            let html = '';
            data.users.forEach(u => {
                let activeCls = (u.id === activeChatUserId) ? 'active' : '';
                html += `
                <div class="chat-user-item ${activeCls}" onclick="selectChatUser(${u.id}, this)" style="display:flex; gap:10px; align-items:center; padding:10px; border-radius:8px; cursor:pointer; margin-bottom:5px;">
                    <img src="${u.img}" style="width:35px; height:35px; border-radius:50%; object-fit:cover;">
                    <span style="font-size:14px; font-weight:bold;">${u.name}</span>
                </div>`;
            });
            container.innerHTML = html || '<p style="text-align:center; color:#888; font-size:12px;">Henüz mesaj yok</p>';
        }
    });
}

function selectChatUser(userId, el) {
    activeChatUserId = userId;
    document.querySelectorAll('.chat-user-item').forEach(item => item.classList.remove('active'));
    el.classList.add('active');
    
    document.getElementById('admin-chat-input-area').style.display = 'flex';
    document.getElementById('admin-chat-messages').innerHTML = '<p style="text-align:center; color:#888;">Yükleniyor...</p>';
    fetchAdminChat();
    if(window.adminChatInterval) clearInterval(window.adminChatInterval);
    window.adminChatInterval = setInterval(fetchAdminChat, 3000);
}

function fetchAdminChat() {
    if(!activeChatUserId) return;
    fetch('/api/get_chat/' + activeChatUserId).then(res => res.json()).then(data => {
        if(data.success) {
            renderChatMessages('admin-chat-messages', data.messages);
        }
    });
}

function sendAdminChatMessage() {
    let input = document.getElementById('admin-chat-input');
    let msg = input.value.trim();
    if(!msg || !activeChatUserId) return;
    fetch('/api/send_chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user_id: activeChatUserId, message: msg})
    }).then(res => res.json()).then(data => {
        if(data.success) {
            input.value = '';
            fetchAdminChat();
        }
    });
}

function replyTicket(ticketId) {
    var replyText = document.getElementById('admin-reply-' + ticketId).value;
    if(!replyText.trim()) return alert("Yanıt boş olamaz.");
    fetch('/api/reply_ticket', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ticket_id: ticketId, reply: replyText}) }).then(res => res.json()).then(data => {
        if(data.success) { loadContent('admin_panel'); }
    });
}

function submitAdminCoupon() {
    const select = document.getElementById('admin-coupon-users');
    const selectedIds = Array.from(select.selectedOptions).map(opt => opt.value);
    const code = document.getElementById('admin-coupon-name').value.trim();
    const rate = document.getElementById('admin-coupon-rate').value;
    const msg = document.getElementById('admin-coupon-message');
    
    if (selectedIds.length === 0) return alert("En az bir kullanıcı seçmelisiniz.");
    if (!code) return alert("Kupon kodu girmelisiniz.");
    
    fetch('/api/admin/create_coupon', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user_ids: selectedIds, code: code, rate: rate})
    }).then(res => res.json()).then(data => {
        msg.textContent = data.message;
        msg.style.color = data.success ? '#27ae60' : '#e74c3c';
        if(data.success) {
            document.getElementById('admin-coupon-name').value = '';
            select.selectedIndex = -1; // Seçimleri temizle
        }
    });
}
