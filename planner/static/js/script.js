/**
 * script.js — AI Study Planner Frontend Logic
 * =============================================
 * Handles:
 *   1. Form validation
 *   2. Slider UI updates
 *   3. Alert auto-dismiss
 *   4. Page animations
 *   5. Print/download plan as PDF
 *   7. Smooth transitions
 */

// -------------------------------------------------------
// DOM Ready
// -------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initSliders();
  initMoodSelector();
  initFormValidation();
  initAlerts();
  initAnimations();
  initCharts();
  initPrintButton();
});

// -------------------------------------------------------
// 1. SLIDER UI — Updates displayed value in real-time
// -------------------------------------------------------
function initSliders() {
  const sliders = document.querySelectorAll('input[type="range"]');

  sliders.forEach(slider => {
    const valueDisplay = document.getElementById(slider.id + '_display');
    
    // Update initial value
    updateSlider(slider, valueDisplay);

    // Update on change
    slider.addEventListener('input', () => {
      updateSlider(slider, valueDisplay);
      
      // Haptic-like visual feedback
      slider.style.transform = 'scaleY(1.2)';
      setTimeout(() => { slider.style.transform = ''; }, 100);
    });
  });
}

function updateSlider(slider, display) {
  if (!display) return;
  
  const value = parseInt(slider.value);
  const min = parseInt(slider.min) || 0;
  const max = parseInt(slider.max) || 100;
  
  // Update displayed value
  display.textContent = value;
  
  // Update gradient fill
  const pct = ((value - min) / (max - min)) * 100;
  slider.style.setProperty('--pct', pct + '%');
  
  // Change color based on value level
  if (pct < 33) {
    display.style.color = 'var(--emerald)';
  } else if (pct < 66) {
    display.style.color = 'var(--amber)';
  } else {
    display.style.color = 'var(--rose)';
  }
}

// -------------------------------------------------------
// 2. MOOD SELECTOR — Visual feedback on selection
// -------------------------------------------------------
function initMoodSelector() {
  const moodOptions = document.querySelectorAll('.mood-option');

  moodOptions.forEach(option => {
    const input = option.querySelector('input[type="radio"]');
    const card = option.querySelector('.mood-card');

    if (input && card) {
      // Click handler on card
      card.addEventListener('click', () => {
        input.checked = true;
        input.dispatchEvent(new Event('change'));
        
        // Brief bounce animation
        card.style.transform = 'scale(0.93)';
        setTimeout(() => { card.style.transform = ''; }, 150);
      });

      // Keyboard accessibility
      card.setAttribute('tabindex', '0');
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          input.checked = true;
        }
      });
    }
  });
}

// -------------------------------------------------------
// 3. FORM VALIDATION — Before submission
// -------------------------------------------------------
function initFormValidation() {
  const studyForm = document.getElementById('study-form');

  if (!studyForm) return;

  studyForm.addEventListener('submit', (e) => {
    const moodSelected = studyForm.querySelector('input[name="mood"]:checked');

    if (!moodSelected) {
      e.preventDefault();
      showToast('⚠️ Please select your mood!', 'error');
      
      // Shake the mood section
      const moodGrid = document.querySelector('.mood-grid');
      if (moodGrid) {
        moodGrid.style.animation = 'none';
        moodGrid.offsetHeight; // Reflow
        moodGrid.style.animation = 'shake 0.4s ease';
      }
      return;
    }

    // Show loading state on submit button
    const btn = studyForm.querySelector('[type="submit"]');
    if (btn) {
      btn.classList.add('loading');
      btn.disabled = true;
    }
  });
}

// CSS shake animation added dynamically
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    20% { transform: translateX(-8px); }
    40% { transform: translateX(8px); }
    60% { transform: translateX(-6px); }
    80% { transform: translateX(6px); }
  }
`;
document.head.appendChild(shakeStyle);

// -------------------------------------------------------
// 4. ALERT AUTO-DISMISS
// -------------------------------------------------------
function initAlerts() {
  const alerts = document.querySelectorAll('.alert');

  alerts.forEach((alert, i) => {
    // Close button
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => dismissAlert(alert));
    }

    // Auto-dismiss after 4 seconds (staggered)
    setTimeout(() => {
      dismissAlert(alert);
    }, 4000 + i * 300);
  });
}

function dismissAlert(alert) {
  alert.style.transition = 'all 0.3s ease';
  alert.style.opacity = '0';
  alert.style.transform = 'translateX(100%)';
  setTimeout(() => alert.remove(), 300);
}

// Toast notification (for client-side messages)
function showToast(message, type = 'info') {
  const container = document.querySelector('.messages-container') 
    || createMessagesContainer();
  
  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button class="alert-close">✕</button>
  `;
  container.appendChild(toast);
  
  const closeBtn = toast.querySelector('.alert-close');
  closeBtn.addEventListener('click', () => dismissAlert(toast));
  
  setTimeout(() => dismissAlert(toast), 4000);
}

