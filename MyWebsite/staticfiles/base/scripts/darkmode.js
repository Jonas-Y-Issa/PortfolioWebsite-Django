function darkmode() {
  document.body.classList.toggle("dark-mode");
  lightText = document.getElementById("lightwrapper");
  if (lightText.style != 'opacity: 0')
  {
    lightText.style = 'opacity: 0'
  }
}
