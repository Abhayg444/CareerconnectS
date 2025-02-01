document.addEventListener('DOMContentLoaded', function() {
    let experienceCount = 1;
    let projectCount = 1;

    // Add more experience dynamically
    document.getElementById('addExperience').addEventListener('click', function() {
        experienceCount++;
        const experienceDiv = document.createElement('div');
        experienceDiv.innerHTML = `
            <div class="form-group">
                <label for="org${experienceCount}">Institute/Organization</label>
                <input type="text" class="form-control" id="org${experienceCount}" placeholder="Institute/Organization">
            </div>
            <div class="form-group">
                <label for="position${experienceCount}">Position</label>
                <input type="text" class="form-control" id="position${experienceCount}" placeholder="Position">
            </div>
            <div class="form-group">
                <label for="duration${experienceCount}">Duration</label>
                <input type="text" class="form-control" id="duration${experienceCount}" placeholder="Duration">
            </div>
            <div class="form-group">
                <label for="description${experienceCount}">Description</label>
                <textarea class="form-control" id="description${experienceCount}" rows="3" placeholder="Description"></textarea>
            </div>
        `;
        document.getElementById('experienceSection').appendChild(experienceDiv);
    });

    // Add more projects dynamically
    document.getElementById('addProject').addEventListener('click', function() {
        projectCount++;
        const projectDiv = document.createElement('div');
        projectDiv.innerHTML = `
            <div class="form-group">
                <label for="project${projectCount}">Project ${projectCount} Title</label>
                <input type="text" class="form-control" id="project${projectCount}" placeholder="Project ${projectCount} Title">
            </div>
            <div class="form-group">
                <label for="projectDesc${projectCount}">Project ${projectCount} Description</label>
                <textarea class="form-control" id="projectDesc${projectCount}" rows="3" placeholder="Project ${projectCount} Description"></textarea>
            </div>
        `;
        document.getElementById('projectSection').appendChild(projectDiv);
    });

    // Generate PDF
    document.getElementById('generatePdf').addEventListener('click', function() {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // Capture form data
        const firstName = document.getElementById('firstName').value;
        const lastName = document.getElementById('lastName').value;
        const email = document.getElementById('email').value;
        const phone = document.getElementById('phone').value;

        // Add Personal Details
        doc.text('Personal Details', 10, 10);
        doc.text(`Name: ${firstName} ${lastName}`, 10, 20);
        doc.text(`Email: ${email}`, 10, 30);
        doc.text(`Phone: ${phone}`, 10, 40);

        // More details can be captured and added similarly

        // Save PDF
        doc.save('resume.pdf');
    });
});
