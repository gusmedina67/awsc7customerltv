// Function to get query string parameters
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// Read tenant and customer_guid from the query string
const tenant = getQueryParam('tenant');
const customer_guid = getQueryParam('customer_guid');

if (tenant && customer_guid) {
    // Create the API client
    var apigClient = apigClientFactory.newClient();
    // Define the path parameters for the API call
    var pathParams = {
        tenant: tenant,
        customer_guid: customer_guid
    };

    // Make the API call
    apigClient.postsGetTenantCustomerGuidGet(pathParams, null, {})
        .then(function (response) {
            // Parse the response to extract the lifetime value
            if (response.data && response.data.lifetimeValue !== undefined) {
                $("#response").text(`Life Time Value = ${response.data.lifetimeValue}`).addClass('success');
            } else {
                $("#response").text("No lifetime value found in the response.").addClass('error');
            }
        })
        .catch(function (error) {
            let errorMessage = "An error occurred while fetching the data.";

            // Check for specific error messages in the response
            if (error.response && error.response.data && error.response.data.message) {
                const message = error.response.data.message;

                if (message.includes("Customer does not exist")) {
                    errorMessage = "Error: The specified customer does not exist.";
                } else if (message.includes("Tenant does not exist")) {
                    errorMessage = "Error: The specified tenant does not exist.";
                } else {
                    errorMessage = `Error: ${message}`;
                }
            } else if (error.message) {
                errorMessage = `Error: ${error.message}`;
            } else {
                errorMessage = `Error: ${error}`;
            }

            // Display the error message
            $("#response").text(errorMessage).addClass('error');
        });

    // Construct the API URL with the query parameters
    //const apiUrl = `https://jjutau8hg7.execute-api.us-east-1.amazonaws.com/dev/posts/get/${tenant}/${customer_guid}`;

    // // Invoke the API when the page loads
    // $.ajax({
    //     url: apiUrl,
    //     method: "GET",
    //     success: function(response) {
    //         // Parse the response to extract the lifetime value
    //         if (response && response.lifetimeValue !== undefined) {
    //             $("#response").text(`Life Time Value = ${response.lifetimeValue}`).addClass('success');
    //         } else {
    //             $("#response").text("No lifetime value found in the response.").addClass('error');
    //         }
    //     },
    //     error: function(error) {
    //         let errorMessage = "An error occurred while fetching the data.";

    //         if (error.responseJSON && error.responseJSON.message) {
    //             const message = error.responseJSON.message;

    //             if (message.includes("Customer does not exist")) {
    //                 errorMessage = "Error: The specified customer does not exist.";
    //             } else if (message.includes("Tenant does not exist")) {
    //                 errorMessage = "Error: The specified tenant does not exist.";
    //             } else {
    //                 errorMessage = `Error: ${message}`;
    //             }
    //         } else {
    //             errorMessage = `Error: ${error.statusText}`;
    //         }

    //         $("#response").text(errorMessage).addClass('error');
    //     }
    // });
} else {
    $("#response").text("Error: Missing tenant or customer_guid in query string.").addClass('error');
}
