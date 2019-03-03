$(document).ready(function() {
      $( "#tabs" ).tabs();
      var img = new Image();
      img.onload = function() {
          var canvas = document.getElementById("can");
          var ctx = canvas.getContext("2d");
          var setcanvas = document.getElementById("set");
          var setctx = setcanvas.getContext("2d");

          ctx.drawImage(img, 0, 0);

          function drawcode(i) {
            var tiles = codetiles[i];
            if (tiles.length > 0) {
              var tile = tiles[0];
              setctx.drawImage(img,
                               8 * tile[0], 8 * tile[1],
                               8, 8,
                               8 * (i & 15), 8 * Math.floor(i / 16),
                               8, 8);
            }
          }
          function updateset(highlight) {
            for (var i = 0; i < 256; i++)
              drawcode(i);
            if (highlight != 256) {
              setctx.globalAlpha = 0.5;
              setctx.fillRect(0, 0, 128, 128);
              setctx.globalAlpha = 1.0;
              drawcode(highlight);
            }
          }
          function updatecan(highlight) {
            ctx.drawImage(img, 0, 0);
            ctx.globalAlpha = 0.5;
            ctx.fillRect(0, 0, img.width, img.height);
            ctx.globalAlpha = 1.0;
            var tiles = codetiles[highlight];
            $("#info").text("Character code " + highlight.toString() + " is used " + tiles.length.toString() + " times")
            for (var x = 0; x < tiles.length; x++) {
              ti = tiles[x];
              i = ti[0] * 8;
              j = ti[1] * 8;
              ctx.drawImage(img, i, j, 8, 8, i, j, 8, 8);
            }
          }

          function xys(x, y) {
            return x.toString() + "," + y.toString();
          }

          var i, j;

          updateset(256);
          ctx.drawImage(img, 0, 0);
          function outside() {
            ctx.drawImage(img, 0, 0);
            $("#info").text("Roll over image for character info");
            updateset(256);
          }
          $("#can").mouseleave(function(e) { outside() });
          $("#can").mousemove(function(e) {
            var offset = $("#can").offset();
            var x = e.pageX - offset.left;
            var y = e.pageY - offset.top;
            var code = tilecode[xys(Math.floor(x / 8), Math.floor(y / 8))];
            updatecan(code);
            updateset(code);
          });
          $("#set").mouseleave(function(e) { outside() });
          $("#set").mousemove(function(e) {
            var offset = $("#set").offset();
            var x = e.pageX - offset.left;
            var y = e.pageY - offset.top;
            var code = Math.floor(x / 8) + 16 * Math.floor(y / 8);
            updatecan(code);
            updateset(code);
          });
      }
      img.src = name + ".png";
});
