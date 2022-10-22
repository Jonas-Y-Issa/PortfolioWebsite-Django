function genCanvas(){
    // Initialise an empty canvas and place it on the page
    var canvas = document.createElement("canvas");
    var intro = document.querySelector('#GoL');
    var context = canvas.getContext("2d");
    intro.appendChild(canvas);
}