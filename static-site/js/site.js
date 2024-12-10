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
        var tenant = getQueryParam('tenantid');
        var customer_guid = getQueryParam('customerid');

        if (!tenant || !customer_guid) {
            tenant = getQueryParam('tenantId');
            customer_guid = getQueryParam('customerId');
        }

        if (!tenant || !customer_guid) {
            $(".header-label")
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
                // Check if the response has data and a title
                if (response.data) {
                    // Set the header title based on the Lambda function response
                    const title = response.data.title || "Lifetime Value"; // Fallback to "Lifetime Value" if title is not provided
                    $(".header-label").text(title).removeClass('error');

                    // Parse and display the response for lifetime value
                    if (response.data.lifetimeValue !== undefined) {
                        const lifetimeValueInCents = response.data.lifetimeValue;

                        // Convert cents to dollars by dividing by 100
                        const lifetimeValueInDollars = lifetimeValueInCents / 100;

                        // Format the lifetime value as USD currency
                        const formattedValue = new Intl.NumberFormat('en-US', {
                            style: 'currency',
                            currency: 'USD'
                        }).format(lifetimeValueInDollars);

                        $(".status-div")
                            .text(formattedValue)
                            .removeClass('error');
                    } else {
                        $(".status-div")
                            .text("$0.00")
                            .removeClass('success');
                    }
                } else {
                    $(".header-label")
                        .text("Error: No response data.")
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

                $(".header-label")
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
