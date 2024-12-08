var App = window.App || {};

(function scopeWrapper($) {

    // Initialize variables
    var apiClient = apigClientFactory.newClient();

    App.loadLifetimeValue = function () {
        // Function to get query string parameters
        function getQueryParam(param) {
            const params = new URLSearchParams(window.location.search);
            return params.get(param);
        }

        // Read tenant and customer_guid from the query string
        var tenant = getQueryParam('tenant');
        var customer_guid = getQueryParam('customer_guid');

        if (!tenant || !customer_guid) {
            $("#response")
                .text("Error: Missing tenant or customer_guid in query string.")
                .addClass('error');
            return;
        }

        // Define the path parameters for the API call
        var pathParams = {
            tenant: tenant,
            customer_guid: customer_guid
        };

        // Make the API call
        apiClient.postsGetTenantCustomerGuidGet(pathParams, null, {})
            .then(function (response) {
                // Parse and display the response
                if (response.data && response.data.lifetimeValue !== undefined) {
                    $("#response")
                        .text(`Lifetime Value = ${response.data.lifetimeValue}`)
                        .removeClass('error')
                        .addClass('success');
                } else {
                    $("#response")
                        .text("No lifetime value found in the response.")
                        .removeClass('success')
                        .addClass('error');
                }
            })
            .catch(function (error) {
                // Handle errors and display messages
                let errorMessage = "An error occurred while fetching the data.";

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

                $("#response")
                    .text(errorMessage)
                    .removeClass('success')
                    .addClass('error');
            });
    };

    // Optional: Initialize functionality when the page loads
    $(document).ready(function () {
        App.loadLifetimeValue();
    });

}(jQuery));
