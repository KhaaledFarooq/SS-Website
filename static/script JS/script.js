//function for nav bar
function myFunction() {
    var x = document.getElementById("navId");
    if (x.className === "nav") {
        x.className += " responsive";
    } else {
        x.className = "nav";
    }
}

//funtion for the footer subscribe button
function display() {
    alert("You have subscribe us , Thank you!!!");
}