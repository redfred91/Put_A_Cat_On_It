document.addEventListener("DOMContentLoaded", function () {
    const generateButton = document.getElementById("generate-button");

    generateButton.addEventListener("click", function (event) {
        event.preventDefault();
        const description = document.getElementById("description").value;

        // Basic validation
        if (!description) {
            alert("Please enter a description.");
            return;
        }
        if (description.length > 100) {
            alert("Description is too long. Please keep it under 100 characters.");
            return;
        }

        // Show loading spinner and clear previous feedback
        document.getElementById("loading-spinner").style.display = "block";
        document.getElementById("feedback-message").innerHTML = "";

        // API URL (replace with your Flask server's endpoint)
        const generateApiURL = "https://your-flask-api.com/api/generate";

        // Make API call to Flask
        fetch(generateApiURL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                description: description
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to generate image");
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            // Hide the loading spinner and provide feedback
            document.getElementById("loading-spinner").style.display = "none";
            document.getElementById("feedback-message").innerHTML = `
                <a href="${data.product.product_url}" target="_blank" style="text-decoration: none; color: #007bff; font-weight: bold;">
                    Your Cat Sticker is Ready! Click Here!
                </a>
            `;
        })
        .catch(error => {
            console.error("Error:", error);
            document.getElementById("feedback-message").innerHTML = `
                <span style="color: red; font-weight: bold;">Error: ${error.message}</span>
            `;
            document.getElementById("loading-spinner").style.display = "none";
        });
    });
});
