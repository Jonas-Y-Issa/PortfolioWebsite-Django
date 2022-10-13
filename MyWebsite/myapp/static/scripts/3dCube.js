myMove();

var id = null;
function myMove() {
var elem = document.getElementById("rectw");
var pos = 0;
clearInterval(id);
id = setInterval(frame, 10);
function frame() {

    pos++;
    $("#rectw").css({'transform': `rotateX(${pos/2}deg)`});
    if(pos/2 === 360)
    {
        pos = 0;

    }
}
}