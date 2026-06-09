// ============================================
// Document Preview Modal
// ============================================
function abrirDocumento(url, tipo, nombre, fecha) {
  var overlay = document.createElement('div');
  overlay.className = 'doc-modal-overlay';

  var iconClass = tipo.toLowerCase();
  var iconSvg = '';
  var previewContent = '';

  if (tipo === 'PDF') {
    iconSvg = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 13l2-2 2 2 3-3 2 2v2a1 1 0 01-1 1H8a1 1 0 01-1-1v-1z"/></svg>';
    previewContent = '<iframe src="' + url + '" title="' + nombre + '"></iframe>';
  } else if (tipo === 'WORD') {
    iconSvg = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>';
    previewContent = '<div class="unsupported-preview"><div class="big-icon">' + iconSvg.replace('width="16"','width="48"').replace('height="16"','height="48"') + '</div><p class="font-medium text-gray-700 mb-1">Documento de Word</p><p class="text-sm text-gray-500">Vista previa no disponible para este formato.</p><p class="text-sm text-gray-500 mt-2">Descarga el archivo para visualizarlo.</p></div>';
  } else if (tipo === 'IMAGEN') {
    iconSvg = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>';
    previewContent = '<img src="' + url + '" alt="' + nombre + '">';
  } else {
    iconSvg = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>';
    previewContent = '<div class="unsupported-preview"><div class="big-icon">' + iconSvg.replace('width="16"','width="48"').replace('height="16"','height="48"') + '</div><p class="font-medium text-gray-700 mb-1">Archivo</p><p class="text-sm text-gray-500">Vista previa no disponible.</p><p class="text-sm text-gray-500 mt-2">Descarga el archivo para visualizarlo.</p></div>';
  }

  overlay.innerHTML = '<div class="doc-modal">' +
    '<div class="doc-modal-header">' +
      '<div class="modal-title">' +
        '<span class="title-icon ' + iconClass + '">' + iconSvg + '</span>' +
        '<span class="truncate max-w-md" title="' + (nombre || '').replace(/"/g,'&quot;') + '">' + (nombre || '') + '</span>' +
      '</div>' +
      '<div class="modal-actions">' +
        '<a href="' + url + '" download class="download-btn" title="Descargar">' +
          '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>' +
        '</a>' +
        '<a href="' + url + '" target="_blank" class="open-btn" title="Abrir en nueva pestaña">' +
          '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>' +
        '</a>' +
        '<button class="close-btn" title="Cerrar (Esc)">' +
          '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>' +
        '</button>' +
      '</div>' +
    '</div>' +
    '<div class="doc-modal-body">' + previewContent + '</div>' +
    '<div class="doc-modal-footer">' +
      '<span class="truncate">' + (nombre || '') + '</span>' +
      '<span>' + (fecha || '') + '</span>' +
    '</div>' +
  '</div>';

  document.body.appendChild(overlay);

  function cerrarModal() { overlay.remove(); document.removeEventListener('keydown', onKey); }

  overlay.querySelector('.close-btn').onclick = cerrarModal;
  overlay.addEventListener('click', function(e) { if (e.target === this) cerrarModal(); });

  function onKey(e) { if (e.key === 'Escape') cerrarModal(); }
  document.addEventListener('keydown', onKey);
}

// ============================================
// Drag & Drop Upload (from grid area)
// ============================================
function iniciarDragDrop(gridId, uploadUrl) {
  var grid = document.getElementById(gridId);
  if (!grid) return;

  var dropOverlay = document.createElement('div');
  dropOverlay.className = 'doc-drop-overlay';
  dropOverlay.innerHTML = '<div class="drop-content">' +
    '<svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>' +
    '<p class="drop-title">Suelta tus archivos aquí</p>' +
    '<p class="drop-hint">PDF, Word, imágenes</p>' +
  '</div>';
  grid.appendChild(dropOverlay);

  var dragCounter = 0;

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  document.addEventListener('dragenter', preventDefaults);
  document.addEventListener('dragover', preventDefaults);
  document.addEventListener('drop', preventDefaults);

  grid.addEventListener('dragenter', function(e) {
    preventDefaults(e);
    dragCounter++;
    grid.classList.add('drag-active');
  });

  grid.addEventListener('dragleave', function(e) {
    preventDefaults(e);
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      grid.classList.remove('drag-active');
    }
  });

  grid.addEventListener('dragover', function(e) {
    preventDefaults(e);
    grid.classList.add('drag-active');
  });

  grid.addEventListener('drop', function(e) {
    preventDefaults(e);
    grid.classList.remove('drag-active');
    dragCounter = 0;

    var files = e.dataTransfer.files;
    if (files.length > 0) {
      subirArchivo(files[0], uploadUrl, grid);
    }
  });
}

