var canvas = document.createElement("canvas");

function genCanvas(){
    // Initialise an empty canvas and place it on the page
    var intro = document.querySelector('#GoL');
    var context = canvas.getContext("2d");

    canvas.height = window.innerHeight ;

    canvas.width = window.innerWidth ;
    intro.appendChild(canvas);
    var x = 150, y = 100,
    side = 10;
    context.fillRect(x, y, side, side);
}

window.addEventListener("resize", () => {
    
    canvas.height = window.innerHeight ;
    
    canvas.width = window.innerWidth ;
    })