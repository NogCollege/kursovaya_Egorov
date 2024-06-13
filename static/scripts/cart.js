function toggleAddressField() {
    var deliveryOption = document.getElementById("delivery_option").value;
    var addressField = document.getElementById("address_field");
    if (deliveryOption === "Delivery") {
        addressField.style.display = "block";
    } else {
        addressField.style.display = "none";
    }
}