function createMessagesContainer() {
  const container = document.createElement('div');
  container.className = 'messages-container';
  document.body.appendChild(container);
  return container;
}

// -------------------------------------------------------
// 5. PAGE ENTRANCE ANIMATIONS
// -------------------------------------------------------
function initAnimations() {
  // Intersection Observer for fade-up on scroll
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  document.querySelectorAll('.card, .stat-card, .timeline-item').forEach(el => {
    observer.observe(el);
  });
}


// -------------------------------------------------------
// 6. CHARTS — Using Chart.js on history page
// -------------------------------------------------------
function initCharts() {
  initMoodChart();
  initFocusChart();
}

function initMoodChart() {
  const canvas = document.getElementById('mood-chart');
  if (!canvas) return;

  const labels = JSON.parse(canvas.dataset.labels || '[]');
  const data = JSON.parse(canvas.dataset.values || '[]');
  if (labels.length === 0) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const moodColors = {
    'Happy': 'rgba(16, 185, 129, 0.8)',
    'Sad': 'rgba(99, 102, 241, 0.8)',
    'Stressed': 'rgba(244, 63, 94, 0.8)',
    'Energetic': 'rgba(245, 158, 11, 0.8)',
    'Tired': 'rgba(148, 163, 184, 0.8)',
  };

  const colors = labels.map(label => moodColors[label] || 'rgba(139, 92, 246, 0.8)');

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors,
        borderColor: 'rgba(6, 8, 15, 0.8)',
        borderWidth: 3,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#94a3b8',
            font: { family: 'DM Sans', size: 13 },
            padding: 16,
            boxWidth: 12,
            borderRadius: 4,
          }
        },
        tooltip: {
          backgroundColor: 'rgba(6, 8, 15, 0.95)',
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.raw} sessions`
          }
        }
      },
      cutout: '65%',
    }
  });
}

function initFocusChart() {
  const canvas = document.getElementById('focus-chart');
  if (!canvas) return;

  const dates = JSON.parse(canvas.dataset.dates || '[]');
  const focus = JSON.parse(canvas.dataset.focus || '[]');
  if (dates.length === 0) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: dates,
      datasets: [{
        label: 'Focus Level',
        data: focus,
        borderColor: 'rgba(139, 92, 246, 0.9)',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        borderWidth: 2.5,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgba(139, 92, 246, 1)',
        pointBorderColor: '#06080f',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#475569', font: { family: 'DM Sans', size: 11 } }
        },
        y: {
          min: 0, max: 10,
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#475569', font: { family: 'DM Sans', size: 11 }, stepSize: 2 }
        }
      },
      plugins: {
        title: {
          display: true,
          text: 'Focus Level Over Time',
          color: '#cbd5e1',
          font: { family: 'DM Sans', size: 14, weight: '600' },
          padding: { bottom: 12 }
        },
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(6, 8, 15, 0.95)',
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          padding: 12,
        }
      }
    }
  });
}


// -------------------------------------------------------
// 7. PRINT / DOWNLOAD PDF
// -------------------------------------------------------
function initPrintButton() {
  const printBtn = document.getElementById('print-pdf');
  if (!printBtn) return;

  printBtn.addEventListener('click', () => {
    // Add a class to style the print view
    document.body.classList.add('printing');
    window.print();
    document.body.classList.remove('printing');
  });
}

// -------------------------------------------------------
// AUTH PAGE — Tab switching (Login ↔ Register)
// -------------------------------------------------------
function switchTab(tab) {
  // Handled via Django URLs, but this adds smooth UX
  document.querySelectorAll('.auth-form').forEach(form => {
    form.style.display = 'none';
  });
  const target = document.getElementById(tab + '-form');
  if (target) target.style.display = 'flex';

  document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
  const activeTab = document.querySelector(`[data-tab="${tab}"]`);
  if (activeTab) activeTab.classList.add('active');
}

// -------------------------------------------------------
// UTILITY: Format date nicely
// -------------------------------------------------------
function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric'
  });
}
