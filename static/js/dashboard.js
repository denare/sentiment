// Dashboard JavaScript - Sentiment Analysis System

$(document).ready(function() {
    // Character counter
    $('#textContent').on('input', function() {
        const charCount = $(this).val().length;
        $('#charCount').text(charCount);
        
        if (charCount > 4500) {
            $('#charCount').parent().addClass('text-danger');
        } else {
            $('#charCount').parent().removeClass('text-danger');
        }
    });
    
    // File upload handler
    $('#textFile').on('change', function(e) {
        const file = e.target.files[0];
        
        if (file) {
            if (file.name.endsWith('.txt')) {
                const reader = new FileReader();
                
                reader.onload = function(event) {
                    const content = event.target.result;
                    $('#textContent').val(content);
                    $('#textContent').trigger('input'); // Update char count
                    
                    // Show notification
                    showNotification('File loaded successfully!', 'success');
                };
                
                reader.readAsText(file);
            } else {
                showNotification('Please upload a .txt file', 'danger');
                $(this).val('');
            }
        }
    });
    
    // Clear button
    $('#clearBtn').on('click', function() {
        $('#textContent').val('');
        $('#textFile').val('');
        $('#resultPanel').slideUp();
        $('#charCount').text('0');
        $('#detectedLang').text('Auto-detect').removeClass('bg-success bg-info').addClass('bg-secondary');
    });
    
    // Form submission
    $('#analysisForm').on('submit', function(e) {
        e.preventDefault();
        
        const textContent = $('#textContent').val().trim();
        
        // Validation
        if (!textContent) {
            showNotification('Please enter some text before analyzing', 'danger');
            return;
        }
        
        if (textContent.length < 5) {
            showNotification('Text must be at least 5 characters', 'warning');
            return;
        }
        
        if (textContent.length > 5000) {
            showNotification('Text exceeds maximum length of 5000 characters', 'danger');
            return;
        }
        
        // Show loading
        $('#loadingSpinner').show();
        $('#resultPanel').slideUp();
        
        // Prepare form data
        const formData = new FormData();
        formData.append('text_content', textContent);
        formData.append('language', $('#language').val());
        
        // AJAX request
        $.ajax({
            url: '/analyze',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('#loadingSpinner').hide();
                
                if (response.success) {
                    displayResult(response.result);
                } else {
                    showNotification('Analysis failed. Please try again.', 'danger');
                }
            },
            error: function(xhr) {
                $('#loadingSpinner').hide();
                
                let errorMsg = 'An error occurred during analysis';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                
                showNotification(errorMsg, 'danger');
            }
        });
    });
    
    // Display result function
    function displayResult(result) {
        const sentiment = result.sentiment;
        const confidence = result.confidence;
        const language = result.language;
        const textPreview = result.text_preview;
        
        // Determine color class
        let colorClass, icon, bgClass;
        if (sentiment === 'Positive') {
            colorClass = 'success';
            icon = 'fa-smile';
            bgClass = 'result-positive';
        } else if (sentiment === 'Negative') {
            colorClass = 'danger';
            icon = 'fa-frown';
            bgClass = 'result-negative';
        } else {
            colorClass = 'secondary';
            icon = 'fa-meh';
            bgClass = 'result-neutral';
        }
        
        // Build result HTML
        const resultHTML = `
            <div class="${bgClass} fade-in">
                <div class="text-center">
                    <div class="sentiment-badge badge bg-${colorClass}">
                        <i class="fas ${icon}"></i> ${sentiment.toUpperCase()}
                    </div>
                </div>
                
                <div class="mt-3">
                    <strong>Confidence Score:</strong>
                    <div class="progress mt-2 confidence-bar">
                        <div class="progress-bar bg-${colorClass}" 
                             role="progressbar" 
                             style="width: ${confidence}%">
                            ${confidence}%
                        </div>
                    </div>
                </div>
                
                <div class="row mt-3">
                    <div class="col-md-6">
                        <strong>Detected Language:</strong>
                        <span class="badge bg-info ms-2">${language}</span>
                    </div>
                    <div class="col-md-6 text-md-end">
                        <strong>Analysis Saved:</strong>
                        <i class="fas fa-check-circle text-success ms-2"></i>
                    </div>
                </div>
                
                <div class="mt-3">
                    <small class="text-muted">
                        <strong>Text Preview:</strong> ${textPreview}
                    </small>
                </div>
                
                <div class="mt-3 text-center">
                    <a href="/history" class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-history"></i> View Full History
                    </a>
                    <button class="btn btn-outline-secondary btn-sm" onclick="$('#clearBtn').click()">
                        <i class="fas fa-redo"></i> Analyze Another
                    </button>
                </div>
            </div>
        `;
        
        $('#resultContent').html(resultHTML);
        $('#resultPanel').slideDown();
        
        // Update detected language badge
        $('#detectedLang')
            .text(language)
            .removeClass('bg-secondary bg-success bg-info')
            .addClass(language === 'English' ? 'bg-info' : 'bg-success');
        
        // Show success notification
        showNotification('Analysis completed successfully!', 'success');
        
        // Reload page stats after 1 second to update sidebar
        setTimeout(function() {
            location.reload();
        }, 2000);
    }
    
    // Show notification function
    function showNotification(message, type) {
        const alertHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Remove existing alerts
        $('.container > .alert').remove();
        
        // Add new alert
        $('.container').first().prepend(alertHTML);
        
        // Auto dismiss after 5 seconds
        setTimeout(function() {
            $('.alert').fadeOut(function() {
                $(this).remove();
            });
        }, 5000);
    }
});
