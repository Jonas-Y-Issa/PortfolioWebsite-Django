
var DynamicMJ = {
    
    formula: document.getElementById("formula"),
  
    update: function () {
      var a = document.getElementById("valueA").value;
      var b = document.getElementById("valueB").value;
      var c = document.getElementById("valueC").value;
      var tex = "\\frac{"+a+"}{2}+ \\frac{"+b+"}{2} = \\frac{"+c+"}{5}";
      this.formula.innerHTML = "\\["+tex+"\\]";
      MathJax.typeset();
    }
  };
  DynamicMJ.update();