function subirArchivo(file, url, grid) {
  // Show uploading feedback on the drop overlay
  var overlay = grid.querySelector('.doc-drop-overlay');
  if (overlay) {
    overlay.innerHTML = '<div class="drop-content">' +
      '<svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24" class="spinner"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>' +
      '<p class="drop-title">Subiendo...</p>' +
    '</div>';
  }

  // Get CSRF token from the modal form (or any form in the page)
  var csrfToken = '';
  var csrfInput = document.querySelector('#modal-subida [name=csrfmiddlewaretoken]');
  if (!csrfInput) csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
  if (csrfInput) csrfToken = csrfInput.value;

  var formData = new FormData();
  formData.append('csrfmiddlewaretoken', csrfToken);
  formData.append('archivo', file);
  formData.append('descripcion', file.name);

  fetch(url, {
    method: 'POST',
    body: formData,
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  }).then(function(response) {
    if (response.redirected || response.ok) {
      window.location.reload();
    } else {
      throw new Error('Error al subir archivo');
    }
  }).catch(function(err) {
    if (overlay) {
      overlay.innerHTML = '<div class="drop-content">' +
        '<svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>' +
        '<p class="drop-title">Error al subir</p>' +
        '<p class="drop-hint">Intente de nuevo</p>' +
      '</div>';
      setTimeout(function() {
        overlay.innerHTML = '<div class="drop-content">' +
          '<svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>' +
          '<p class="drop-title">Suelta tus archivos aquí</p>' +
          '<p class="drop-hint">PDF, Word, imágenes</p>' +
        '</div>';
      }, 3000);
    }
  });
}

// ============================================
// Upload Modal - Shared Utilities
// ============================================

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

function getFileIcon(fileName) {
  var name = fileName.toLowerCase();
  if (name.indexOf('.pdf') !== -1) return 'pdf';
  if (/\.docx?$/.test(name)) return 'word';
  if (/\.(png|jpg|jpeg|webp|gif)$/.test(name)) return 'image';
  return 'other';
}

var ICON_COLORS = {pdf: '#dc2626', word: '#2563eb', image: '#16a34a', other: '#6b7280'};
var ICON_BGS    = {pdf: '#fef2f2', word: '#eff6ff', image: '#dcfce7', other: '#f3f4f6'};

function abrirModalUpload(modalId) {
  var modal = document.getElementById(modalId);
  if (!modal) return;
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  void modal.offsetHeight; // trigger reflow for animation
}

function _suffix(s) {
  return s ? '-' + s : '';
}

function cerrarModalUpload(modalId, suffix) {
  var modal = document.getElementById(modalId);
  if (!modal) return;
  modal.style.display = 'none';
  document.body.style.overflow = '';
  if (suffix !== undefined) limpiarArchivoUpload(suffix);
}

function limpiarArchivoUpload(suffix) {
  var s = _suffix(suffix);
  var input = document.getElementById('file-input' + s + '-modal');
  if (input) input.value = '';
  var fileCard = document.getElementById('upload-file-card' + s);
  var dropArea = document.getElementById('upload-drop' + s);
  if (fileCard) fileCard.style.display = 'none';
  if (dropArea) dropArea.style.display = 'block';
}

function onFileSelectedUpload(input, suffix) {
  var file = input.files[0];
  if (!file) return;
  var iconType = getFileIcon(file.name);
  var s = _suffix(suffix);

  var nameEl = document.getElementById('upload-file-name' + s);
  var sizeEl = document.getElementById('upload-file-size' + s);
  var iconEl = document.getElementById('upload-file-icon' + s);
  var fileCard = document.getElementById('upload-file-card' + s);
  var dropArea = document.getElementById('upload-drop' + s);

  if (nameEl) nameEl.textContent = file.name;
  if (sizeEl) sizeEl.textContent = formatFileSize(file.size);
  if (iconEl) {
    iconEl.style.color = ICON_COLORS[iconType] || '#6b7280';
    iconEl.style.background = ICON_BGS[iconType] || '#f3f4f6';
  }
  if (dropArea) dropArea.style.display = 'none';
  if (fileCard) fileCard.style.display = 'flex';
}

function initModalClickOutside(modalId, closeFn) {
  document.addEventListener('click', function(e) {
    if (e.target === document.getElementById(modalId)) closeFn();
  });
}

function initModalEscape(closeFn) {
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeFn();
  });
}

function initDropZone(dropAreaId, fileInputId, callbackName) {
  var dropArea = document.getElementById(dropAreaId);
  if (!dropArea) return;

  dropArea.addEventListener('click', function() {
    document.getElementById(fileInputId).click();
  });

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function(ev) {
    dropArea.addEventListener(ev, function(e) {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  var dragCounter = 0;

  dropArea.addEventListener('dragenter', function(e) {
    e.preventDefault();
    dragCounter++;
    dropArea.classList.add('drag-over');
  });

  dropArea.addEventListener('dragleave', function(e) {
    e.preventDefault();
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      dropArea.classList.remove('drag-over');
    }
  });

  dropArea.addEventListener('drop', function(e) {
    e.preventDefault();
    dropArea.classList.remove('drag-over');
    dragCounter = 0;
    var files = e.dataTransfer.files;
    if (files.length > 0) {
      var input = document.getElementById(fileInputId);
      input.files = files;
      if (typeof window[callbackName] === 'function') {
        window[callbackName](input);
      }
    }
  });
}

// ============================================
// Auto-init on DOMContentLoaded
// ============================================
document.addEventListener('DOMContentLoaded', function() {
  var grids = document.querySelectorAll('.doc-grid');
  grids.forEach(function(grid) {
    var uploadUrl = grid.getAttribute('data-upload-url');
    if (grid.id && uploadUrl) {
      iniciarDragDrop(grid.id, uploadUrl);
    }
  });
});
