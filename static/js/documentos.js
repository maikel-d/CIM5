// ============================================
// Security: HTML Escaping & URL Sanitization
// ============================================
function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.appendChild(document.createTextNode(text));
  return div.innerHTML;
}

function sanitizeUrl(url) {
  if (!url) return '';
  // Block dangerous URL schemes (javascript:, data:, vbscript:)
  if (/^\s*javascript:/i.test(url)) return '';
  if (/^\s*data:/.test(url)) return '';
  if (/^\s*vbscript:/i.test(url)) return '';
  return url;
}

// ============================================
// Document Preview Modal
// ============================================
function abrirDocumento(url, tipo, nombre, fecha) {
  var overlay = document.createElement('div');
  overlay.className = 'doc-modal-overlay';

  var iconClass = escapeHtml(tipo.toLowerCase());
  var iconSvg = '';
  var previewContent = '';

  if (tipo === 'PDF') {
    iconSvg = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 13l2-2 2 2 3-3 2 2v2a1 1 0 01-1 1H8a1 1 0 01-1-1v-1z"/></svg>';
    previewContent = '<iframe src="' + sanitizeUrl(url) + '" title="' + escapeHtml(nombre) + '"></iframe>';
  } else if (tipo === 'WORD') {
    iconSvg = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>';
    previewContent = '<div class="unsupported-preview"><div class="big-icon">' + iconSvg.replace('width="16"','width="48"').replace('height="16"','height="48"') + '</div><p class="font-medium text-gray-700 mb-1">Documento de Word</p><p class="text-sm text-gray-500">Vista previa no disponible para este formato.</p><p class="text-sm text-gray-500 mt-2">Descarga el archivo para visualizarlo.</p></div>';
  } else if (tipo === 'IMAGEN') {
    iconSvg = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>';
    previewContent = '<img src="' + sanitizeUrl(url) + '" alt="' + escapeHtml(nombre) + '">';
  } else {
    iconSvg = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>';
    previewContent = '<div class="unsupported-preview"><div class="big-icon">' + iconSvg.replace('width="16"','width="48"').replace('height="16"','height="48"') + '</div><p class="font-medium text-gray-700 mb-1">Archivo</p><p class="text-sm text-gray-500">Vista previa no disponible.</p><p class="text-sm text-gray-500 mt-2">Descarga el archivo para visualizarlo.</p></div>';
  }

  overlay.innerHTML = '<div class="doc-modal">' +
    '<div class="doc-modal-header">' +
      '<div class="modal-title">' +
        '<span class="title-icon ' + iconClass + '">' + iconSvg + '</span>' +
        '<span class="truncate max-w-md" title="' + escapeHtml(nombre) + '">' + escapeHtml(nombre) + '</span>' +
      '</div>' +
      '<div class="modal-actions">' +
        '<a href="' + sanitizeUrl(url) + '" download class="download-btn" title="Descargar">' +
          '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>' +
        '</a>' +
        '<a href="' + sanitizeUrl(url) + '" target="_blank" class="open-btn" title="Abrir en nueva pestaña">' +
          '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>' +
        '</a>' +
        '<button class="close-btn" title="Cerrar (Esc)">' +
          '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>' +
        '</button>' +
      '</div>' +
    '</div>' +
    '<div class="doc-modal-body">' + previewContent + '</div>' +
    '<div class="doc-modal-footer">' +
      '<span class="truncate">' + escapeHtml(nombre) + '</span>' +
      '<span>' + escapeHtml(fecha) + '</span>' +
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
// Batch Upload with Progress Bar
// ============================================
function iniciarBatchUpload() {
  var zone = document.getElementById('batch-upload-zone');
  if (!zone) return;
  var input = document.getElementById('batch-file-input');
  var preview = document.getElementById('batch-preview');
  var progressContainer = document.getElementById('batch-progress');
  var progressBar = document.getElementById('batch-progress-bar');
  var progressText = document.getElementById('batch-progress-text');
  var submitBtn = document.getElementById('batch-submit-btn');
  var counter = document.getElementById('batch-file-count');

  var selectedFiles = [];

  // Click to select files
  zone.addEventListener('click', function(e) {
    if (e.target.closest('.batch-file-remove') || e.target.closest('#batch-submit-btn')) return;
    input.click();
  });

  input.addEventListener('change', function() {
    addFiles(this.files);
    this.value = '';
  });

  // Drag & Drop on zone
  var dragCounter = 0;
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function(ev) {
    zone.addEventListener(ev, function(e) {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  zone.addEventListener('dragenter', function(e) {
    e.preventDefault();
    dragCounter++;
    zone.classList.add('drag-over');
  });

  zone.addEventListener('dragleave', function(e) {
    e.preventDefault();
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      zone.classList.remove('drag-over');
    }
  });

  zone.addEventListener('drop', function(e) {
    e.preventDefault();
    zone.classList.remove('drag-over');
    dragCounter = 0;
    addFiles(e.dataTransfer.files);
  });

  function addFiles(files) {
    for (var i = 0; i < files.length; i++) {
      var f = files[i];
      // Skip duplicates
      var dup = false;
      for (var j = 0; j < selectedFiles.length; j++) {
        if (selectedFiles[j].name === f.name && selectedFiles[j].size === f.size) {
          dup = true;
          break;
        }
      }
      if (!dup) selectedFiles.push(f);
    }
    renderPreview();
  }

  function renderPreview() {
    if (selectedFiles.length === 0) {
      preview.innerHTML = '';
      preview.style.display = 'none';
      document.getElementById('batch-actions').style.display = 'none';
      submitBtn.style.display = 'none';
      counter.textContent = '0';
      return;
    }
    preview.style.display = 'block';
    document.getElementById('batch-actions').style.display = 'block';
    submitBtn.style.display = 'flex';
    counter.textContent = selectedFiles.length;

    var html = '';
    for (var i = 0; i < selectedFiles.length; i++) {
      var f = selectedFiles[i];
      var iconType = getFileIcon(f.name);
      var iconColor = ICON_COLORS[iconType] || '#6b7280';
      var iconBg = ICON_BGS[iconType] || '#f3f4f6';
      html += '<div class="batch-file-item" data-index="' + i + '">' +
        '<div class="batch-file-icon" style="color:' + iconColor + ';background:' + iconBg + '">' +
          '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>' +
        '</div>' +
        '<div class="batch-file-info">' +
          '<span class="batch-file-name">' + escapeHtml(f.name) + '</span>' +
          '<span class="batch-file-size">' + formatFileSize(f.size) + '</span>' +
        '</div>' +
        '<button type="button" class="batch-file-remove" onclick="removeBatchFile(' + i + ')" title="Quitar">' +
          '<svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>' +
        '</button>' +
      '</div>';
    }
    preview.innerHTML = html;
  }

  window.removeBatchFile = function(index) {
    selectedFiles.splice(index, 1);
    renderPreview();
  };

  // Submit upload
  submitBtn.addEventListener('click', function() {
    if (selectedFiles.length === 0) return;
    uploadFiles();
  });

  function uploadFiles() {
    var formData = new FormData();
    for (var i = 0; i < selectedFiles.length; i++) {
      formData.append('archivos', selectedFiles[i]);
    }
    var csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) formData.append('csrfmiddlewaretoken', csrfInput.value);

    // Get selected category from active category filter
    var catSelect = document.getElementById('batch-categoria');
    if (catSelect) formData.append('categoria', catSelect.value);

    // Show progress
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Subiendo...';
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressText.textContent = '0 / ' + selectedFiles.length + ' archivos...';

    var xhr = new XMLHttpRequest();
    xhr.open('POST', batchUploadUrl, true);

    xhr.upload.onprogress = function(e) {
      if (e.lengthComputable) {
        var pct = Math.round((e.loaded / e.total) * 100);
        progressBar.style.width = pct + '%';
        progressText.textContent = 'Subiendo... ' + pct + '%';
      }
    };

    xhr.onload = function() {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          var data = JSON.parse(xhr.responseText);
          if (data.success) {
            progressBar.style.width = '100%';
            progressText.textContent = 'Completado: ' + data.created + ' subido(s)' +
              (data.errors > 0 ? ', ' + data.errors + ' error(es)' : '');
            progressBar.classList.add('bg-green-500');
            // Reload after short delay to show complete status
            setTimeout(function() { window.location.reload(); }, 1500);
          } else {
            progressText.textContent = 'Error: ' + (data.error || 'Error desconocido');
            resetButton();
          }
        } catch(e) {
          progressText.textContent = 'Error al procesar respuesta';
          resetButton();
        }
      } else {
        progressText.textContent = 'Error del servidor: ' + xhr.status;
        resetButton();
      }
    };

    xhr.onerror = function() {
      progressText.textContent = 'Error de conexión';
      resetButton();
    };

    xhr.send(formData);
  }

  function resetButton() {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg> Subir ' + selectedFiles.length + ' archivo(s)';
  }
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
  // Init batch upload zone
  if (document.getElementById('batch-upload-zone')) {
    iniciarBatchUpload();
  }
});
