// app.js - UI interactions
document.addEventListener('DOMContentLoaded', function () {
  const navbar = document.querySelector('[data-nav]');
  const navToggle = document.querySelector('.nav-toggle');

  if (navbar && navToggle) {
    navToggle.addEventListener('click', function () {
      const isOpen = navbar.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', String(isOpen));
    });
  }

  // Export CSV button (placeholder)
  const exportBtn = document.getElementById('export-csv');
  if (exportBtn) {
    exportBtn.addEventListener('click', function () {
      alert('Export to CSV (UI placeholder). Implement server-side export endpoint.');
    });
  }

  // Delete confirmation for all delete forms
  const deleteForms = document.querySelectorAll('form.delete-form, form[action*="/delete"]');
  deleteForms.forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (form.dataset.confirmed === '1') {
        return;
      }
      e.preventDefault();
      e.stopImmediatePropagation();
      const message = form.classList.contains('delete-form')
        ? 'Are you sure you want to delete this employee?'
        : 'Are you sure you want to delete this record?';

      if (confirm(message)) {
        form.dataset.confirmed = '1';
        if (typeof form.requestSubmit === 'function') {
          form.requestSubmit();
        } else {
          form.submit();
        }
      }
    });
  });

  // Client-side validation feedback
  const forms = document.querySelectorAll('form');
  forms.forEach(function (form) {
    form.addEventListener('invalid', function (event) {
      const field = event.target;
      showFieldError(field, field.validationMessage);
    }, true);

    form.addEventListener('input', function (event) {
      const field = event.target;
      if (field.classList && field.classList.contains('is-invalid')) {
        clearFieldError(field);
      }
    });

    form.addEventListener('submit', function (event) {
      if (event.defaultPrevented) {
        return;
      }
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
        return;
      }

      const submitter = event.submitter || form.querySelector('button[type="submit"], input[type="submit"]');
      if (submitter) {
        setLoadingState(form, submitter);
      }
    });
  });

  function showFieldError(field, message) {
    if (!field || !field.classList) return;
    field.classList.add('is-invalid');

    let error = field.parentElement.querySelector('.field-error');
    if (!error) {
      error = document.createElement('div');
      error.className = 'field-error';
      field.parentElement.appendChild(error);
    }
    error.textContent = message || 'Please fill out this field.';
  }

  function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const error = field.parentElement.querySelector('.field-error');
    if (error) {
      error.remove();
    }
  }

  function setLoadingState(form, submitter) {
    const buttons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
    buttons.forEach(function (btn) {
      btn.disabled = true;
    });

    if (submitter.classList) {
      submitter.classList.add('is-loading');
    }

    if (!submitter.dataset.originalText) {
      submitter.dataset.originalText = submitter.textContent.trim();
    }

    const loadingText = submitter.dataset.loadingText || 'Processing...';
    submitter.textContent = loadingText;
  }

  // Tables: search, sort, paginate
  const tables = document.querySelectorAll('table.js-sortable');
  tables.forEach(function (table) {
    initializeTable(table);
  });

  function initializeTable(table) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;

    const noDataCell = tbody.querySelector('.no-data');
    const emptyMessage = table.dataset.emptyMessage || (noDataCell ? noDataCell.textContent.trim() : 'No results found.');

    const allRows = Array.from(tbody.querySelectorAll('tr'))
      .filter(function (row) { return !row.querySelector('.no-data'); });

    const paginateEnabled = table.dataset.clientPaginate === 'true';

    const state = {
      table: table,
      tbody: tbody,
      allRows: allRows,
      filteredRows: allRows.slice(),
      pageSize: paginateEnabled ? parseInt(table.dataset.pageSize || '10', 10) : 0,
      currentPage: 1,
      emptyMessage: emptyMessage,
      pagination: null,
      paginateEnabled: paginateEnabled
    };

    setupSorting(state);
    setupSearch(state);
    setupPagination(state);
    renderTable(state);
  }

  function setupSorting(state) {
    const sortButtons = state.table.querySelectorAll('.sort-btn');
    sortButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        const isAsc = button.classList.contains('is-asc');
        sortButtons.forEach(function (btn) { btn.classList.remove('is-asc', 'is-desc'); });
        button.classList.add(isAsc ? 'is-desc' : 'is-asc');

        const columnIndex = Array.from(button.closest('tr').children).indexOf(button.parentElement);
        const type = button.dataset.type || 'text';

        state.filteredRows.sort(function (a, b) {
          const aText = getCellValue(a, columnIndex);
          const bText = getCellValue(b, columnIndex);
          const result = compareValues(aText, bText, type);
          return isAsc ? -result : result;
        });

        state.currentPage = 1;
        renderTable(state);
      });
    });
  }

  function getCellValue(row, index) {
    const cell = row.children[index];
    if (!cell) return '';
    return cell.textContent.trim();
  }

  function compareValues(a, b, type) {
    if (type === 'number') {
      const aNum = parseFloat(a.replace(/[^0-9.-]/g, '')) || 0;
      const bNum = parseFloat(b.replace(/[^0-9.-]/g, '')) || 0;
      return aNum - bNum;
    }

    if (type === 'date') {
      const aDate = Date.parse(a);
      const bDate = Date.parse(b);
      return (aDate || 0) - (bDate || 0);
    }

    return a.localeCompare(b);
  }

  function setupSearch(state) {
    if (!state.table.id) return;
    const searchInput = document.querySelector('.table-search[data-table-search="' + state.table.id + '"]');
    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
      const query = searchInput.value.trim().toLowerCase();
      state.filteredRows = state.allRows.filter(function (row) {
        return row.textContent.toLowerCase().includes(query);
      });
      state.currentPage = 1;
      renderTable(state);
    });
  }

  function setupPagination(state) {
    if (!state.table.id) return;
    const pagination = document.querySelector('.js-pagination[data-table="' + state.table.id + '"]');
    state.pagination = pagination;
  }

  function renderTable(state) {
    const totalRows = state.filteredRows.length;
    const pageSize = state.pageSize;
    const totalPages = state.paginateEnabled && pageSize > 0 ? Math.ceil(totalRows / pageSize) : 1;
    const currentPage = Math.min(state.currentPage, totalPages || 1);
    state.currentPage = currentPage;

    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const pageRows = state.paginateEnabled && pageSize > 0 ? state.filteredRows.slice(start, end) : state.filteredRows;

    state.tbody.innerHTML = '';

    if (pageRows.length === 0) {
      const columnCount = state.table.querySelectorAll('thead th').length;
      const emptyRow = document.createElement('tr');
      const cell = document.createElement('td');
      cell.colSpan = columnCount;
      cell.className = 'no-data';
      cell.textContent = state.emptyMessage || 'No results found.';
      emptyRow.appendChild(cell);
      state.tbody.appendChild(emptyRow);
    } else {
      pageRows.forEach(function (row) {
        state.tbody.appendChild(row);
      });
    }

    renderPagination(state, totalPages);
  }

  function renderPagination(state, totalPages) {
    if (!state.pagination || !state.paginateEnabled) return;
    state.pagination.innerHTML = '';

    if (totalPages <= 1) return;

    const createButton = function (label, page, isActive, isDisabled) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = label;
      button.className = 'btn btn-secondary btn-small' + (isActive ? ' active' : '');
      button.disabled = !!isDisabled;
      button.addEventListener('click', function () {
        state.currentPage = page;
        renderTable(state);
      });
      return button;
    };

    state.pagination.appendChild(createButton('Prev', Math.max(1, state.currentPage - 1), false, state.currentPage === 1));

    const maxButtons = 5;
    let startPage = Math.max(1, state.currentPage - 2);
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);

    if (endPage - startPage < maxButtons - 1) {
      startPage = Math.max(1, endPage - maxButtons + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      state.pagination.appendChild(createButton(String(i), i, i === state.currentPage, false));
    }

    state.pagination.appendChild(createButton('Next', Math.min(totalPages, state.currentPage + 1), false, state.currentPage === totalPages));
  }
});
