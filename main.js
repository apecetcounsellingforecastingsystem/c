/**
 * AP ECET Counselling Forecasting System — Frontend JavaScript
 * Handles theme toggling, interactive Chart.js charts, simulated OTP verification,
 * preference list reordering, bookmarking, and dynamic What-If simulations.
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initPasswordToggles();
  initAlertDismissal();
  initAuthModal();
  initFaqAccordion();
  initHomeInteractions();
  initSidebarDrawer();
});

// 1. Theme Management (Dark / Light Mode)
function initTheme() {
  const savedTheme = localStorage.getItem('apecet_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  const toggleBtn = document.getElementById('themeToggleBtn');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('apecet_theme', next);
      updateThemeIcon(next);
      
      // Notify any active charts to re-render colors
      if (window.activeCharts) {
        window.activeCharts.forEach(c => c.update());
      }
    });
  }
}

function updateThemeIcon(theme) {
  const icon = document.getElementById('themeToggleIcon');
  if (icon) {
    icon.innerHTML = theme === 'dark' ? '☀️' : '🌙';
  }
}

// 2. Modern SVG Password Visibility Toggle (No Emojis)
const SVG_EYE_OPEN = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
const SVG_EYE_SLASH = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;

function initPasswordToggles() {
  document.querySelectorAll('.password-toggle-btn').forEach(btn => {
    btn.innerHTML = SVG_EYE_SLASH;
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        if (input.type === 'password') {
          input.type = 'text';
          btn.innerHTML = SVG_EYE_OPEN;
          btn.setAttribute('title', 'Hide password');
        } else {
          input.type = 'password';
          btn.innerHTML = SVG_EYE_SLASH;
          btn.setAttribute('title', 'Show password');
        }
      }
    });
  });
}

// 2b. Left Navigation Drawer for Students (Three Straight Lines / Hamburger)
function initSidebarDrawer() {
  const drawer = document.getElementById('studentSidebarDrawer');
  const backdrop = document.getElementById('drawerOverlay');
  const toggleBtns = document.querySelectorAll('.drawer-toggle-btn');
  const closeBtn = document.getElementById('closeDrawerBtn');

  function openDrawer() {
    if (drawer) drawer.classList.add('open');
    if (backdrop) backdrop.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeDrawer() {
    if (drawer) drawer.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
    document.body.style.overflow = '';
  }

  toggleBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      openDrawer();
    });
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', closeDrawer);
  }

  if (backdrop) {
    backdrop.addEventListener('click', closeDrawer);
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && drawer && drawer.classList.contains('open')) {
      closeDrawer();
    }
  });
}

// 3. Alert Auto-Dismissal
function initAlertDismissal() {
  setTimeout(() => {
    document.querySelectorAll('.auto-dismiss').forEach(el => {
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    });
  }, 5000);
}

// 4. Simulated OTP Verification (Email & Phone)
function sendOtp(type) {
  const inputId = type === 'email' ? 'regEmail' : 'regPhone';
  const val = document.getElementById(inputId)?.value.trim();
  const statusEl = document.getElementById(`${type}OtpStatus`);

  if (!val) {
    alert(`Please enter a valid ${type} first.`);
    return;
  }

  // Generate 6 digit OTP
  const mockOtp = Math.floor(100000 + Math.random() * 900000).toString();
  sessionStorage.setItem(`mock_otp_${type}`, mockOtp);

  if (statusEl) {
    statusEl.innerHTML = `<span style="color: var(--accent-cyan); font-weight:600;">OTP Sent! (Simulated Code: <b>${mockOtp}</b>)</span>`;
  }
  
  // Prompt user or display input
  const otpInput = prompt(`[SIMULATED SMS/EMAIL GATEWAY]\nYour AP ECET 6-digit verification code is: ${mockOtp}\n\nPlease enter the code to verify:`, mockOtp);
  if (otpInput === mockOtp) {
    sessionStorage.setItem(`verified_${type}`, 'true');
    const badge = document.getElementById(`${type}VerifiedBadge`);
    if (badge) {
      badge.style.display = 'inline-flex';
    }
    const sendBtn = document.getElementById(`btnSend${type.charAt(0).toUpperCase() + type.slice(1)}Otp`);
    if (sendBtn) {
      sendBtn.disabled = true;
      sendBtn.innerText = 'Verified ✓';
      sendBtn.className = 'btn-secondary-glass';
      sendBtn.style.color = 'var(--color-safe)';
    }
    if (statusEl) {
      statusEl.innerHTML = `<span style="color: var(--color-safe); font-weight:600;">✓ ${type.toUpperCase()} Verified Successfully</span>`;
    }
  } else if (otpInput !== null) {
    alert('Incorrect verification code. Please try again.');
  }
}

// 5. Bookmark / Save College
async function toggleSaveCollege(collegeCode, branchName, btn) {
  try {
    const res = await fetch('/api/save-college', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ college_code: collegeCode, branch_name: branchName })
    });
    const data = await res.json();
    if (data.success) {
      if (data.action === 'saved') {
        btn.innerHTML = '❤️ Saved';
        btn.style.color = '#ef4444';
      } else {
        btn.innerHTML = '🤍 Save';
        btn.style.color = 'inherit';
      }
    }
  } catch (err) {
    console.error('Save college error:', err);
  }
}

// 6. Add to Preference List
async function addToPreferences(collegeCode, collegeName, branchName, district, classification, probability, closingRank, fees) {
  try {
    const res = await fetch('/api/preference-list/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        college_code: collegeCode,
        college_name: collegeName,
        branch_name: branchName,
        district: district,
        classification: classification,
        probability: probability,
        closing_rank: closingRank,
        fees: fees
      })
    });
    const data = await res.json();
    if (data.success) {
      alert(`✓ ${collegeCode} (${branchName}) added to your Preference List as Choice #${data.order}`);
    } else {
      alert(data.message || 'Could not add to preference list.');
    }
  } catch (err) {
    console.error('Add to preferences error:', err);
  }
}

// 7. Reorder Preference List
function movePreference(order, direction) {
  const currentItem = document.querySelector(`.preference-item[data-order="${order}"]`);
  if (!currentItem) return;

  if (direction === 'up') {
    const prev = currentItem.previousElementSibling;
    if (prev && prev.classList.contains('preference-item')) {
      currentItem.parentNode.insertBefore(currentItem, prev);
      reindexPreferences();
    }
  } else if (direction === 'down') {
    const next = currentItem.nextElementSibling;
    if (next && next.classList.contains('preference-item')) {
      currentItem.parentNode.insertBefore(next, currentItem);
      reindexPreferences();
    }
  }
}

async function removePreference(order, id) {
  if (!confirm('Remove this choice from your preference list?')) return;
  try {
    const res = await fetch(`/api/preference-list/delete/${id}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      const el = document.querySelector(`.preference-item[data-order="${order}"]`);
      if (el) el.remove();
      reindexPreferences();
    }
  } catch (err) {
    console.error('Delete preference error:', err);
  }
}

function reindexPreferences() {
  const items = document.querySelectorAll('.preference-item');
  const payload = [];
  items.forEach((el, index) => {
    const newOrder = index + 1;
    el.setAttribute('data-order', newOrder);
    const badge = el.querySelector('.preference-order-badge');
    if (badge) badge.innerText = newOrder < 10 ? `0${newOrder}` : newOrder;
    payload.push({ id: el.getAttribute('data-id'), order: newOrder });
  });

  // Save new order to backend
  fetch('/api/preference-list/reorder', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items: payload })
  });
}

// 8. Interactive Chart.js Rendering Helpers
window.renderCutoffTrendChart = function(canvasId, years, cutoffs, forecasts) {
  const ctx = document.getElementById(canvasId)?.getContext('2d');
  if (!ctx) return;

  const labels = ['2023', '2024', '2025', '2026'];
  const historicalData = [cutoffs['2023'] || null, cutoffs['2024'] || null, null, null];
  const forecastedData = [null, cutoffs['2024'] || null, forecasts['2025'] || null, forecasts['2026'] || null];

  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Original Historical Closing Rank',
          data: historicalData,
          borderColor: '#10b981', // Green as required
          backgroundColor: 'rgba(16, 185, 129, 0.2)',
          borderWidth: 3,
          pointBackgroundColor: '#10b981',
          pointRadius: 6,
          tension: 0.2,
          fill: false
        },
        {
          label: 'Expected / Forecasted Closing Rank',
          data: forecastedData,
          borderColor: '#f59e0b', // Orange as required
          backgroundColor: 'rgba(245, 158, 11, 0.2)',
          borderWidth: 3,
          borderDash: [6, 4],
          pointBackgroundColor: '#f59e0b',
          pointRadius: 6,
          tension: 0.2,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', weight: 600 } }
        },
        tooltip: {
          backgroundColor: '#0f172a',
          borderColor: '#38bdf8',
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.06)' },
          ticks: { color: '#94a3b8' }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.06)' },
          ticks: { color: '#94a3b8' },
          title: { display: true, text: 'Closing Rank (Lower = More Competitive)', color: '#94a3b8' }
        }
      }
    }
  });

  window.activeCharts = window.activeCharts || [];
  window.activeCharts.push(chart);
};

// 9. Auth Requirement Modal Logic (For Gated Navigation & Buttons)
function isUserAuthenticated() {
  return document.body.getAttribute('data-user-authenticated') === 'true';
}

function openAuthModal(featureName) {
  const modal = document.getElementById('authRequiredModal');
  if (!modal) return;
  const title = document.getElementById('authModalTitle');
  const desc = document.getElementById('authModalDesc');
  if (featureName && desc) {
    desc.innerHTML = `Please sign in or register your candidate account to access <b>${featureName}</b>, historical cutoffs, and personalized seat predictions.`;
  }
  modal.style.display = 'flex';
}

function closeAuthModal() {
  const modal = document.getElementById('authRequiredModal');
  if (modal) modal.style.display = 'none';
}

function initAuthModal() {
  // Listen to all gated nav links and buttons
  document.querySelectorAll('.auth-required-nav, .auth-required-btn').forEach(el => {
    el.addEventListener('click', (e) => {
      if (!isUserAuthenticated()) {
        e.preventDefault();
        const feature = el.getAttribute('data-feature') || el.innerText.trim();
        openAuthModal(feature);
      }
    });
  });

  // Close button
  const closeBtn = document.getElementById('closeAuthModalBtn');
  if (closeBtn) {
    closeBtn.addEventListener('click', closeAuthModal);
  }

  // Close when clicking outside card
  const modal = document.getElementById('authRequiredModal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeAuthModal();
      }
    });
  }

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeAuthModal();
    }
  });
}

// 10. FAQ Accordion Logic
function initFaqAccordion() {
  document.querySelectorAll('.faq-question').forEach(header => {
    header.addEventListener('click', () => {
      const parent = header.closest('.faq-box');
      if (parent) {
        parent.classList.toggle('active');
      }
    });
  });
}

// 11. Home Page Interactive Estimator & Contact Form Simulation
function initHomeInteractions() {
  // Contact Form submit simulation
  const contactForm = document.getElementById('homeContactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const statusEl = document.getElementById('contactStatusMsg');
      if (statusEl) {
        statusEl.innerHTML = `<div class="alert-glass alert-normal" style="margin-top: 1rem;"><span>✅</span><span>Thank you! Your inquiry has been logged. An AP ECET counselling advisor will respond within 24 hours.</span></div>`;
        contactForm.reset();
      }
    });
  }

  // Quick Rank Estimator
  const estimatorBtn = document.getElementById('btnQuickEstimate');
  if (estimatorBtn) {
    estimatorBtn.addEventListener('click', () => {
      const rankVal = parseInt(document.getElementById('quickRankInput')?.value);
      const branchVal = document.getElementById('quickBranchSelect')?.value;
      const resultBox = document.getElementById('quickEstimateResult');
      
      if (!rankVal || isNaN(rankVal) || rankVal <= 0) {
        alert('Please enter a valid rank (e.g. 150, 850, 2400).');
        return;
      }

      let odds = '88% (SAFE)';
      let colName = 'JNTUK Univ. College of Engg., Kakinada';
      let tagClass = 'badge-safe';
      
      if (rankVal < 500) {
        odds = '92% (SAFE)';
        colName = 'Andhra University College of Engineering (AUCE), Visakhapatnam';
        tagClass = 'badge-safe';
      } else if (rankVal < 1500) {
        odds = '78% (MODERATE)';
        colName = 'JNTUA College of Engineering, Anantapur';
        tagClass = 'badge-moderate';
      } else if (rankVal < 3500) {
        odds = '62% (AMBITIOUS)';
        colName = 'VR Siddhartha Engineering College, Vijayawada';
        tagClass = 'badge-ambitious';
      } else {
        odds = '45% (DREAM)';
        colName = 'GMR Institute of Technology, Rajam';
        tagClass = 'badge-dream';
      }

      if (resultBox) {
        resultBox.style.display = 'block';
        resultBox.innerHTML = `
          <div style="background: rgba(14, 165, 233, 0.08); border: 1px solid rgba(14, 165, 233, 0.3); border-radius: var(--radius-md); padding: 1.25rem; margin-top: 1.25rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
              <span style="font-size: 0.85rem; color: var(--text-secondary);">Simulated Match Preview:</span>
              <span class="${tagClass}">${odds}</span>
            </div>
            <div style="font-weight: 700; font-size: 1.05rem; color: var(--text-primary); margin-bottom: 0.25rem;">${colName}</div>
            <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">Branch: ${branchVal || 'Computer Science & Engineering'}</div>
            <a href="#" class="btn-primary-glass auth-required-btn" data-feature="Full 25+ Autonomous College Forecast" style="width: 100%; padding: 0.65rem; font-size: 0.88rem;">
              <span>⚡</span> Unlock All 25+ Forecasted Colleges (Login / Register)
            </a>
          </div>
        `;
        // rebind auth modal for new button
        const newBtn = resultBox.querySelector('.auth-required-btn');
        if (newBtn && !isUserAuthenticated()) {
          newBtn.addEventListener('click', (e) => {
            e.preventDefault();
            openAuthModal('Full 25+ College Forecast');
          });
        }
      }
    });
  }
}
