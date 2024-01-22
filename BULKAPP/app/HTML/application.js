function init() {
    var parrafos = document.querySelectorAll('p');
    var foundLorem = false;
  
    for (var i = 0; i < parrafos.length; i++) {
      var size1 = '728x90';
      var size2 = '970x250';
      var size3 = '320x100';
  
      // Verifica si el contenido del párrafo contiene el tamaño
      if (parrafos[i].innerText.includes(size1) || parrafos[i].innerText.includes(size2) || parrafos[i].innerText.includes(size3)) {
        foundLorem = true;
      }
  
      if (foundLorem && parrafos[i].innerText.trim().startsWith("Lorem")) {
        // Agrega la clase "parrafo" al elemento <p> que empieza por Lorem
        parrafos[i].classList.add("parrafo");
      }
    }
  
    var parrafosConClase = document.querySelectorAll('p.parrafo');
    for (var j = 0; j < parrafosConClase.length; j++) {
      // Agrega la clase "vertical-text" al elemento div con la clase "text"
      var divElement = parrafosConClase[j].closest('.main');
      if (divElement) {
        divElement.classList.add("vertical-text");
      }
    }
  
    var tags = document.getElementsByClassName('parrafo');
  }
init();
