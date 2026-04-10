/* ============================================================
   EduLearn Platform — main.js
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

  /* ── SIDEBAR TOGGLE (Mobile) ── */
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });

    // Close sidebar on outside click
    document.addEventListener('click', function (e) {
      if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  /* ── AUTO-DISMISS TOASTS ── */
  const toastEls = document.querySelectorAll('.toast');
  toastEls.forEach(function (el) {
    const toast = bootstrap.Toast.getOrCreateInstance(el);
    toast.show();
    setTimeout(() => toast.hide(), 4500);
  });

  /* ── PASSWORD TOGGLE (shared helper, also called inline) ── */
  window.togglePassword = function (fieldId, btn) {
    const field = document.getElementById(fieldId);
    const icon  = btn.querySelector('i');
    if (!field) return;
    if (field.type === 'password') {
      field.type = 'text';
      icon.classList.replace('bi-eye', 'bi-eye-slash');
    } else {
      field.type = 'password';
      icon.classList.replace('bi-eye-slash', 'bi-eye');
    }
  };

  /* ── STAR RATING HOVER EFFECT ── */
  const starLabels = document.querySelectorAll('.star-rating label');
  starLabels.forEach(function (label, i) {
    label.addEventListener('mouseenter', function () {
      starLabels.forEach(function (l, j) {
        const icon = l.querySelector('i');
        if (icon) {
          if (j <= i) {
            icon.className = 'bi bi-star-fill text-warning';
          } else {
            icon.className = 'bi bi-star text-muted';
          }
        }
      });
    });
  });

  const starRating = document.querySelector('.star-rating');
  if (starRating) {
    starRating.addEventListener('mouseleave', function () {
      const checked = starRating.querySelector('input[type=radio]:checked');
      const checkedVal = checked ? parseInt(checked.value) : 0;
      starLabels.forEach(function (l, j) {
        const icon = l.querySelector('i');
        if (icon) {
          if (j < checkedVal) {
            icon.className = 'bi bi-star-fill text-warning';
          } else {
            icon.className = 'bi bi-star text-muted';
          }
        }
      });
    });
  }

  /* ── FILE INPUT LABEL UPDATE ── */
  document.querySelectorAll('input[type=file]').forEach(function (input) {
    input.addEventListener('change', function () {
      const label = input.closest('.mb-3')?.querySelector('.form-text');
      if (label && input.files.length > 0) {
        label.textContent = '✓ ' + input.files[0].name;
        label.style.color = '#10B981';
      }
    });
  });

  /* ── SMOOTH SCROLL FOR ANCHOR LINKS ── */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  /* ── PROGRESS BARS ANIMATE ON LOAD ── */
  const bars = document.querySelectorAll('.progress-bar');
  bars.forEach(function (bar) {
    const target = bar.style.width;
    bar.style.width = '0%';
    setTimeout(function () {
      bar.style.width = target;
    }, 300);
  });

  /* ── CONFIRM DELETE FORMS ── */
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  /* ── TABLE ROW HIGHLIGHT ── */
  document.querySelectorAll('.table tbody tr').forEach(function (row) {
    row.style.cursor = 'default';
  });

});
