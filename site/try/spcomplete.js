
$(document).ready(function() {
      $( "#selectable" ).selectable();
      $( "#tabs" ).tabs();
      // $( "#tabs" ).tabs();
      var img = new Image();
      img.onload = function() {
          for (var i = 0; i < sprites.length; i++) {
            var spr = sprites[i];
            var x = spr[0];
            var y = spr[1];
            var canvas = document.getElementById("can" + x.toString() + "_" + y.toString());
            var ctx = canvas.getContext("2d");
            console.log(x, y);
            ctx.drawImage(img, x, y, 16, 16, 0, 0, 16, 16);
          }
      }
      img.src = "paletted.png";
});
