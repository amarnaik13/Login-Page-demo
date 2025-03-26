document.addEventListener('DOMContentLoaded', function() {
    // Form submission handling
    const uploadForm = document.getElementById('uploadForm');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsCard = document.getElementById('resultsCard');
    let uploadedFiles = {};

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading spinner
            loadingSpinner.classList.remove('d-none');
            
            // Create FormData object
            const formData = new FormData();
            formData.append('file1', document.getElementById('file1').files[0]);
            formData.append('file2', document.getElementById('file2').files[0]);
            formData.append('isCvSkills', document.getElementById('isCvSkills').checked);
            
            // Send AJAX request
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Store the uploaded file paths
                uploadedFiles = data;
                
                // Load the recommendations data
                loadRecommendations(data);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred during file upload: ' + error.message);
                loadingSpinner.classList.add('d-none');
            });
        });
    }
    
    // Function to load recommendations data
    function loadRecommendations(fileData) {
        // First load RR recommendations
        fetch(`/recommendations/rr?rr_file=${fileData.file1}&bench_file=${fileData.file2}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Populate RR table
                populateTable('rrTable', data);
                
                // Now load profile recommendations
                return fetch(`/recommendations/profiles?rr_file=${fileData.file1}&bench_file=${fileData.file2}`);
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Populate profiles table
                populateTable('profilesTable', data);
                
                // Hide loading spinner and show results
                loadingSpinner.classList.add('d-none');
                resultsCard.classList.remove('d-none');
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while loading recommendations: ' + error.message);
                loadingSpinner.classList.add('d-none');
            });
    }
    
    // Function to populate table with data
    function populateTable(tableId, data) {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        tbody.innerHTML = ''; // Clear existing rows
        
        data.forEach(item => {
            const row = document.createElement('tr');
            
            // Create cells based on which table we're populating
            if (tableId === 'rrTable') {
                row.innerHTML = `
                    <td>${item.RR || ''}</td>
                    <td>${item['RR Skills'] || ''}</td>
                    <td>${item['Portal ID'] || ''}</td>
                    <td>${item['Employee Name'] || ''}</td>
                    <td>${item['Match Score'] || ''}%</td>
                    <td>${item['Matched Skills'] || ''}</td>
                    <td>${item['Recommended Trainings'] || ''}</td>
                `;
            } else {
                row.innerHTML = `
                    <td>${item['Portal ID'] || ''}</td>
                    <td>${item['Employee Name'] || ''}</td>
                    <td>${item['Overall Employee Skills'] || ''}</td>
                    <td>${item.RR || ''}</td>
                    <td>${item['RR Skills'] || ''}</td>
                    <td>${item['Match Score'] || ''}%</td>
                    <td>${item['Matched Skills'] || ''}</td>
                    <td>${item['Recommended Trainings'] || ''}</td>
                `;
            }
            
            // Highlight rows with high match scores
            if (parseInt(item['Match Score']) >= 80) {
                row.classList.add('highlighted');
            }
            
            tbody.appendChild(row);
        });
    }
    
    // Alert dismissal
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const closeBtn = alert.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                alert.remove();
            });
            
            // Auto dismiss after 5 seconds
            setTimeout(() => {
                alert.classList.remove('show');
                setTimeout(() => {
                    alert.remove();
                }, 150);
            }, 5000);
        }
    });
});